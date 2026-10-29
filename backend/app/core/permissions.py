from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.enums import UserRoleEnum
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.grievance import Grievance

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    """Retrieve current user if a valid bearer token is supplied, otherwise return None without raising 401."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id_str = payload.get("sub")

    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Reusable dependency ensuring the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact an administrator."
        )
    return current_user

def require_roles(*allowed_roles):
    """Reusable role-requirement dependency factory."""
    flat_roles = []
    for r in allowed_roles:
        if isinstance(r, (list, tuple, set)):
            flat_roles.extend(r)
        else:
            flat_roles.append(r)

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.default_role == UserRoleEnum.SUPER_ADMIN:
            return current_user
            
        # Check default role
        if current_user.default_role in flat_roles:
            return current_user
            
        # Check institution memberships roles
        membership_roles = [m.role for m in current_user.memberships if m.is_active]
        for role in membership_roles:
            if role in flat_roles:
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: insufficient role permissions."
        )
    return role_checker

def require_super_admin(current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN))) -> User:
    """Super-admin-only reusable authorization dependency."""
    return current_user

def get_user_institution_ids(user: User, db: Session) -> List[int]:
    """Return all institution IDs a user has active membership with."""
    if user.default_role == UserRoleEnum.SUPER_ADMIN:
        return [inst.id for inst in db.query(Institution).all()]
    return [m.institution_id for m in user.memberships if m.is_active]

def check_institution_access(user: User, institution_id: int, db: Session) -> bool:
    """Check if the user has legitimate access to an institution via membership or regulatory jurisdiction."""
    if user.default_role == UserRoleEnum.SUPER_ADMIN:
        return True
    
    # Direct membership check
    user_institutions = get_user_institution_ids(user, db)
    if institution_id in user_institutions:
        return True
        
    # Regulatory admin check - check if institution is in assigned active jurisdiction
    if user.default_role == UserRoleEnum.REGULATORY_ADMIN:
        jurisdictions = db.query(RegulatoryJurisdiction).filter(
            RegulatoryJurisdiction.user_id == user.id,
            RegulatoryJurisdiction.is_active == True
        ).all()
        # Direct institution assignment
        assigned_inst_ids = [j.institution_id for j in jurisdictions if j.institution_id is not None]
        if institution_id in assigned_inst_ids:
            return True

        # State/region-level assignment
        assigned_states = [j.state.strip().lower() for j in jurisdictions if j.state]
        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if inst and inst.state.strip().lower() in assigned_states:
            return True
            
    return False

def check_regulatory_access(user: User, state: str, db: Session) -> bool:
    """Check if a regulatory administrator has jurisdiction over a given state."""
    if user.default_role == UserRoleEnum.SUPER_ADMIN:
        return True
    if user.default_role != UserRoleEnum.REGULATORY_ADMIN:
        return False
    jurisdictions = db.query(RegulatoryJurisdiction).filter(
        RegulatoryJurisdiction.user_id == user.id,
        RegulatoryJurisdiction.is_active == True
    ).all()
    assigned_states = [j.state.strip().lower() for j in jurisdictions if j.state]
    return state.strip().lower() in assigned_states


def check_grievance_access(user: User, grievance: Grievance, db: Session, require_officer_edit: bool = False) -> bool:
    """
    Enforce strict multi-tenant boundary and role-based data isolation:
    - Super Admin: full access
    - Student: only their own grievances (and read/message/feedback only, no officer edits)
    - College Officer: only grievances of their authorized institution
    - Institution Head: only grievances of their authorized institution
    - Regulatory Admin: only grievances of institutions in their assigned jurisdiction
    """
    if user.default_role == UserRoleEnum.SUPER_ADMIN:
        return True

    # If student, strictly verify ownership
    if user.default_role == UserRoleEnum.STUDENT:
        if require_officer_edit:
            return False
        return grievance.student_id == user.id

    # For officers and heads, strictly verify institution membership
    if user.default_role in (UserRoleEnum.COLLEGE_OFFICER, UserRoleEnum.INSTITUTION_HEAD):
        return check_institution_access(user, grievance.institution_id, db)

    # For regulatory admin
    if user.default_role == UserRoleEnum.REGULATORY_ADMIN:
        if require_officer_edit:
            return False
        return check_institution_access(user, grievance.institution_id, db)

    return False

def get_user_bureau_unit_ids(user: User, db: Session) -> List[int]:
    """
    Return all organizational unit IDs a user has an active bureau membership with.
    Super administrators have holistic oversight across all active units.
    """
    from app.models.organizational_unit import OrganizationalUnit
    from app.models.bureau_membership import BureauMembership

    if user.default_role == UserRoleEnum.SUPER_ADMIN:
        return [u.id for u in db.query(OrganizationalUnit).filter(OrganizationalUnit.is_active == True).all()]
    
    return [
        bm.organizational_unit_id for bm in user.bureau_memberships 
        if bm.is_active
    ]

def check_bureau_access(user: User, unit_id: int, db: Session, require_head: bool = False) -> bool:
    """
    Verify access to an AICTE organizational unit / Bureau:
    - Super administrators retain master governance access.
    - College-level roles (STUDENT, COLLEGE_OFFICER, INSTITUTION_HEAD, REGULATORY_ADMIN) NEVER inherit bureau access.
    - Ordinary bureau officers can view unit cases but cannot perform bureau administrative mutations.
    - If require_head=True, user must be SUPER_ADMIN or hold BUREAU_HEAD role in that specific unit.
    """
    if user.default_role == UserRoleEnum.SUPER_ADMIN:
        return True

    # Check active BureauMembership strictly
    for bm in user.bureau_memberships:
        if bm.is_active and bm.organizational_unit_id == unit_id:
            if require_head:
                return bm.membership_role in ("BUREAU_HEAD", "REGIONAL_DIRECTOR", "ADMIN")
            return True

    return False

