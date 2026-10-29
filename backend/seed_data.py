import os
import sys
from datetime import datetime, timezone, timedelta

# Insert backend directory into python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal, engine
from app.database.base import Base
from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum, EscalationLevelEnum
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.category import GrievanceCategory
from app.models.grievance import Grievance, GrievanceStatusHistory
from app.models.communication import GrievanceMessage, GrievanceInternalNote
from app.models.feedback import GrievanceFeedback
from app.models.notification import Notification
from app.core.security import hash_password
from app.services.bootstrap_service import seed_roles, seed_organizational_units
from app.models.role import Role

def seed_database():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 0. Seed baseline roles and AICTE organizational units
        seed_roles(db)
        print("System roles verified.")
        seed_organizational_units(db)
        print("AICTE organizational units verified.")

        # 1. Seed Grievance Categories
        categories_data = [
            {"code": "ACADEMIC", "name": "Academics & Teaching", "sla": 7, "desc": "Issues regarding faculty, classes, syllabus, attendance or course schedules."},
            {"code": "EXAM", "name": "Examinations & Results", "sla": 5, "desc": "Evaluation, admit card, grade sheet corrections, supplementary exams."},
            {"code": "FINANCE", "name": "Fees & Finance", "sla": 5, "desc": "Tuition payment discrepancies, fee refund processing, caution deposit dues."},
            {"code": "SCHOLARSHIP", "name": "Scholarships & Financial Aid", "sla": 10, "desc": "Institutional and government scholarship disbursement and verification."},
            {"code": "HOSTEL", "name": "Hostel & Accommodation", "sla": 3, "desc": "Mess food quality, room allotment, water supply, hostel maintenance."},
            {"code": "INFRA", "name": "Infrastructure & Facilities", "sla": 5, "desc": "Campus WiFi, library facilities, laboratory equipment, sanitation."},
            {"code": "ADMIN", "name": "Administration & Records", "sla": 7, "desc": "ID cards, bonafide certificates, transfer/migration documents."},
            {"code": "CONDUCT", "name": "Student Conduct & Anti-Ragging", "sla": 2, "desc": "Harassment, ragging, discrimination, security or misconduct concerns."},
            {"code": "SUPPORT", "name": "Accessibility & Special Support", "sla": 4, "desc": "Disability ramps, wheelchair access, medical and psychological counseling."}
        ]

        cat_lookup = {}
        for c in categories_data:
            existing_cat = db.query(GrievanceCategory).filter(GrievanceCategory.code == c["code"]).first()
            if not existing_cat:
                new_cat = GrievanceCategory(
                    code=c["code"],
                    name=c["name"],
                    description=c["desc"],
                    default_sla_days=c["sla"],
                    is_active=True
                )
                db.add(new_cat)
                db.commit()
                db.refresh(new_cat)
                cat_lookup[c["code"]] = new_cat
            else:
                cat_lookup[c["code"]] = existing_cat

        print(f"Categories seeded: {len(cat_lookup)}")

        # 2. Seed Institutions
        inst_data = [
            {
                "code": "NITD01",
                "name": "National Institute of Technology Delhi",
                "state": "Delhi",
                "city": "New Delhi",
                "contact_email": "grievance-cell@nitdelhi.ac.in",
                "contact_phone": "+91-11-33861000",
                "website": "https://nitdelhi.ac.in"
            },
            {
                "code": "IISTB02",
                "name": "Indian Institute of Science & Technology Bangalore",
                "state": "Karnataka",
                "city": "Bengaluru",
                "contact_email": "dean.students@iistb.edu.in",
                "contact_phone": "+91-80-22932001",
                "website": "https://iistb.edu.in"
            },
            {
                "code": "MEUM03",
                "name": "Metro Engineering University",
                "state": "Maharashtra",
                "city": "Mumbai",
                "contact_email": "grievances@meumumbai.ac.in",
                "contact_phone": "+91-22-26543000",
                "website": "https://meumumbai.ac.in"
            }
        ]

        inst_lookup = {}
        for inst in inst_data:
            existing_inst = db.query(Institution).filter(Institution.code == inst["code"]).first()
            if not existing_inst:
                new_inst = Institution(
                    code=inst["code"],
                    name=inst["name"],
                    state=inst["state"],
                    city=inst["city"],
                    contact_email=inst["contact_email"],
                    contact_phone=inst["contact_phone"],
                    website=inst["website"],
                    is_active=True,
                    is_verified=True
                )
                db.add(new_inst)
                db.commit()
                db.refresh(new_inst)
                inst_lookup[inst["code"]] = new_inst
            else:
                inst_lookup[inst["code"]] = existing_inst

        print(f"Institutions seeded: {len(inst_lookup)}")

        # 3. Seed Users for each Role
        users_data = [
            {
                "email": "admin@eduresolve.ai",
                "full_name": "Super Administrator",
                "role": UserRoleEnum.SUPER_ADMIN,
                "password": "Password@123",
                "phone": "+91-9876543210"
            },
            {
                "email": "head@nitdelhi.ac.in",
                "full_name": "Dr. Rajesh Sharma (Director)",
                "role": UserRoleEnum.INSTITUTION_HEAD,
                "password": "Password@123",
                "phone": "+91-9876543211",
                "inst_code": "NITD01",
                "dept": "Directorate Office",
                "desig": "Institution Head"
            },
            {
                "email": "officer@nitdelhi.ac.in",
                "full_name": "Prof. Ananya Sen (Grievance Officer)",
                "role": UserRoleEnum.COLLEGE_OFFICER,
                "password": "Password@123",
                "phone": "+91-9876543212",
                "inst_code": "NITD01",
                "dept": "Grievance Redressal Cell",
                "desig": "Senior Grievance Officer"
            },
            {
                "email": "regulator@education.gov.in",
                "full_name": "V. K. Mehta (Regional Director)",
                "role": UserRoleEnum.REGULATORY_ADMIN,
                "password": "Password@123",
                "phone": "+91-9876543213",
                "jurisdiction_state": "Delhi"
            },
            {
                "email": "student@nitdelhi.ac.in",
                "full_name": "Aarav Sharma",
                "role": UserRoleEnum.STUDENT,
                "password": "Password@123",
                "phone": "+91-9876543214",
                "student_id": "2023CSB1042",
                "inst_code": "NITD01"
            }
        ]

        user_lookup = {}
        for u in users_data:
            existing_user = db.query(User).filter(User.email == u["email"]).first()
            if not existing_user:
                new_user = User(
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    phone_number=u["phone"],
                    default_role=u["role"],
                    student_id_number=u.get("student_id"),
                    is_active=True,
                    is_verified=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user_lookup[u["email"]] = new_user

                # Add membership if associated with institution
                if "inst_code" in u and u["inst_code"] in inst_lookup:
                    role_rec = db.query(Role).filter(Role.name == u["role"].value).first()
                    mem = InstitutionMembership(
                        user_id=new_user.id,
                        institution_id=inst_lookup[u["inst_code"]].id,
                        role_id=role_rec.id if role_rec else None,
                        role=u["role"],
                        department=u.get("dept", "General"),
                        designation=u.get("desig", "Student")
                    )
                    db.add(mem)
                    db.commit()


                # Add regulatory jurisdiction if regulatory admin
                if "jurisdiction_state" in u:
                    jur = RegulatoryJurisdiction(
                        user_id=new_user.id,
                        state=u["jurisdiction_state"],
                        jurisdiction_code="NORTH-REG-01",
                        notes="Northern Regional Education Jurisdiction"
                    )
                    db.add(jur)
                    db.commit()
            else:
                user_lookup[u["email"]] = existing_user

        print(f"Users seeded: {len(user_lookup)}")

        # 4. Seed Grievances
        student_user = user_lookup["student@nitdelhi.ac.in"]
        officer_user = user_lookup["officer@nitdelhi.ac.in"]
        nit_inst = inst_lookup["NITD01"]

        existing_grvs = db.query(Grievance).filter(Grievance.institution_id == nit_inst.id).count()
        if existing_grvs == 0:
            sample_grievances = [
                {
                    "ref": "GRV-2026-EXAM01",
                    "title": "Discrepancy in End-Semester Data Structures Grade Sheet",
                    "desc": "My official grade card shows an 'Absent' status for CS201 Data Structures exam, even though I attended and signed the attendance sheet in Exam Hall 3. Requesting urgent verification with the exam superintendent.",
                    "cat": "EXAM",
                    "status": GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
                    "prio": GrievancePriorityEnum.HIGH,
                    "ai_cat": "EXAM",
                    "ai_conf": 0.94,
                    "ai_prio": GrievancePriorityEnum.HIGH,
                    "ai_exp": "Matched keywords 'grade card', 'exam', 'attendance sheet'. High priority due to semester result deadlines.",
                    "assigned": officer_user.id
                },
                {
                    "ref": "GRV-2026-HOST02",
                    "title": "Severe Water Supply Disruption in Boys Hostel Block C",
                    "desc": "Block C 3rd floor has had no running water for the past 36 hours. Students are unable to access basic hygiene facilities before morning classes.",
                    "cat": "HOSTEL",
                    "status": GrievanceStatusEnum.SUBMITTED,
                    "prio": GrievancePriorityEnum.HIGH,
                    "ai_cat": "HOSTEL",
                    "ai_conf": 0.91,
                    "ai_prio": GrievancePriorityEnum.HIGH,
                    "ai_exp": "Matched keywords 'hostel', 'water', 'hygiene'. Urgency flagged for basic amenities.",
                    "assigned": officer_user.id
                },
                {
                    "ref": "GRV-2026-FEE003",
                    "title": "Excess Caution Deposit Deducted During Semester Registration",
                    "desc": "During the recent fee portal registration, my transaction debited twice. Bank transaction IDs are attached and college accounts desk hasn't refunded the excess Rs. 15,000.",
                    "cat": "FINANCE",
                    "status": GrievanceStatusEnum.RESOLVED,
                    "prio": GrievancePriorityEnum.NORMAL,
                    "ai_cat": "FINANCE",
                    "ai_conf": 0.89,
                    "ai_prio": GrievancePriorityEnum.NORMAL,
                    "ai_exp": "Matched keywords 'fee', 'debited', 'refund'. Normal operational financial inquiry.",
                    "assigned": officer_user.id,
                    "res_summary": "Accounts section confirmed duplicate debit with payment gateway. Refund of Rs. 15,000 processed to student's bank account on 24th Oct.",
                    "has_feedback": True
                }
            ]

            now = datetime.now(timezone.utc)
            for g_item in sample_grievances:
                category = cat_lookup[g_item["cat"]]
                grv = Grievance(
                    reference_number=g_item["ref"],
                    student_id=student_user.id,
                    institution_id=nit_inst.id,
                    category_id=category.id,
                    title=g_item["title"],
                    description=g_item["desc"],
                    status=g_item["status"],
                    priority=g_item["prio"],
                    is_confidential=False,
                    preferred_contact="portal",
                    ai_suggested_category_id=category.id,
                    ai_confidence=g_item["ai_conf"],
                    ai_suggested_priority=g_item["ai_prio"],
                    ai_explanation=g_item["ai_exp"],
                    assigned_officer_id=g_item.get("assigned"),
                    due_date=now + timedelta(days=5),
                    resolution_summary=g_item.get("res_summary"),
                    resolved_at=now - timedelta(days=1) if g_item["status"] == GrievanceStatusEnum.RESOLVED else None
                )
                db.add(grv)
                db.commit()
                db.refresh(grv)

                # Add history
                hist = GrievanceStatusHistory(
                    grievance_id=grv.id,
                    from_status=None,
                    to_status=GrievanceStatusEnum.SUBMITTED,
                    changed_by_user_id=student_user.id,
                    reason="Grievance submitted by student."
                )
                db.add(hist)

                if grv.status != GrievanceStatusEnum.SUBMITTED:
                    hist2 = GrievanceStatusHistory(
                        grievance_id=grv.id,
                        from_status=GrievanceStatusEnum.SUBMITTED,
                        to_status=grv.status,
                        changed_by_user_id=officer_user.id,
                        reason="Assigned and under review by grievance cell."
                    )
                    db.add(hist2)

                # Add a message
                msg = GrievanceMessage(
                    grievance_id=grv.id,
                    sender_id=officer_user.id,
                    message="Case acknowledged. We are currently checking the respective department records.",
                    is_student_visible=True
                )
                db.add(msg)

                # Add internal note
                note = GrievanceInternalNote(
                    grievance_id=grv.id,
                    author_id=officer_user.id,
                    note="Internal memo sent to HOD/Accounts supervisor for verification."
                )
                db.add(note)

                # If feedback
                if g_item.get("has_feedback"):
                    fb = GrievanceFeedback(
                        grievance_id=grv.id,
                        student_id=student_user.id,
                        rating=5,
                        satisfies_resolution=True,
                        comments="Resolved promptly within 2 days! Thank you for the assistance."
                    )
                    db.add(fb)

                db.commit()

            print("Sample grievances seeded successfully.")

        print("=== Database Seeding Complete! ===")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
