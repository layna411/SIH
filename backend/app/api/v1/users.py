import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.connection import get_db
from app.core.config import settings
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.invitation import UserInvitation
from app.models.enums import UserRoleEnum
from app.core.permissions import (
    get_current_user, 
    get_current_active_user,
    require_roles, 
    get_user_institution_ids,
    check_institution_access
)
from app.schemas.auth import UserResponse
from app.schemas.invitation import UserInviteRequest, UserInviteResponse
from app.api.v1.auth import build_user_response
from app.services.audit_service import log_audit

router = APIRouter(prefix="/users", tags=["Users"])

class RoleUpdateRequest(BaseModel):
    role: UserRoleEnum

class StatusUpdateRequest(BaseModel):
    is_active: bool


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user profile."""
    return build_user_response(current_user, db)


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRoleEnum] = None,
    institution_id: Optional[int] = None,
    account_status: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """
    List and search platform users with multi-tenant scoping.
    Super Admins can view platform-wide users.
    Institution Heads can only view users affiliated with their authorized institution.
    """
    query = db.query(User)

    # Multi-tenant scoping for Institution Heads
    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        head_inst_ids = get_user_institution_ids(current_user, db)
        if institution_id is not None and institution_id not in head_inst_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to users of this institution."
            )
        # Filter users who belong to the institution head's authorized institutions
        query = query.join(User.memberships).filter(
            InstitutionMembership.institution_id.in_(head_inst_ids),
            InstitutionMembership.is_active == True
        )
    elif institution_id:
        # Super Admin filtering by specific institution
        query = query.join(User.memberships).filter(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.is_active == True
        )

    # Filter by Role
    if role:
        query = query.filter(User.default_role == role)

    # Filter by Account Status (ACTIVE, INACTIVE)
    if account_status:
        clean_status = account_status.strip().upper()
        if clean_status == "ACTIVE":
            query = query.filter(User.is_active == True)
        elif clean_status == "INACTIVE":
            query = query.filter(User.is_active == False)

    # Keyword Search
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.student_id_number.ilike(search_pattern)
            )
        )

    users = query.distinct().order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return [build_user_response(u, db) for u in users]


@router.get("/{id}", response_model=UserResponse)
def get_user_detail(
    id: int,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """View user details with multi-tenant verification."""
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        head_inst_ids = get_user_institution_ids(current_user, db)
        target_inst_ids = [m.institution_id for m in target_user.memberships if m.is_active]
        if not any(inst_id in head_inst_ids for inst_id in target_inst_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to view this user's profile."
            )

    return build_user_response(target_user, db)


@router.post("/invite", response_model=UserInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_user(
    req: UserInviteRequest,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """
    Invite a privileged user (College Officer, Institution Head, or Regulatory Admin).
    Enforces strict role hierarchies and multi-tenant isolation.
    """
    clean_email = req.email.strip().lower()

    # 1. Role Authorization Enforcement
    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        # Institution Heads can only invite College Officers for their own institution
        if req.role != UserRoleEnum.COLLEGE_OFFICER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Institution Heads can only invite College Officers."
            )
        head_inst_ids = get_user_institution_ids(current_user, db)
        if not req.institution_id or req.institution_id not in head_inst_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Institution Heads can only invite officers for their own institution."
            )

    # Super Admin validation
    if current_user.default_role == UserRoleEnum.SUPER_ADMIN:
        if req.role in (UserRoleEnum.COLLEGE_OFFICER, UserRoleEnum.INSTITUTION_HEAD):
            if not req.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An institution must be selected when inviting a {req.role.value.replace('_', ' ')}."
                )
        elif req.role == UserRoleEnum.REGULATORY_ADMIN:
            if not req.jurisdiction_state:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A state jurisdiction must be specified when inviting a Regulatory Admin."
                )

    # 2. Validate Institution if provided
    inst = None
    if req.institution_id:
        inst = db.query(Institution).filter(Institution.id == req.institution_id, Institution.is_active == True).first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected institution does not exist or is inactive."
            )

    # 3. Check for Duplicate Active Memberships
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user and req.institution_id:
        active_mem = db.query(InstitutionMembership).filter(
            InstitutionMembership.user_id == existing_user.id,
            InstitutionMembership.institution_id == req.institution_id,
            InstitutionMembership.role == req.role,
            InstitutionMembership.is_active == True
        ).first()
        if active_mem:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A user with email '{clean_email}' already has an active {req.role.value} membership in this institution."
            )

    # 4. Check for Existing Pending Invitations
    now = datetime.now(timezone.utc)
    existing_invite = db.query(UserInvitation).filter(
        UserInvitation.email == clean_email,
        UserInvitation.role == req.role,
        UserInvitation.institution_id == req.institution_id,
        UserInvitation.status == "PENDING"
    ).first()

    if existing_invite:
        exp = existing_invite.expires_at if existing_invite.expires_at.tzinfo else existing_invite.expires_at.replace(tzinfo=timezone.utc)
        if exp > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An active pending invitation has already been issued to '{clean_email}'. Please resend or revoke the existing invite."
            )
        else:
            existing_invite.status = "EXPIRED"
            db.commit()

    # 5. Generate Cryptographic Single-Use Invitation Token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = now + timedelta(days=7)

    invitation = UserInvitation(
        email=clean_email,
        full_name=req.full_name.strip(),
        role=req.role,
        institution_id=req.institution_id,
        department=req.department.strip() if req.department else None,
        designation=req.designation.strip() if req.designation else None,
        staff_id_number=req.staff_id_number.strip() if req.staff_id_number else None,
        jurisdiction_state=req.jurisdiction_state.strip() if req.jurisdiction_state else None,
        jurisdiction_code=req.jurisdiction_code.strip() if req.jurisdiction_code else None,
        jurisdiction_notes=req.jurisdiction_notes.strip() if req.jurisdiction_notes else None,
        token_hash=token_hash,
        invited_by_user_id=current_user.id,
        status="PENDING",
        expires_at=expires_at
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    log_audit(
        db,
        action="INVITE_USER",
        entity_type="USER_INVITATION",
        user_id=current_user.id,
        entity_id=str(invitation.id),
        details=f"Invited {clean_email} as {req.role.value}"
    )

    # 6. Delivery Status & Development Link Handling
    # If SMTP is configured, delivery would be attempted. In dev mode without SMTP, deliver clear link.
    delivery_status = "DEVELOPMENT_LINK_GENERATED"
    invitation_link = f"http://localhost:5173/accept-invitation?token={raw_token}"
    notes = "Development Mode: SMTP email delivery is unconfigured. Share the invitation link directly with the user."

    return UserInviteResponse(
        id=invitation.id,
        email=invitation.email,
        full_name=invitation.full_name,
        role=invitation.role,
        institution_id=invitation.institution_id,
        institution_name=inst.name if inst else None,
        department=invitation.department,
        designation=invitation.designation,
        staff_id_number=invitation.staff_id_number,
        jurisdiction_state=invitation.jurisdiction_state,
        jurisdiction_code=invitation.jurisdiction_code,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        delivery_status=delivery_status,
        invitation_link=invitation_link,
        notes=notes
    )


@router.get("/invitations/list", response_model=List[UserInviteResponse])
def list_invitations(
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """List pending and historical account invitations."""
    query = db.query(UserInvitation)

    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        head_inst_ids = get_user_institution_ids(current_user, db)
        query = query.filter(UserInvitation.institution_id.in_(head_inst_ids))

    invitations = query.order_by(UserInvitation.created_at.desc()).limit(100).all()

    results = []
    for inv in invitations:
        inst_name = inv.institution.name if inv.institution else None
        results.append(UserInviteResponse(
            id=inv.id,
            email=inv.email,
            full_name=inv.full_name,
            role=inv.role,
            institution_id=inv.institution_id,
            institution_name=inst_name,
            department=inv.department,
            designation=inv.designation,
            staff_id_number=inv.staff_id_number,
            jurisdiction_state=inv.jurisdiction_state,
            jurisdiction_code=inv.jurisdiction_code,
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            delivery_status="STORED_PENDING" if inv.status == "PENDING" else inv.status,
            invitation_link=None,
            notes=None
        ))
    return results


@router.delete("/invitations/{id}", response_model=dict)
def revoke_invitation(
    id: int,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """Revoke a pending user invitation."""
    invite = db.query(UserInvitation).filter(UserInvitation.id == id).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        head_inst_ids = get_user_institution_ids(current_user, db)
        if invite.institution_id not in head_inst_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to revoke this invitation.")

    invite.status = "REVOKED"
    db.commit()

    log_audit(
        db,
        action="REVOKE_INVITATION",
        entity_type="USER_INVITATION",
        user_id=current_user.id,
        entity_id=str(invite.id),
        details=f"Revoked invitation for {invite.email}"
    )
    return {"message": "Invitation revoked successfully.", "id": id}


@router.post("/invitations/{id}/resend", response_model=UserInviteResponse)
def resend_invitation(
    id: int,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """Regenerate a single-use token and renew invitation expiration."""
    invite = db.query(UserInvitation).filter(UserInvitation.id == id).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        head_inst_ids = get_user_institution_ids(current_user, db)
        if invite.institution_id not in head_inst_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to resend this invitation.")

    if invite.status == "ACCEPTED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has already been accepted.")

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    invite.token_hash = token_hash
    invite.expires_at = now + timedelta(days=7)
    invite.status = "PENDING"
    db.commit()
    db.refresh(invite)

    log_audit(
        db,
        action="RESEND_INVITATION",
        entity_type="USER_INVITATION",
        user_id=current_user.id,
        entity_id=str(invite.id),
        details=f"Renewed invitation for {invite.email}"
    )

    inst_name = invite.institution.name if invite.institution else None
    return UserInviteResponse(
        id=invite.id,
        email=invite.email,
        full_name=invite.full_name,
        role=invite.role,
        institution_id=invite.institution_id,
        institution_name=inst_name,
        department=invite.department,
        designation=invite.designation,
        staff_id_number=invite.staff_id_number,
        jurisdiction_state=invite.jurisdiction_state,
        jurisdiction_code=invite.jurisdiction_code,
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        delivery_status="DEVELOPMENT_LINK_GENERATED",
        invitation_link=f"http://localhost:5173/accept-invitation?token={raw_token}",
        notes="Development Mode: Share the new invitation link directly with the user."
    )


@router.put("/{id}/role", response_model=UserResponse)
def update_user_role(
    id: int,
    req: RoleUpdateRequest,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Update user role (Super Admin only). Never permits self-elevation without verification."""
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.default_role = req.role
    db.commit()
    db.refresh(target_user)

    log_audit(db, action="UPDATE_USER_ROLE", entity_type="USER", user_id=current_user.id, entity_id=str(target_user.id), details=f"Assigned role: {req.role.value}")

    return build_user_response(target_user, db)


@router.put("/{id}/status", response_model=UserResponse)
def update_user_status(
    id: int,
    req: StatusUpdateRequest,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate user account.
    Super Admins can toggle status across users.
    Institution Heads can toggle status only for officers within their authorized institution.
    """
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Prevent deactivating own account
    if target_user.id == current_user.id and not req.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own administrative account.")

    if current_user.default_role == UserRoleEnum.INSTITUTION_HEAD:
        # Cannot modify Super Admins or other Institution Heads
        if target_user.default_role in (UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot alter administrative accounts.")
        
        # Must belong to current head's institution
        head_inst_ids = get_user_institution_ids(current_user, db)
        user_inst_ids = [m.institution_id for m in target_user.memberships if m.is_active]
        if not any(inst_id in head_inst_ids for inst_id in user_inst_ids):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to manage users outside your institution.")

        # Also toggle active status on the institution membership
        for m in target_user.memberships:
            if m.institution_id in head_inst_ids:
                m.is_active = req.is_active

    target_user.is_active = req.is_active
    db.commit()
    db.refresh(target_user)

    log_audit(db, action="TOGGLE_USER_STATUS", entity_type="USER", user_id=current_user.id, entity_id=str(target_user.id), details=f"Active: {req.is_active}")

    return build_user_response(target_user, db)
