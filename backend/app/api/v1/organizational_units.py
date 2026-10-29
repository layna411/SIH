import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.connection import get_db
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.user import User
from app.models.enums import UserRoleEnum
from app.core.permissions import (
    get_current_user,
    get_current_active_user,
    require_roles,
    check_bureau_access
)
from app.schemas.organizational_unit import (
    OrganizationalUnitCreate,
    OrganizationalUnitUpdate,
    OrganizationalUnitResponse,
    BureauMembershipCreate,
    BureauMembershipUpdate,
    BureauMembershipResponse
)
from app.services.bootstrap_service import seed_organizational_units
from app.services.audit_service import log_audit

logger = logging.getLogger("eduresolve.organizational_units")

router = APIRouter(prefix="/organizational-units", tags=["Organizational Units & Bureaus"])

def check_hierarchy_cycle(unit_id: int, proposed_parent_id: Optional[int], db: Session) -> bool:
    """Validate that setting parent_unit_id does not introduce a cyclic hierarchy."""
    if proposed_parent_id is None:
        return False
    if proposed_parent_id == unit_id:
        return True
    visited = {unit_id}
    curr = proposed_parent_id
    while curr:
        if curr in visited:
            return True
        visited.add(curr)
        parent_obj = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == curr).first()
        if not parent_obj or not parent_obj.parent_unit_id:
            break
        curr = parent_obj.parent_unit_id
    return False

def build_unit_response(unit: OrganizationalUnit) -> OrganizationalUnitResponse:
    active_members_count = sum(1 for m in unit.memberships if m.is_active)
    return OrganizationalUnitResponse(
        id=unit.id,
        code=unit.code,
        name=unit.name,
        unit_type=unit.unit_type,
        description=unit.description,
        parent_unit_id=unit.parent_unit_id,
        parent_unit_name=unit.parent_unit.name if unit.parent_unit else None,
        region_code=unit.region_code,
        contact_email=unit.contact_email,
        is_active=unit.is_active,
        created_at=unit.created_at,
        updated_at=unit.updated_at,
        member_count=active_members_count
    )

@router.get("", response_model=List[OrganizationalUnitResponse])
def list_organizational_units(
    unit_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List AICTE organizational units (Bureaus, Cells, Regional Offices).
    Accessible to authenticated users; internal administrative fields are strictly scoped.
    """
    query = db.query(OrganizationalUnit)

    if unit_type:
        query = query.filter(OrganizationalUnit.unit_type == unit_type.strip().upper())
    if is_active is not None:
        query = query.filter(OrganizationalUnit.is_active == is_active)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                OrganizationalUnit.name.ilike(search_pattern),
                OrganizationalUnit.code.ilike(search_pattern),
                OrganizationalUnit.description.ilike(search_pattern)
            )
        )

    units = query.order_by(OrganizationalUnit.unit_type.asc(), OrganizationalUnit.name.asc()).all()
    return [build_unit_response(u) for u in units]

@router.get("/{id}", response_model=OrganizationalUnitResponse)
def get_organizational_unit(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve detailed metadata for an organizational unit."""
    unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizational unit not found.")
    return build_unit_response(unit)

@router.post("", response_model=OrganizationalUnitResponse, status_code=status.HTTP_201_CREATED)
def create_organizational_unit(
    req: OrganizationalUnitCreate,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new AICTE organizational unit (Super Admin only)."""
    code_clean = req.code.strip().upper()
    existing = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organizational unit with code '{code_clean}' already exists."
        )

    if req.parent_unit_id:
        parent_exists = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == req.parent_unit_id).first()
        if not parent_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified parent organizational unit does not exist."
            )

    new_unit = OrganizationalUnit(
        code=code_clean,
        name=req.name.strip(),
        unit_type=req.unit_type.strip().upper(),
        description=req.description.strip() if req.description else None,
        parent_unit_id=req.parent_unit_id,
        region_code=req.region_code.strip().upper() if req.region_code else None,
        contact_email=req.contact_email.strip().lower() if req.contact_email else None,
        is_active=req.is_active
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)

    log_audit(
        db,
        action="CREATE_ORGANIZATIONAL_UNIT",
        entity_type="ORGANIZATIONAL_UNIT",
        user_id=current_user.id,
        entity_id=str(new_unit.id),
        details={"code": new_unit.code, "name": new_unit.name, "unit_type": new_unit.unit_type}
    )
    return build_unit_response(new_unit)

@router.put("/{id}", response_model=OrganizationalUnitResponse)
def update_organizational_unit(
    id: int,
    req: OrganizationalUnitUpdate,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Update organizational unit metadata with cycle protection (Super Admin only)."""
    unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizational unit not found.")

    payload = req.model_dump(exclude_unset=True)

    if "code" in payload and payload["code"]:
        new_code = payload["code"].strip().upper()
        if new_code != unit.code:
            existing = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == new_code, OrganizationalUnit.id != id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Organizational unit with code '{new_code}' already exists."
                )
            unit.code = new_code

    if "parent_unit_id" in payload:
        new_parent_id = payload["parent_unit_id"]
        if new_parent_id is not None:
            parent_exists = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == new_parent_id).first()
            if not parent_exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified parent unit does not exist.")
            if check_hierarchy_cycle(id, new_parent_id, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid parent unit: hierarchy cycle or self-reference detected."
                )
        unit.parent_unit_id = new_parent_id

    for key, val in payload.items():
        if key not in ("code", "parent_unit_id"):
            setattr(unit, key, val)

    db.commit()
    db.refresh(unit)

    log_audit(
        db,
        action="UPDATE_ORGANIZATIONAL_UNIT",
        entity_type="ORGANIZATIONAL_UNIT",
        user_id=current_user.id,
        entity_id=str(unit.id),
        details={"code": unit.code, "name": unit.name}
    )
    return build_unit_response(unit)

@router.post("/seed-defaults", response_model=List[OrganizationalUnitResponse])
def seed_default_units(
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Idempotently seed the baseline AICTE units (RB, PGRC, AB, RO_NORTH, RO_WEST, RO_SOUTH).
    Safe to execute multiple times; never duplicates or overwrites manual administrator edits.
    """
    seeded = seed_organizational_units(db)
    log_audit(
        db,
        action="SEED_ORGANIZATIONAL_UNITS",
        entity_type="ORGANIZATIONAL_UNIT",
        user_id=current_user.id,
        details=f"Verified/seeded {len(seeded)} units."
    )
    return [build_unit_response(u) for u in seeded]

# Bureau Membership Endpoints
@router.get("/{id}/members", response_model=List[BureauMembershipResponse])
def list_unit_memberships(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List member officers belonging to an organizational unit.
    Requires Super Admin or active Bureau access to the unit.
    """
    unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizational unit not found.")

    if not check_bureau_access(current_user, id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to view this bureau's staff.")

    members = db.query(BureauMembership).filter(
        BureauMembership.organizational_unit_id == id
    ).all()

    return [
        BureauMembershipResponse(
            id=m.id,
            user_id=m.user_id,
            user_name=m.user.full_name if m.user else None,
            user_email=m.user.email if m.user else None,
            organizational_unit_id=m.organizational_unit_id,
            unit_code=unit.code,
            unit_name=unit.name,
            membership_role=m.membership_role,
            designation=m.designation,
            is_active=m.is_active,
            assigned_by_user_id=m.assigned_by_user_id,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in members
    ]

@router.post("/{id}/members", response_model=BureauMembershipResponse, status_code=status.HTTP_201_CREATED)
def assign_bureau_membership(
    id: int,
    req: BureauMembershipCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Assign a user to an AICTE organizational unit.
    Restricted to Super Administrators and Bureau Heads of that unit.
    College-level roles (College Officers, College Heads) cannot assign Bureau memberships.
    """
    unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizational unit not found.")

    if not check_bureau_access(current_user, id, db, require_head=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: assigning bureau staff requires Super Admin or Bureau Head authority."
        )

    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")

    existing_membership = db.query(BureauMembership).filter(
        BureauMembership.user_id == req.user_id,
        BureauMembership.organizational_unit_id == id
    ).first()

    if existing_membership:
        existing_membership.membership_role = req.membership_role.strip().upper()
        existing_membership.designation = req.designation.strip() if req.designation else None
        existing_membership.is_active = True
        existing_membership.assigned_by_user_id = current_user.id
        db.commit()
        db.refresh(existing_membership)
        membership = existing_membership
    else:
        membership = BureauMembership(
            user_id=req.user_id,
            organizational_unit_id=id,
            membership_role=req.membership_role.strip().upper(),
            designation=req.designation.strip() if req.designation else None,
            is_active=True,
            assigned_by_user_id=current_user.id
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)

    log_audit(
        db,
        action="ASSIGN_BUREAU_MEMBERSHIP",
        entity_type="BUREAU_MEMBERSHIP",
        user_id=current_user.id,
        entity_id=str(membership.id),
        details={"unit_id": id, "target_user_id": target_user.id, "role": membership.membership_role}
    )

    return BureauMembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        user_name=target_user.full_name,
        user_email=target_user.email,
        organizational_unit_id=id,
        unit_code=unit.code,
        unit_name=unit.name,
        membership_role=membership.membership_role,
        designation=membership.designation,
        is_active=membership.is_active,
        assigned_by_user_id=membership.assigned_by_user_id,
        created_at=membership.created_at,
        updated_at=membership.updated_at
    )

@router.delete("/{id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_bureau_membership(
    id: int,
    membership_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke or deactivate an AICTE Bureau membership.
    Restricted to Super Administrators and Bureau Heads of that unit.
    """
    membership = db.query(BureauMembership).filter(
        BureauMembership.id == membership_id,
        BureauMembership.organizational_unit_id == id
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bureau membership not found.")

    if not check_bureau_access(current_user, id, db, require_head=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: revoking bureau staff requires Super Admin or Bureau Head authority."
        )

    # Soft deactivate membership
    membership.is_active = False
    db.commit()

    log_audit(
        db,
        action="REVOKE_BUREAU_MEMBERSHIP",
        entity_type="BUREAU_MEMBERSHIP",
        user_id=current_user.id,
        entity_id=str(membership_id),
        details={"unit_id": id, "user_id": membership.user_id}
    )
    return None
