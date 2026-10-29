import os
import sys
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.user import User
from app.models.enums import UserRoleEnum
from app.core.security import hash_password

logger = logging.getLogger("eduresolve.bootstrap")

BASELINE_ROLES = [
    {"name": "STUDENT", "description": "Enrolled student submitter with private grievance tracking"},
    {"name": "COLLEGE_OFFICER", "description": "Assigned college redressing officer with workflow authority"},
    {"name": "INSTITUTION_HEAD", "description": "Head of institution with executive college oversight"},
    {"name": "REGULATORY_ADMIN", "description": "Regional regulatory body administrator for compliance monitoring"},
    {"name": "SUPER_ADMIN", "description": "Master system administrator with full governance access"}
]

def seed_roles(db: Session) -> list[Role]:
    """
    Safely and idempotently seed the baseline roles.
    Re-running does not create duplicate roles or reset user data.
    """
    seeded_roles = []
    for r_data in BASELINE_ROLES:
        existing_role = db.query(Role).filter(Role.name == r_data["name"]).first()
        if not existing_role:
            new_role = Role(name=r_data["name"], description=r_data["description"])
            db.add(new_role)
            db.commit()
            db.refresh(new_role)
            seeded_roles.append(new_role)
            logger.info("Created baseline role: %s", new_role.name)
        else:
            seeded_roles.append(existing_role)
    return seeded_roles

def bootstrap_super_admin(
    db: Session,
    email: str,
    password: str,
    full_name: str = "System Super Admin"
) -> User:
    """
    Controlled administrative bootstrap for the initial super administrator.
    Requires an explicit secure password (minimum 8 characters).
    Never uses hardcoded passwords.
    """
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean:
        raise ValueError("A valid email address is required.")
    
    if not password or len(password) < 8:
        raise ValueError("Super Admin password must be at least 8 characters long.")
    
    # Ensure roles exist first
    seed_roles(db)

    user = db.query(User).filter(User.email == email_clean).first()
    if user:
        user.full_name = full_name.strip()
        user.hashed_password = hash_password(password)
        user.default_role = UserRoleEnum.SUPER_ADMIN
        user.is_active = True
        user.is_verified = True
        user.is_email_verified = True
        db.commit()
        db.refresh(user)
        logger.info("Updated existing user %s to SUPER_ADMIN role.", email_clean)
        return user
    else:
        new_user = User(
            email=email_clean,
            full_name=full_name.strip(),
            hashed_password=hash_password(password),
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info("Created new SUPER_ADMIN user %s.", email_clean)
        return new_user

INITIAL_ORGANIZATIONAL_UNITS = [
    {
        "code": "RB",
        "name": "Regulation Bureau",
        "unit_type": "BUREAU",
        "description": "Enforcement of AICTE regulations, norms, standards and regulatory compliance scrutiny. Note: Administrator must verify official unit nomenclature.",
        "region_code": None,
        "contact_email": "regulation@aicte-india.org"
    },
    {
        "code": "PGRC",
        "name": "Public Grievance Redressal Cell",
        "unit_type": "CELL",
        "description": "Central cell monitoring complaints and grievances from students, faculty, staff and public stakeholders. Note: Administrator must verify official unit nomenclature.",
        "region_code": None,
        "contact_email": "pg-cell@aicte-india.org"
    },
    {
        "code": "AB",
        "name": "Approval Bureau",
        "unit_type": "BUREAU",
        "description": "Processing of institutional approvals, extensions, intake revisions, and closure accreditations. Note: Administrator must verify official unit nomenclature.",
        "region_code": None,
        "contact_email": "approval@aicte-india.org"
    },
    {
        "code": "RO_NORTH",
        "name": "Regional Office, North",
        "unit_type": "REGIONAL_OFFICE",
        "description": "Northern regional oversight covering designated northern states and union territories. Note: Administrator must verify regional jurisdictional mapping.",
        "region_code": "NORTH",
        "contact_email": "ro.north@aicte-india.org"
    },
    {
        "code": "RO_WEST",
        "name": "Regional Office, West",
        "unit_type": "REGIONAL_OFFICE",
        "description": "Western regional oversight covering designated western states. Note: Administrator must verify regional jurisdictional mapping.",
        "region_code": "WEST",
        "contact_email": "ro.west@aicte-india.org"
    },
    {
        "code": "RO_SOUTH",
        "name": "Regional Office, South",
        "unit_type": "REGIONAL_OFFICE",
        "description": "Southern regional oversight covering designated southern states. Note: Administrator must verify regional jurisdictional mapping.",
        "region_code": "SOUTH",
        "contact_email": "ro.south@aicte-india.org"
    }
]

def seed_organizational_units(db: Session):
    """
    Safely and idempotently seed initial AICTE organizational units.
    Re-running does not create duplicates or overwrite administrator-edited values.
    """
    from app.models.organizational_unit import OrganizationalUnit

    seeded_units = []
    for u_data in INITIAL_ORGANIZATIONAL_UNITS:
        existing = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == u_data["code"]).first()
        if not existing:
            new_unit = OrganizationalUnit(
                code=u_data["code"],
                name=u_data["name"],
                unit_type=u_data["unit_type"],
                description=u_data["description"],
                region_code=u_data["region_code"],
                contact_email=u_data["contact_email"],
                is_active=True
            )
            db.add(new_unit)
            db.commit()
            db.refresh(new_unit)
            seeded_units.append(new_unit)
            logger.info("Created organizational unit: %s (%s)", new_unit.code, new_unit.name)
        else:
            seeded_units.append(existing)

    return seeded_units

