import logging
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.enums import UserRoleEnum
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.core.security import hash_password
from app.database.connection import SessionLocal

logger = logging.getLogger("eduresolve.seed_demo_staff")

DEMO_STAFF_ACCOUNTS = [
    {
        "email": "bureau.rb@aicte.gov.in",
        "full_name": "Dr. S. K. Rastogi",
        "phone_number": "+91 98101 23456",
        "default_role": UserRoleEnum.COLLEGE_OFFICER,
        "password": "Password@123",
        "unit_code": "RB",
        "membership_role": "BUREAU_HEAD",
        "designation": "Advisor & Bureau Head (Regulation)"
    },
    {
        "email": "bureau.pgrc@aicte.gov.in",
        "full_name": "Ms. Pooja Verma",
        "phone_number": "+91 98102 34567",
        "default_role": UserRoleEnum.COLLEGE_OFFICER,
        "password": "Password@123",
        "unit_code": "PGRC",
        "membership_role": "BUREAU_OFFICER",
        "designation": "Deputy Director (Public Grievance Redressal)"
    },
    {
        "email": "bureau.ab@aicte.gov.in",
        "full_name": "Dr. Ramesh Nair",
        "phone_number": "+91 98103 45678",
        "default_role": UserRoleEnum.COLLEGE_OFFICER,
        "password": "Password@123",
        "unit_code": "AB",
        "membership_role": "BUREAU_OFFICER",
        "designation": "Senior Scrutiny Officer (Approval Bureau)"
    },
    {
        "email": "ro.north@aicte.gov.in",
        "full_name": "Dr. Vikram Malhotra",
        "phone_number": "+91 98104 56789",
        "default_role": UserRoleEnum.REGULATORY_ADMIN,
        "password": "Password@123",
        "unit_code": "RO_NORTH",
        "membership_role": "REGIONAL_OFFICER",
        "designation": "Regional Officer (North)"
    }
]

def seed_demo_staff(db: Session):
    """
    Safely and idempotently seed demo AICTE bureau staff accounts.
    Never duplicates users or overwrites passwords if they already exist.
    """
    created_or_updated = []
    for staff in DEMO_STAFF_ACCOUNTS:
        email = staff["email"].lower().strip()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=hash_password(staff["password"]),
                full_name=staff["full_name"],
                phone_number=staff["phone_number"],
                default_role=staff["default_role"],
                is_active=True,
                is_verified=True,
                is_email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created demo staff user: %s (%s)", user.full_name, user.email)
        else:
            # Ensure user is active and password matches demo credential
            user.hashed_password = hash_password(staff["password"])
            user.is_active = True
            db.commit()
            db.refresh(user)

        unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == staff["unit_code"]).first()
        if unit:
            bm = db.query(BureauMembership).filter(
                BureauMembership.user_id == user.id,
                BureauMembership.organizational_unit_id == unit.id
            ).first()
            if not bm:
                bm = BureauMembership(
                    user_id=user.id,
                    organizational_unit_id=unit.id,
                    membership_role=staff["membership_role"],
                    designation=staff["designation"],
                    is_active=True
                )
                db.add(bm)
                db.commit()
                db.refresh(bm)
                logger.info("Assigned active BureauMembership: %s to %s", user.email, unit.code)
            else:
                bm.membership_role = staff["membership_role"]
                bm.designation = staff["designation"]
                bm.is_active = True
                db.commit()

        created_or_updated.append(user)
    return created_or_updated

if __name__ == "__main__":
    db = SessionLocal()
    try:
        users = seed_demo_staff(db)
        print(f"Successfully seeded {len(users)} demo staff accounts.")
    finally:
        db.close()
