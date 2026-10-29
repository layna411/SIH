from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.config import settings
from app.models.user import User
from app.models.role import Role
from app.models.institution import Institution, InstitutionMembership
from app.models.enums import UserRoleEnum
from app.core.security import hash_password, verify_password, create_access_token
from app.core.permissions import get_current_active_user, get_current_user, get_current_user_optional
from app.schemas.auth import (
    UserRegisterRequest, 
    UserLoginRequest, 
    TokenResponse, 
    UserResponse, 
    UserProfileUpdate,
    UserPasswordChangeRequest,
    EmailVerifyRequest,
    EmailResendVerificationRequest,
    InstitutionMembershipSummary,
    JurisdictionSummary
)
from app.schemas.role import RoleResponse
from app.schemas.invitation import AcceptInvitationRequest, InvitationValidateResponse
from app.models.invitation import UserInvitation
from app.models.institution import RegulatoryJurisdiction
from app.services.audit_service import log_audit
from app.services.email_service import email_service
from app.services.notification_service import create_notification
import hashlib
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    """List system roles definitions."""
    return db.query(Role).order_by(Role.id.asc()).all()


def build_user_response(user: User, db: Session) -> UserResponse:
    memberships = []
    for m in user.memberships:
        if m.is_active and m.institution:
            memberships.append(InstitutionMembershipSummary(
                id=m.id,
                institution_id=m.institution_id,
                institution_name=m.institution.name,
                institution_code=m.institution.code,
                role_id=m.role_id,
                role=m.role,
                department=m.department,
                designation=m.designation,
                is_active=m.is_active
            ))
    
    jurisdictions = []
    for j in user.regulatory_jurisdictions:
        if j.is_active:
            jurisdictions.append(JurisdictionSummary(
                id=j.id,
                user_id=j.user_id,
                jurisdiction_type=j.jurisdiction_type,
                state=j.state,
                region=j.region,
                institution_id=j.institution_id,
                jurisdiction_code=j.jurisdiction_code,
                notes=j.notes,
                is_active=j.is_active
            ))

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_email_verified=user.is_email_verified,
        default_role=user.default_role,
        student_id_number=user.student_id_number,
        created_at=user.created_at,
        updated_at=user.updated_at,
        memberships=memberships,
        regulatory_jurisdictions=jurisdictions
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new student account.
    Public registration strictly creates student accounts only.
    Caller cannot select privileged roles (SUPER_ADMIN, REGULATORY_ADMIN, etc.).
    """
    clean_email = req.email.lower().strip()
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Strictly assign STUDENT role for all public self-registrations
    role_to_assign = UserRoleEnum.STUDENT
    student_role = db.query(Role).filter(Role.name == "STUDENT").first()
    student_role_id = student_role.id if student_role else None

    new_user = User(
        email=clean_email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        phone_number=req.phone_number,
        student_id_number=req.student_id_number,
        default_role=role_to_assign,
        is_active=True,
        is_verified=True,
        is_email_verified=False  # Accurate: email verification delivery is not configured
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If an institution was selected, create student membership
    if req.institution_id:
        inst = db.query(Institution).filter(Institution.id == req.institution_id).first()
        if inst and inst.is_active:
            existing_membership = db.query(InstitutionMembership).filter(
                InstitutionMembership.user_id == new_user.id,
                InstitutionMembership.institution_id == inst.id
            ).first()
            if not existing_membership:
                membership = InstitutionMembership(
                    user_id=new_user.id,
                    institution_id=inst.id,
                    role_id=student_role_id,
                    role=role_to_assign,
                    department="Student Body",
                    is_active=True
                )
                db.add(membership)
                db.commit()
                db.refresh(new_user)

    log_audit(db, action="USER_REGISTER", entity_type="USER", user_id=new_user.id, entity_id=str(new_user.id))

    # Dispatch email verification token
    raw_token, _ = email_service.generate_verification_token(db, new_user)
    email_service.send_verification_email(new_user, raw_token, db)

    # In-app welcome and verification guidance notification
    create_notification(
        db=db,
        user_id=new_user.id,
        title="Welcome to EduResolve AI",
        message="Your account has been registered. Please verify your email address to access full grievance features.",
        link="/profile",
        notification_type="INFO",
        email_notify=False
    )

    return build_user_response(new_user, db)

@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password.
    Returns JWT access token with role information and token expiry.
    """
    invalid_creds_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    clean_email = req.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise invalid_creds_exception
        
    if not verify_password(req.password, user.hashed_password):
        raise invalid_creds_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support."
        )

    # Create JWT
    token_payload = {
        "email": user.email,
        "role": user.default_role.value,
        "name": user.full_name
    }
    access_token = create_access_token(subject=user.id, extra_claims=token_payload)
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    log_audit(db, action="USER_LOGIN", entity_type="USER", user_id=user.id, entity_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=build_user_response(user, db)
    )

@router.post("/token", response_model=TokenResponse)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password form compatible login endpoint for Swagger UI."""
    req = UserLoginRequest(email=form_data.username, password=form_data.password)
    return login(req, db)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Return authenticated current user profile with safe authorized roles and memberships."""
    return build_user_response(current_user, db)

@router.put("/me", response_model=UserResponse)
def update_profile(
    req: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update personal profile information.
    Users cannot modify their email, role, or permissions through this endpoint.
    """
    if req.full_name is not None:
        current_user.full_name = req.full_name.strip()
    if req.phone_number is not None:
        current_user.phone_number = req.phone_number.strip()
    if req.student_id_number is not None:
        current_user.student_id_number = req.student_id_number.strip()

    db.commit()
    db.refresh(current_user)
    log_audit(db, action="USER_PROFILE_UPDATE", entity_type="USER", user_id=current_user.id, entity_id=str(current_user.id))
    return build_user_response(current_user, db)


@router.get("/invitations/{token}", response_model=InvitationValidateResponse)
def validate_invitation(token: str, db: Session = Depends(get_db)):
    """Validate invitation token and retrieve onboarding metadata."""
    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    invite = db.query(UserInvitation).filter(UserInvitation.token_hash == token_hash).first()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation link is invalid or does not exist."
        )
        
    if invite.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This invitation has already been {invite.status.lower()}."
        )
        
    now = datetime.now(timezone.utc)
    exp = invite.expires_at if invite.expires_at.tzinfo else invite.expires_at.replace(tzinfo=timezone.utc)
    if exp < now:
        invite.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation link has expired. Please ask your administrator to resend the invite."
        )
        
    inst_name = invite.institution.name if invite.institution else None
    return InvitationValidateResponse(
        is_valid=True,
        email=invite.email,
        full_name=invite.full_name,
        role=invite.role,
        institution_id=invite.institution_id,
        institution_name=inst_name,
        department=invite.department,
        designation=invite.designation,
        expires_at=invite.expires_at
    )


@router.post("/invitations/{token}/accept", response_model=TokenResponse)
def accept_invitation(token: str, req: AcceptInvitationRequest, db: Session = Depends(get_db)):
    """
    Accept single-use invitation, set secure password, and activate account with assigned permissions.
    """
    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    invite = db.query(UserInvitation).filter(UserInvitation.token_hash == token_hash).first()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation link is invalid or does not exist."
        )
        
    if invite.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This invitation has already been {invite.status.lower()}."
        )
        
    now = datetime.now(timezone.utc)
    exp = invite.expires_at if invite.expires_at.tzinfo else invite.expires_at.replace(tzinfo=timezone.utc)
    if exp < now:
        invite.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation link has expired. Please ask an administrator to resend the invite."
        )
        
    # Check if a user with this email already exists
    user = db.query(User).filter(User.email == invite.email).first()
    if not user:
        user = User(
            email=invite.email,
            hashed_password=hash_password(req.password),
            full_name=invite.full_name,
            phone_number=req.phone_number,
            student_id_number=invite.staff_id_number,
            default_role=invite.role,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Existing user updating password and default role
        user.hashed_password = hash_password(req.password)
        user.default_role = invite.role
        user.is_active = True
        user.is_verified = True
        user.is_email_verified = True
        if req.phone_number:
            user.phone_number = req.phone_number
        db.commit()
        db.refresh(user)
        
    # Associate Institutional Membership if relevant
    if invite.institution_id:
        existing_mem = db.query(InstitutionMembership).filter(
            InstitutionMembership.user_id == user.id,
            InstitutionMembership.institution_id == invite.institution_id
        ).first()
        
        role_record = db.query(Role).filter(Role.name == invite.role.value).first()
        role_id = role_record.id if role_record else None
        
        if existing_mem:
            existing_mem.role = invite.role
            existing_mem.role_id = role_id
            existing_mem.department = invite.department
            existing_mem.designation = invite.designation
            existing_mem.is_active = True
        else:
            new_mem = InstitutionMembership(
                user_id=user.id,
                institution_id=invite.institution_id,
                role_id=role_id,
                role=invite.role,
                department=invite.department,
                designation=invite.designation,
                is_active=True
            )
            db.add(new_mem)
        db.commit()
        
    # Associate Regulatory Jurisdiction if relevant
    if invite.role == UserRoleEnum.REGULATORY_ADMIN and invite.jurisdiction_state:
        existing_jur = db.query(RegulatoryJurisdiction).filter(
            RegulatoryJurisdiction.user_id == user.id,
            RegulatoryJurisdiction.state == invite.jurisdiction_state
        ).first()
        if not existing_jur:
            new_jur = RegulatoryJurisdiction(
                user_id=user.id,
                jurisdiction_type="STATE",
                state=invite.jurisdiction_state,
                jurisdiction_code=invite.jurisdiction_code or f"JUR-{invite.jurisdiction_state.upper()[:3]}",
                notes=invite.jurisdiction_notes or "Onboarded via Regulatory Administrator invitation",
                is_active=True
            )
            db.add(new_jur)
            db.commit()

    # Mark invitation as accepted
    invite.status = "ACCEPTED"
    invite.accepted_at = now
    db.commit()
    
    log_audit(
        db,
        action="ACCEPT_INVITATION",
        entity_type="USER_INVITATION",
        user_id=user.id,
        entity_id=str(invite.id),
        details=f"User {user.email} activated account with role {invite.role.value}"
    )
    
    # Generate login token for immediate session
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.default_role.value}
    )
    user_resp = build_user_response(user, db)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_resp
    )

@router.post("/change-password")
def change_password(
    req: UserPasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Allow authenticated user to change their password securely.
    Verifies the current password before applying the new Argon2 hashed password.
    """
    if req.confirm_password and req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match."
        )

    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    if req.current_password == req.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as your current password."
        )

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()

    log_audit(
        db,
        action="CHANGE_PASSWORD",
        entity_type="USER",
        user_id=current_user.id,
        entity_id=str(current_user.id),
        details={"status": "SUCCESS", "email": current_user.email}
    )

    return {"message": "Password changed successfully."}

@router.post("/verify-email")
def verify_email(
    req: EmailVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Validate cryptographically secure email verification token.
    Updates account verification status upon successful validation.
    """
    success, message, user = email_service.verify_email_token(db, req.token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return {"status": "success", "message": message, "email": user.email if user else None}

@router.post("/resend-verification")
def resend_verification(
    req: EmailResendVerificationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Resend verification email with rate limiting and cooldown enforcement.
    Maintains uniform public response to prevent account enumeration.
    """
    target_email = None
    if current_user:
        target_email = current_user.email
    elif req.email:
        target_email = req.email.strip().lower()

    generic_response = {
        "status": "success",
        "message": "If the account exists and requires verification, a new confirmation link has been dispatched."
    }

    if not target_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required."
        )

    user = db.query(User).filter(User.email == target_email).first()
    if not user or user.is_email_verified:
        return generic_response

    can_resend, remaining = email_service.can_resend_verification(db, user)
    if not can_resend:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} second(s) before requesting another verification email."
        )

    raw_token, _ = email_service.generate_verification_token(db, user)
    email_service.send_verification_email(user, raw_token, db)

    return generic_response

@router.get("/verification-status")
def get_verification_status(
    current_user: User = Depends(get_current_user)
):
    """Return email verification status of currently authenticated user."""
    return {
        "email": current_user.email,
        "is_email_verified": current_user.is_email_verified
    }


