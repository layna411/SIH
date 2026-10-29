from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.connection import get_db
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction, InstitutionAlias
from app.models.user import User
from app.models.enums import UserRoleEnum
from app.models.role import Role
from app.core.security import hash_password
from app.core.config import settings
from app.core.permissions import (
    get_current_user,
    get_current_active_user,
    get_current_user_optional,
    require_roles,
    check_institution_access
)
from app.schemas.institution import (
    InstitutionCreate,
    InstitutionUpdate,
    InstitutionResponse,
    InstitutionVerifyAICTE,
    InstitutionAliasCreate,
    InstitutionAliasResponse,
    InstitutionMembershipCreate,
    InstitutionMembershipResponse,
    JurisdictionCreate,
    JurisdictionResponse
)
from app.schemas.auth import UserResponse
from app.services.audit_service import log_audit

router = APIRouter(prefix="/institutions", tags=["Institutions"])

@router.get("", response_model=List[InstitutionResponse])
def list_institutions(
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination page limit"),
    state: Optional[str] = None,
    region: Optional[str] = None,
    aicte_permanent_id: Optional[str] = None,
    is_aicte_verified: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List verified active institutions suitable for student registration and AICTE oversight.
    Supports filtering by state, region, AICTE Permanent ID, verification status, and name/alias search.
    """
    query = db.query(Institution).filter(
        Institution.is_active == True,
        (Institution.verification_status == "VERIFIED") | (Institution.is_verified == True)
    )
    if state:
        query = query.filter(Institution.state.ilike(f"%{state.strip()}%"))
    if region:
        query = query.filter(Institution.region.ilike(f"%{region.strip()}%"))
    if aicte_permanent_id:
        query = query.filter(Institution.aicte_permanent_id == aicte_permanent_id.strip().upper())
    if is_aicte_verified is not None:
        query = query.filter(Institution.is_aicte_verified == is_aicte_verified)
    if search:
        search_term = search.strip()
        search_pattern = f"%{search_term}%"
        # Find institution IDs that match via aliases
        alias_matching_inst_ids = [
            row[0] for row in db.query(InstitutionAlias.institution_id).filter(
                InstitutionAlias.is_active == True,
                or_(
                    InstitutionAlias.alias_name.ilike(search_pattern),
                    InstitutionAlias.normalized_alias.ilike(f"%{search_term.lower()}%")
                )
            ).all()
        ]

        query = query.filter(
            or_(
                Institution.name.ilike(search_pattern),
                Institution.code.ilike(search_pattern),
                Institution.city.ilike(search_pattern),
                Institution.aicte_permanent_id.ilike(search_pattern),
                Institution.id.in_(alias_matching_inst_ids) if alias_matching_inst_ids else False
            )
        )
    return query.order_by(Institution.name.asc()).offset(skip).limit(limit).all()

@router.post("", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_institution(
    req: InstitutionCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Submit an institution registration request or create directly if super administrator.
    Public callers create an unverified PENDING institution request without any privileges.
    """
    code_clean = req.institution_code.upper().strip()
    existing = db.query(Institution).filter(Institution.code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Institution with code '{code_clean}' already exists."
        )

    # Validate AICTE Permanent ID if supplied
    clean_aicte_id = req.aicte_permanent_id.strip().upper() if req.aicte_permanent_id else None
    if clean_aicte_id:
        existing_aicte = db.query(Institution).filter(Institution.aicte_permanent_id == clean_aicte_id).first()
        if existing_aicte:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Institution with AICTE Permanent ID '{clean_aicte_id}' already exists."
            )

    is_super_admin = current_user is not None and current_user.default_role == UserRoleEnum.SUPER_ADMIN
    verification_status = "VERIFIED" if is_super_admin else "PENDING"
    is_verified = is_super_admin
    is_aicte_verified = bool(is_super_admin and req.is_aicte_verified and clean_aicte_id)

    new_inst = Institution(
        code=code_clean,
        name=req.name.strip(),
        institution_type=req.institution_type or "COLLEGE",
        state=req.state.strip(),
        district=req.district.strip() if req.district else None,
        city=req.city.strip() if req.city else (req.district.strip() if req.district else ""),
        address=req.address,
        contact_email=req.official_email.lower().strip(),
        contact_phone=req.contact_phone,
        website=req.website,
        aicte_permanent_id=clean_aicte_id,
        region=req.region.strip() if req.region else None,
        is_active=True,
        is_verified=is_verified,
        is_aicte_verified=is_aicte_verified,
        verification_status=verification_status
    )
    db.add(new_inst)
    db.commit()
    db.refresh(new_inst)

    actor_id = current_user.id if current_user else None
    log_audit(
        db,
        action="CREATE_INSTITUTION" if is_super_admin else "REQUEST_INSTITUTION",
        entity_type="INSTITUTION",
        user_id=actor_id,
        entity_id=str(new_inst.id),
        details={"code": new_inst.code, "aicte_permanent_id": clean_aicte_id, "is_aicte_verified": is_aicte_verified}
    )

    # Automatically create or link the Institution Head account with default password
    default_pwd = settings.DEFAULT_INSTITUTION_PASSWORD
    account_created = False
    head_user = db.query(User).filter(User.email == new_inst.contact_email).first()

    if not head_user:
        head_user = User(
            email=new_inst.contact_email,
            full_name=f"{new_inst.name} Administration",
            hashed_password=hash_password(default_pwd),
            default_role=UserRoleEnum.INSTITUTION_HEAD,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db.add(head_user)
        db.commit()
        db.refresh(head_user)
        account_created = True

        log_audit(
            db,
            action="CREATE_INSTITUTION_HEAD_ACCOUNT",
            entity_type="USER",
            user_id=actor_id,
            entity_id=str(head_user.id),
            details={"email": head_user.email, "institution_id": new_inst.id, "initial_password_set": True}
        )
    elif head_user.default_role == UserRoleEnum.STUDENT and is_super_admin:
        # Elevate to head if appropriate
        head_user.default_role = UserRoleEnum.INSTITUTION_HEAD
        db.commit()

    # Link user to new institution via InstitutionMembership
    head_role = db.query(Role).filter(Role.name == UserRoleEnum.INSTITUTION_HEAD).first()
    existing_membership = db.query(InstitutionMembership).filter(
        InstitutionMembership.user_id == head_user.id,
        InstitutionMembership.institution_id == new_inst.id
    ).first()

    if not existing_membership:
        membership = InstitutionMembership(
            user_id=head_user.id,
            institution_id=new_inst.id,
            role_id=head_role.id if head_role else None,
            role=UserRoleEnum.INSTITUTION_HEAD,
            designation="Institution Head",
            department="Administration",
            is_active=True
        )
        db.add(membership)
        db.commit()

    # Populate transient attributes for response
    new_inst.admin_account_email = head_user.email
    new_inst.default_password = default_pwd if account_created else None
    new_inst.account_created = account_created

    return new_inst

@router.get("/{id}", response_model=InstitutionResponse)
def get_institution(id: int, db: Session = Depends(get_db)):
    """View institution details by ID."""
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")
    return inst

@router.put("/{id}", response_model=InstitutionResponse)
def update_institution(
    id: int,
    req: InstitutionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update institution details (Super Admin or authorized Institution Head)."""
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")

    if not check_institution_access(current_user, id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this institution.")

    is_super_admin = current_user.default_role == UserRoleEnum.SUPER_ADMIN

    for field, value in req.model_dump(exclude_unset=True).items():
        # Only super admin can change platform verification status or official AICTE identity
        if field in ("verification_status", "is_aicte_verified", "aicte_permanent_id") and not is_super_admin:
            continue

        if field == "aicte_permanent_id" and value:
            clean_aicte = str(value).strip().upper()
            collision = db.query(Institution).filter(
                Institution.aicte_permanent_id == clean_aicte,
                Institution.id != id
            ).first()
            if collision:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AICTE Permanent ID '{clean_aicte}' is already assigned to institution ID {collision.id} ({collision.name})."
                )
            value = clean_aicte

        setattr(inst, field, value)

    db.commit()
    db.refresh(inst)
    log_audit(db, action="UPDATE_INSTITUTION", entity_type="INSTITUTION", user_id=current_user.id, entity_id=str(inst.id))
    return inst

@router.post("/{id}/verify-aicte", response_model=InstitutionResponse)
def verify_aicte_institution(
    id: int,
    req: InstitutionVerifyAICTE,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Formally verify or update an institution's official AICTE Permanent ID and regional jurisdiction.
    Restricted strictly to Super Administrators.
    """
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")

    clean_aicte = req.aicte_permanent_id.strip().upper() if req.aicte_permanent_id else None
    if clean_aicte:
        collision = db.query(Institution).filter(
            Institution.aicte_permanent_id == clean_aicte,
            Institution.id != id
        ).first()
        if collision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AICTE Permanent ID '{clean_aicte}' is already assigned to institution ID {collision.id} ({collision.name})."
            )
        inst.aicte_permanent_id = clean_aicte

    if req.region is not None:
        inst.region = req.region.strip() if req.region else None

    inst.is_aicte_verified = req.is_aicte_verified
    if req.is_aicte_verified:
        inst.is_verified = True
        inst.verification_status = "VERIFIED"

    db.commit()
    db.refresh(inst)

    log_audit(
        db,
        action="VERIFY_AICTE_INSTITUTION",
        entity_type="INSTITUTION",
        user_id=current_user.id,
        entity_id=str(inst.id),
        details={"aicte_permanent_id": inst.aicte_permanent_id, "region": inst.region, "is_aicte_verified": inst.is_aicte_verified}
    )
    return inst

# Alias Management Endpoints
@router.get("/{id}/aliases", response_model=List[InstitutionAliasResponse])
def list_institution_aliases(
    id: int,
    db: Session = Depends(get_db)
):
    """Retrieve all recorded aliases for a given institution."""
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")
    return db.query(InstitutionAlias).filter(
        InstitutionAlias.institution_id == id,
        InstitutionAlias.is_active == True
    ).order_by(InstitutionAlias.alias_name.asc()).all()

@router.post("/{id}/aliases", response_model=InstitutionAliasResponse, status_code=status.HTTP_201_CREATED)
def add_institution_alias(
    id: int,
    req: InstitutionAliasCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Register a verified or alternative alias for an institution.
    Authorized for Super Admins and authorized Institution Heads.
    """
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")

    if not check_institution_access(current_user, id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to manage aliases for this institution.")

    alias_clean = req.alias_name.strip()
    norm_alias = " ".join(alias_clean.lower().split())

    # Check duplicate for this institution
    existing = db.query(InstitutionAlias).filter(
        InstitutionAlias.institution_id == id,
        InstitutionAlias.normalized_alias == norm_alias
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.alias_name = alias_clean
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alias '{alias_clean}' is already registered for this institution."
        )

    # Protect against ambiguous alias registered for another institution
    other_match = db.query(InstitutionAlias).filter(
        InstitutionAlias.institution_id != id,
        InstitutionAlias.normalized_alias == norm_alias,
        InstitutionAlias.is_active == True
    ).first()
    if other_match:
        other_inst = db.query(Institution).filter(Institution.id == other_match.institution_id).first()
        other_name = other_inst.name if other_inst else f"ID {other_match.institution_id}"
        # Permit with warning or tag source, but if exact duplicate acronym, log provenance
        log_audit(
            db,
            action="AMBIGUOUS_ALIAS_WARNING",
            entity_type="ALIAS",
            user_id=current_user.id,
            entity_id=str(id),
            details=f"Alias '{alias_clean}' also registered for {other_name}"
        )

    new_alias = InstitutionAlias(
        institution_id=id,
        alias_name=alias_clean,
        normalized_alias=norm_alias,
        source=req.source or "MANUAL",
        is_verified=bool(req.is_verified),
        is_active=True,
        created_by_user_id=current_user.id
    )
    db.add(new_alias)
    db.commit()
    db.refresh(new_alias)

    log_audit(
        db,
        action="ADD_INSTITUTION_ALIAS",
        entity_type="INSTITUTION_ALIAS",
        user_id=current_user.id,
        entity_id=str(new_alias.id),
        details={"institution_id": id, "alias_name": alias_clean, "normalized_alias": norm_alias}
    )
    return new_alias

@router.delete("/{id}/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_institution_alias(
    id: int,
    alias_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate or remove an institution alias (Super Admin or authorized Institution Head)."""
    alias = db.query(InstitutionAlias).filter(
        InstitutionAlias.id == alias_id,
        InstitutionAlias.institution_id == id
    ).first()
    if not alias:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alias not found.")

    if not check_institution_access(current_user, id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.delete(alias)
    db.commit()

    log_audit(
        db,
        action="REMOVE_INSTITUTION_ALIAS",
        entity_type="INSTITUTION_ALIAS",
        user_id=current_user.id,
        entity_id=str(alias_id),
        details={"institution_id": id, "alias_name": alias.alias_name}
    )
    return None

@router.post("/{id}/members", response_model=InstitutionMembershipResponse, status_code=status.HTTP_201_CREATED)
def add_institution_member(
    id: int,
    req: InstitutionMembershipCreate,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """Assign an officer or staff member to the institution."""
    if not check_institution_access(current_user, id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to manage this institution's staff.")

    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    role_record = db.query(Role).filter(Role.name == req.role.value).first()
    role_id = role_record.id if role_record else None

    existing_membership = db.query(InstitutionMembership).filter(
        InstitutionMembership.institution_id == id,
        InstitutionMembership.user_id == req.user_id
    ).first()

    if existing_membership:
        existing_membership.role = req.role
        existing_membership.role_id = role_id
        existing_membership.department = req.department
        existing_membership.designation = req.designation
        existing_membership.is_active = True
        db.commit()
        db.refresh(existing_membership)
        membership = existing_membership
    else:
        membership = InstitutionMembership(
            user_id=req.user_id,
            institution_id=id,
            role_id=role_id,
            role=req.role,
            department=req.department,
            designation=req.designation,
            is_active=True
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)

    log_audit(db, action="ASSIGN_INSTITUTION_MEMBER", entity_type="MEMBERSHIP", user_id=current_user.id, entity_id=str(membership.id))
    return membership

@router.get("/{id}/members", response_model=List[InstitutionMembershipResponse])
def get_institution_members(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get members belonging to this institution."""
    if not check_institution_access(current_user, id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return db.query(InstitutionMembership).filter(
        InstitutionMembership.institution_id == id,
        InstitutionMembership.is_active == True
    ).all()

# Jurisdiction endpoints for Regulatory Admins
@router.post("/jurisdictions", response_model=JurisdictionResponse, status_code=status.HTTP_201_CREATED)
def add_regulatory_jurisdiction(
    req: JurisdictionCreate,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Assign jurisdiction to a Regulatory Administrator."""
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    jurisdiction = RegulatoryJurisdiction(
        user_id=req.user_id,
        state=req.state.strip(),
        jurisdiction_code=req.jurisdiction_code.strip(),
        notes=req.notes
    )
    db.add(jurisdiction)
    db.commit()
    db.refresh(jurisdiction)

    log_audit(db, action="ASSIGN_REGULATORY_JURISDICTION", entity_type="JURISDICTION", user_id=current_user.id, entity_id=str(jurisdiction.id))
    return jurisdiction

@router.get("/jurisdictions/my", response_model=List[JurisdictionResponse])
def get_my_jurisdictions(
    current_user: User = Depends(require_roles(UserRoleEnum.REGULATORY_ADMIN, UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Retrieve jurisdictions assigned to the current user."""
    return db.query(RegulatoryJurisdiction).filter(RegulatoryJurisdiction.user_id == current_user.id).all()
