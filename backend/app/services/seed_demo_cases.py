import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseActionTypeEnum,
    AICTECaseSourceTypeEnum,
    AICTEComplainantTypeEnum,
    GrievancePriorityEnum,
    AICTETransferStatusEnum,
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTEDetectionMethodEnum,
)
from app.models.user import User
from app.models.institution import Institution
from app.models.organizational_unit import OrganizationalUnit
from app.models.grievance import Grievance
from app.models.aicte_case import AICTECase, CaseAction
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.aicte_overlap import AICTECaseOverlap
from app.services.aicte_alert_service import AICTEAlertService

logger = logging.getLogger("eduresolve.seed_demo_cases")

def seed_demo_cases(db: Session):
    """
    Safely and idempotently seed realistic AICTE demo cases, procedural actions,
    inter-Bureau transfers, overlap candidates, and alerts.
    """
    now = datetime.now(timezone.utc)

    # 1. Fetch Users
    admin = db.query(User).filter(User.email == "admin@eduresolve.ai").first()
    bureau_rb = db.query(User).filter(User.email == "bureau.rb@aicte.gov.in").first()
    bureau_pgrc = db.query(User).filter(User.email == "bureau.pgrc@aicte.gov.in").first()
    bureau_ab = db.query(User).filter(User.email == "bureau.ab@aicte.gov.in").first()
    ro_north = db.query(User).filter(User.email == "ro.north@aicte.gov.in").first()
    regulator = db.query(User).filter(User.email == "regulator@education.gov.in").first() or admin
    college_officer = db.query(User).filter(User.email == "officer@nitdelhi.ac.in").first() or admin

    if not bureau_rb or not bureau_pgrc or not bureau_ab or not ro_north:
        logger.error("Required demo bureau staff accounts not found. Run seed_demo_staff first.")
        return []

    # 2. Fetch Units
    unit_rb = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB").first()
    unit_pgrc = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC").first()
    unit_ab = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == "AB").first()
    unit_ron = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RO_NORTH").first()
    unit_row = db.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RO_WEST").first() or unit_ron

    # 3. Fetch Institutions
    inst_nitd = db.query(Institution).filter(Institution.code == "NITD01").first() or db.query(Institution).first()
    inst_meum = db.query(Institution).filter(Institution.code == "MEUM03").first() or inst_nitd
    inst_simats = db.query(Institution).filter(Institution.code == "SIMATS101").first() or inst_nitd
    inst_iistb = db.query(Institution).filter(Institution.code == "IISTB02").first() or inst_nitd

    # Fetch Campus Grievances for linking
    grv_hostel = db.query(Grievance).filter(Grievance.reference_number == "GRV-2026-HOST02").first()
    grv_fee = db.query(Grievance).filter(Grievance.reference_number == "GRV-2026-FEE003").first()

    created_cases = []

    # =========================================================================
    # CASE 1: AICTE-2026-RB-001 (Regulation Bureau — Overdue Next Action Alert)
    # =========================================================================
    case1 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-RB-001").first()
    if not case1:
        case1 = AICTECase(
            case_reference="AICTE-2026-RB-001",
            institution_id=inst_nitd.id,
            source_type=AICTECaseSourceTypeEnum.DIRECT,
            official_reference_number="AICTE/RB/2026/0411",
            received_at=now - timedelta(days=14),
            complainant_type=AICTEComplainantTypeEnum.STAKEHOLDER,
            complainant_name="Dr. Vinod Kapoor (Parents Association)",
            complainant_email="v.kapoor.assoc@gmail.com",
            complainant_phone="+91 98111 22334",
            category="Regulatory Compliance",
            subject="Mandatory AICTE Anti-Ragging Committee Non-Compliance & Squad Vacancy",
            description=(
                "Complaint filed under AICTE (Prevention and Prohibition of Ragging in Technical Institutions) "
                "Regulations, 2009. The statutory Anti-Ragging Committee and Squad have not been reconstituted "
                "for the 2025-26 academic cycle, and emergency helpline contact numbers displayed on campus "
                "remain non-functional."
            ),
            status=AICTECaseStatusEnum.UNDER_PROCESS,
            current_unit_id=unit_rb.id,
            assigned_officer_id=bureau_rb.id,
            region="Northern",
            priority=GrievancePriorityEnum.HIGH,
            last_action_at=now - timedelta(days=3),
            next_action_required="Submit formal show-cause compliance report to Regulation Bureau",
            next_action_due_at=now - timedelta(days=2),  # OVERDUE alert!
            expected_disposal_at=now + timedelta(days=12),
            created_by_user_id=admin.id,
            created_at=now - timedelta(days=14)
        )
        db.add(case1)
        db.commit()
        db.refresh(case1)

        # Procedural Actions
        a1 = CaseAction(
            case_id=case1.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Direct Regulatory Complaint Registered",
            action_description="Case admitted through AICTE Centralized Regulatory Intake Portal.",
            previous_status=None,
            new_status="RECEIVED",
            unit_id=unit_rb.id,
            performed_by_user_id=admin.id,
            action_at=now - timedelta(days=14),
            remarks="Verified prima facie jurisdiction under AICTE Anti-Ragging Regulations."
        )
        a2 = CaseAction(
            case_id=case1.id,
            action_type=AICTECaseActionTypeEnum.ASSIGNMENT,
            action_title="Assigned to Bureau Head Dr. S. K. Rastogi",
            action_description="Case assigned to Regulation Bureau for compliance scrutiny.",
            previous_status="RECEIVED",
            new_status="UNDER_PROCESS",
            unit_id=unit_rb.id,
            performed_by_user_id=admin.id,
            action_at=now - timedelta(days=12)
        )
        a3 = CaseAction(
            case_id=case1.id,
            action_type=AICTECaseActionTypeEnum.INFO_REQUESTED,
            action_title="Show Cause Notice Served to NIT Delhi",
            action_description="Notice served under Section 10(1)(v) of AICTE Act. 10 days granted for explanation.",
            previous_status="UNDER_PROCESS",
            new_status="UNDER_PROCESS",
            unit_id=unit_rb.id,
            performed_by_user_id=bureau_rb.id,
            action_at=now - timedelta(days=8),
            next_action_required="Submit formal show-cause compliance report to Regulation Bureau",
            next_action_due_at=now - timedelta(days=2)
        )
        db.add_all([a1, a2, a3])
        db.commit()
        created_cases.append(case1.case_reference)

    # =========================================================================
    # CASE 2: AICTE-2026-PGRC-002 (PGRC — Pending Inter-Bureau Transfer to RB!)
    # =========================================================================
    case2 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-PGRC-002").first()
    if not case2:
        case2 = AICTECase(
            case_reference="AICTE-2026-PGRC-002",
            institution_id=inst_meum.id,
            source_grievance_id=grv_fee.id if grv_fee else None,
            source_type=AICTECaseSourceTypeEnum.CAMPUS_REFERRAL,
            official_reference_number="AICTE/PGRC/TR/2026/089",
            received_at=now - timedelta(days=7),
            complainant_type=AICTEComplainantTypeEnum.STUDENT,
            complainant_name="Neha Sharma",
            complainant_email="neha.s@student.metro.edu",
            complainant_phone="+91 98765 43210",
            category="Student Grievance & Fee Refund",
            subject="Irregular Withholding of Original Educational Certificates & Caution Deposit Refusal",
            description=(
                "Institution refused to return original 10th and 12th certificates following withdrawal "
                "within AICTE permitted cut-off deadline, demanding full remaining 4-year tuition fee as exit penalty."
            ),
            status=AICTECaseStatusEnum.TRANSFER_PENDING,
            current_unit_id=unit_pgrc.id,
            assigned_officer_id=bureau_pgrc.id,
            region="Western",
            priority=GrievancePriorityEnum.URGENT,
            last_action_at=now - timedelta(days=1),
            next_action_required="Pending transfer acceptance by Regulation Bureau for penal sanction",
            next_action_due_at=now + timedelta(hours=28),  # APPROACHING DEADLINE alert!
            expected_disposal_at=now + timedelta(days=14),
            created_by_user_id=college_officer.id,
            created_at=now - timedelta(days=7)
        )
        db.add(case2)
        db.commit()
        db.refresh(case2)

        # Actions
        ca1 = CaseAction(
            case_id=case2.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Campus Grievance Escalated to PGRC",
            action_description="Referral received from College Grievance Redressal Committee.",
            unit_id=unit_pgrc.id,
            performed_by_user_id=college_officer.id,
            action_at=now - timedelta(days=7)
        )
        ca2 = CaseAction(
            case_id=case2.id,
            action_type=AICTECaseActionTypeEnum.INITIAL_SCRUTINY,
            action_title="PGRC Scrutiny Completed",
            action_description="Violation of AICTE Public Notice Advt. No. AICTE/Legal/04(01)/2007 confirmed.",
            unit_id=unit_pgrc.id,
            performed_by_user_id=bureau_pgrc.id,
            action_at=now - timedelta(days=4)
        )
        ca3 = CaseAction(
            case_id=case2.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_INITIATED,
            action_title="Transfer Initiated to Regulation Bureau (RB)",
            action_description="PGRC recommended statutory penalty proceedings under Regulation Bureau.",
            previous_status="UNDER_PROCESS",
            new_status="TRANSFER_PENDING",
            unit_id=unit_pgrc.id,
            performed_by_user_id=bureau_pgrc.id,
            action_at=now - timedelta(days=1)
        )
        db.add_all([ca1, ca2, ca3])

        # Active Transfer Record (PENDING_ACCEPTANCE)
        transfer1 = AICTECaseTransfer(
            case_id=case2.id,
            from_unit_id=unit_pgrc.id,
            to_unit_id=unit_rb.id,
            initiated_by_user_id=bureau_pgrc.id,
            proposed_assignee_id=bureau_rb.id,
            transfer_reason=(
                "Institutional non-compliance with fee refund norms requires invoking Regulation Bureau "
                "statutory withdrawal of approval powers under Chapter IV of AICTE Regulations."
            ),
            handover_summary="Student submitted certified bank statements and campus withdrawal receipt.",
            prior_case_status="UNDER_PROCESS",
            transfer_status=AICTETransferStatusEnum.PENDING_ACCEPTANCE,
            initiated_at=now - timedelta(days=1)
        )
        db.add(transfer1)
        db.commit()
        created_cases.append(case2.case_reference)

    # =========================================================================
    # CASE 3: AICTE-2026-AB-003 (Approval Bureau — Intake & Seat Matrix Violation)
    # =========================================================================
    case3 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-AB-003").first()
    if not case3:
        case3 = AICTECase(
            case_reference="AICTE-2026-AB-003",
            institution_id=inst_simats.id,
            source_type=AICTECaseSourceTypeEnum.DIRECT,
            official_reference_number="AICTE/AB/2026/SCRUTINY-77",
            received_at=now - timedelta(days=10),
            complainant_type=AICTEComplainantTypeEnum.FACULTY,
            complainant_name="Prof. K. Sundaram",
            complainant_email="k.sundaram.edu@outlook.com",
            complainant_phone="+91 94440 12345",
            category="Approval & Accreditation",
            subject="Expansion of Computer Science Intake Exceeding AICTE Approved Seat Matrix",
            description=(
                "Institution admitted 360 students against approved intake of 180 in B.Tech Computer Science "
                "and Engineering without obtaining Extension of Approval (EoA) or supernumerary approval."
            ),
            status=AICTECaseStatusEnum.AWAITING_RESPONSE,
            current_unit_id=unit_ab.id,
            assigned_officer_id=bureau_ab.id,
            region="Southern",
            priority=GrievancePriorityEnum.HIGH,
            last_action_at=now - timedelta(days=2),
            next_action_required="Receive verified infrastructure inspection logs and faculty roster",
            next_action_due_at=now + timedelta(days=4),
            expected_disposal_at=now + timedelta(days=18),
            created_by_user_id=bureau_ab.id,
            created_at=now - timedelta(days=10)
        )
        db.add(case3)
        db.commit()
        db.refresh(case3)

        act3_1 = CaseAction(
            case_id=case3.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Faculty Complaint on Unapproved Seat Expansion",
            action_description="Direct formal submission with enrollment rosters attached.",
            unit_id=unit_ab.id,
            performed_by_user_id=bureau_ab.id,
            action_at=now - timedelta(days=10)
        )
        act3_2 = CaseAction(
            case_id=case3.id,
            action_type=AICTECaseActionTypeEnum.INFO_REQUESTED,
            action_title="Direct Scrutiny Query Issued to Registrar",
            action_description="Demanded official admission ledger, state counselling allotment lists, and faculty registers.",
            previous_status="UNDER_PROCESS",
            new_status="AWAITING_RESPONSE",
            unit_id=unit_ab.id,
            performed_by_user_id=bureau_ab.id,
            action_at=now - timedelta(days=2),
            next_action_required="Receive verified infrastructure inspection logs and faculty roster",
            next_action_due_at=now + timedelta(days=4)
        )
        db.add_all([act3_1, act3_2])
        db.commit()
        created_cases.append(case3.case_reference)

    # =========================================================================
    # CASE 4: AICTE-2026-AB-004 (Approval Bureau — Overlap Candidate with Case 3!)
    # =========================================================================
    case4 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-AB-004").first()
    if not case4:
        case4 = AICTECase(
            case_reference="AICTE-2026-AB-004",
            institution_id=inst_simats.id,
            source_type=AICTECaseSourceTypeEnum.DIRECT,
            official_reference_number="AICTE/AB/2026/DUP-901",
            received_at=now - timedelta(days=8),
            complainant_type=AICTEComplainantTypeEnum.STUDENT,
            complainant_name="Anand R.",
            complainant_email="anand.student@gmail.com",
            complainant_phone="+91 94441 56789",
            category="Approval & Accreditation",
            subject="Admission Irregularities and Lab Shortage in AI & Data Science B.Tech Division",
            description=(
                "Overcrowded classrooms and severe computer lab equipment shortage following massive unapproved "
                "intake surge in computer division for academic year 2025-26."
            ),
            status=AICTECaseStatusEnum.UNDER_PROCESS,
            current_unit_id=unit_ab.id,
            assigned_officer_id=bureau_ab.id,
            region="Southern",
            priority=GrievancePriorityEnum.NORMAL,
            last_action_at=now - timedelta(days=2),
            next_action_required="Cross-reference with Case AICTE-2026-AB-003",
            next_action_due_at=now + timedelta(days=3),
            expected_disposal_at=now + timedelta(days=20),
            created_by_user_id=admin.id,
            created_at=now - timedelta(days=8)
        )
        db.add(case4)
        db.commit()
        db.refresh(case4)

        act4_1 = CaseAction(
            case_id=case4.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Student Complaint Registered",
            action_description="Complaint flagged by Automated Overlap Detection Engine.",
            unit_id=unit_ab.id,
            performed_by_user_id=admin.id,
            action_at=now - timedelta(days=8)
        )
        db.add(act4_1)

        # Create Overlap Candidate between Case 3 and Case 4
        c_low = min(case3.id, case4.id)
        c_high = max(case3.id, case4.id)
        existing_overlap = db.query(AICTECaseOverlap).filter(
            AICTECaseOverlap.case_id_low == c_low,
            AICTECaseOverlap.case_id_high == c_high
        ).first()

        if not existing_overlap:
            overlap1 = AICTECaseOverlap(
                case_id_low=c_low,
                case_id_high=c_high,
                overlap_type=AICTEOverlapTypeEnum.POTENTIAL_DUPLICATE,
                match_score=0.89,
                match_reasons=json.dumps({
                    "common_institution": True,
                    "institution_name": inst_simats.name,
                    "category_match": True,
                    "subject_similarity": 0.86,
                    "keyword_overlap": ["intake", "unapproved", "computer", "admission", "shortage"]
                }),
                detection_method=AICTEDetectionMethodEnum.HYBRID,
                review_status=AICTEOverlapReviewStatusEnum.PENDING,
                detected_at=now - timedelta(days=8)
            )
            db.add(overlap1)

        db.commit()
        created_cases.append(case4.case_reference)

    # =========================================================================
    # CASE 5: AICTE-2026-RON-005 (RO North — Passed Expected Disposal Date Alert)
    # =========================================================================
    case5 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-RON-005").first()
    if not case5:
        case5 = AICTECase(
            case_reference="AICTE-2026-RON-005",
            institution_id=inst_nitd.id,
            source_grievance_id=grv_hostel.id if grv_hostel else None,
            source_type=AICTECaseSourceTypeEnum.CAMPUS_REFERRAL,
            official_reference_number="AICTE/RON/2026/HOSTEL-09",
            received_at=now - timedelta(days=35),
            complainant_type=AICTEComplainantTypeEnum.STUDENT,
            complainant_name="Aarav Sharma",
            complainant_email="student@nitdelhi.ac.in",
            complainant_phone="+91 98123 45678",
            category="Infrastructure Deficiencies",
            subject="Substandard Hostel Sanitation & Potable Water Disruption in Hostels B & C",
            description=(
                "Chronic drinking water contamination and non-operational RO filtration units in resident student hostels. "
                "Multiple jaundice cases reported among resident scholars without emergency medical intervention."
            ),
            status=AICTECaseStatusEnum.ESCALATED,
            current_unit_id=unit_ron.id,
            assigned_officer_id=ro_north.id,
            region="Northern",
            priority=GrievancePriorityEnum.URGENT,
            last_action_at=now - timedelta(days=6),
            next_action_required="Physical spot-check by AICTE Regional Inspection Committee",
            next_action_due_at=now - timedelta(days=1),   # OVERDUE NEXT ACTION
            expected_disposal_at=now - timedelta(days=5), # OVERDUE DISPOSAL alert!
            created_by_user_id=regulator.id,
            created_at=now - timedelta(days=35)
        )
        db.add(case5)
        db.commit()
        db.refresh(case5)

        act5_1 = CaseAction(
            case_id=case5.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Escalated from Regional Directorate",
            action_description="Direct escalation due to failure of campus grievance redressal within statutory 30 days.",
            unit_id=unit_ron.id,
            performed_by_user_id=regulator.id,
            action_at=now - timedelta(days=35)
        )
        act5_2 = CaseAction(
            case_id=case5.id,
            action_type=AICTECaseActionTypeEnum.HEARING_SCHEDULED,
            action_title="Virtual Inquiry with NIT Delhi Chief Warden",
            action_description="Director and Chief Warden summoned for urgent clarification regarding water testing reports.",
            unit_id=unit_ron.id,
            performed_by_user_id=ro_north.id,
            action_at=now - timedelta(days=18)
        )
        act5_3 = CaseAction(
            case_id=case5.id,
            action_type=AICTECaseActionTypeEnum.ESCALATION,
            action_title="Mandatory On-Site Regional Inspection Ordered",
            action_description="Two-member expert committee dispatched to verify water quality and medical clinic logs.",
            previous_status="UNDER_PROCESS",
            new_status="ESCALATED",
            unit_id=unit_ron.id,
            performed_by_user_id=ro_north.id,
            action_at=now - timedelta(days=6),
            next_action_required="Physical spot-check by AICTE Regional Inspection Committee",
            next_action_due_at=now - timedelta(days=1)
        )
        db.add_all([act5_1, act5_2, act5_3])
        db.commit()
        created_cases.append(case5.case_reference)

    # =========================================================================
    # CASE 6: AICTE-2026-PGRC-006 (PGRC — Successfully Disposed Case)
    # =========================================================================
    case6 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-PGRC-006").first()
    if not case6:
        case6 = AICTECase(
            case_reference="AICTE-2026-PGRC-006",
            institution_id=inst_iistb.id,
            source_type=AICTECaseSourceTypeEnum.DIRECT,
            official_reference_number="AICTE/PGRC/DISP/2026/012",
            received_at=now - timedelta(days=28),
            complainant_type=AICTEComplainantTypeEnum.STUDENT,
            complainant_name="M. Shweta (M.Tech Scholar)",
            complainant_email="m.shweta@iistb.ac.in",
            complainant_phone="+91 97777 88888",
            category="Scholarships & Fellowships",
            subject="Non-Disbursement of AICTE PG GATE Fellowship for 2025-26 Academic Year",
            description=(
                "GATE scholarship stipend withheld for 6 months despite monthly attendance upload on AICTE portal."
            ),
            status=AICTECaseStatusEnum.DISPOSED,
            current_unit_id=unit_pgrc.id,
            assigned_officer_id=bureau_pgrc.id,
            region="Southern",
            priority=GrievancePriorityEnum.NORMAL,
            last_action_at=now - timedelta(days=3),
            next_action_required=None,
            next_action_due_at=None,
            expected_disposal_at=now - timedelta(days=2),
            disposed_at=now - timedelta(days=3),
            created_by_user_id=admin.id,
            created_at=now - timedelta(days=28)
        )
        db.add(case6)
        db.commit()
        db.refresh(case6)

        act6_1 = CaseAction(
            case_id=case6.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Scholarship Grievance Admitted",
            unit_id=unit_pgrc.id,
            performed_by_user_id=admin.id,
            action_at=now - timedelta(days=28)
        )
        act6_2 = CaseAction(
            case_id=case6.id,
            action_type=AICTECaseActionTypeEnum.COMPLIANCE_VERIFIED,
            action_title="PFMS Portal Validation Rectified",
            action_description="Bank IFSC code mapped correctly in National Scholarship Portal (NSP) gateway.",
            unit_id=unit_pgrc.id,
            performed_by_user_id=bureau_pgrc.id,
            action_at=now - timedelta(days=5)
        )
        act6_3 = CaseAction(
            case_id=case6.id,
            action_type=AICTECaseActionTypeEnum.DISPOSAL_ORDER,
            action_title="Formal Disposal Order Issued",
            action_description="Stipend arrears of INR 74,400 successfully credited to beneficiary account. Case disposed.",
            previous_status="UNDER_PROCESS",
            new_status="DISPOSED",
            unit_id=unit_pgrc.id,
            performed_by_user_id=bureau_pgrc.id,
            action_at=now - timedelta(days=3)
        )
        db.add_all([act6_1, act6_2, act6_3])
        db.commit()
        created_cases.append(case6.case_reference)

    # =========================================================================
    # CASE 7: AICTE-2026-RB-007 (Regulation Bureau — Completed Inter-Bureau Transfer)
    # =========================================================================
    case7 = db.query(AICTECase).filter(AICTECase.case_reference == "AICTE-2026-RB-007").first()
    if not case7:
        case7 = AICTECase(
            case_reference="AICTE-2026-RB-007",
            institution_id=inst_meum.id,
            source_type=AICTECaseSourceTypeEnum.WHISTLEBLOWER,
            official_reference_number="AICTE/RB/WB/2026/005",
            received_at=now - timedelta(days=18),
            complainant_type=AICTEComplainantTypeEnum.ANONYMOUS,
            complainant_name="Citizens Higher Education Watch",
            complainant_email="chew.whistle@protonmail.com",
            complainant_phone=None,
            category="Regulatory Compliance",
            subject="Unfair Capitation Fee Charged for Management Quota Admissions",
            description=(
                "Whistleblower disclosure alleging cash capitation payments of INR 5 Lakhs per seat under "
                "management quota admissions in direct violation of AICTE Approval Process Handbook."
            ),
            status=AICTECaseStatusEnum.UNDER_PROCESS,
            current_unit_id=unit_rb.id,
            assigned_officer_id=bureau_rb.id,
            region="Western",
            priority=GrievancePriorityEnum.HIGH,
            last_action_at=now - timedelta(days=4),
            next_action_required="Standing Appellate Committee forensic financial audit review",
            next_action_due_at=now + timedelta(days=5),
            expected_disposal_at=now + timedelta(days=25),
            created_by_user_id=regulator.id,
            created_at=now - timedelta(days=18)
        )
        db.add(case7)
        db.commit()
        db.refresh(case7)

        act7_1 = CaseAction(
            case_id=case7.id,
            action_type=AICTECaseActionTypeEnum.INTAKE,
            action_title="Whistleblower Intake at Western Regional Office",
            unit_id=unit_row.id,
            performed_by_user_id=regulator.id,
            action_at=now - timedelta(days=18)
        )
        act7_2 = CaseAction(
            case_id=case7.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_INITIATED,
            action_title="Transferred to Regulation Bureau Headquarters",
            action_description="Western Regional Office initiated transfer citing multi-crore capitation gravity.",
            unit_id=unit_row.id,
            performed_by_user_id=regulator.id,
            action_at=now - timedelta(days=14)
        )
        act7_3 = CaseAction(
            case_id=case7.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_ACCEPTED,
            action_title="Transfer Accepted by Bureau Head Dr. S. K. Rastogi",
            action_description="Case admitted under Regulation Bureau special scrutiny wing.",
            unit_id=unit_rb.id,
            performed_by_user_id=bureau_rb.id,
            action_at=now - timedelta(days=12)
        )
        act7_4 = CaseAction(
            case_id=case7.id,
            action_type=AICTECaseActionTypeEnum.COMMITTEE_REVIEW,
            action_title="Forensic Audit Notice Issued",
            action_description="Directed independent chartered accountancy firm to examine trust accounts.",
            unit_id=unit_rb.id,
            performed_by_user_id=bureau_rb.id,
            action_at=now - timedelta(days=4),
            next_action_required="Standing Appellate Committee forensic financial audit review",
            next_action_due_at=now + timedelta(days=5)
        )
        db.add_all([act7_1, act7_2, act7_3, act7_4])

        # Accepted Transfer Record
        transfer2 = AICTECaseTransfer(
            case_id=case7.id,
            from_unit_id=unit_row.id,
            to_unit_id=unit_rb.id,
            initiated_by_user_id=regulator.id,
            proposed_assignee_id=bureau_rb.id,
            transfer_reason="Allegations require national Regulation Bureau punitive powers under AICTE Act.",
            handover_summary="Attached ledger receipts and whistleblower sworn affidavit.",
            prior_case_status="RECEIVED",
            transfer_status=AICTETransferStatusEnum.ACCEPTED,
            initiated_at=now - timedelta(days=14),
            responded_at=now - timedelta(days=12),
            responded_by_user_id=bureau_rb.id,
            response_notes="Accepted for formal hearing before National Standing Appellate Committee.",
            accepted_assignee_id=bureau_rb.id
        )
        db.add(transfer2)
        db.commit()
        created_cases.append(case7.case_reference)

    # 4. Generate Demo Alerts & Notifications for Bureau Staff
    try:
        AICTEAlertService.send_alert(
            db=db,
            recipient_id=bureau_rb.id,
            category="SLA_WARNING",
            severity="URGENT",
            title="Overdue Next Action: Case AICTE-2026-RB-001",
            message="Show-cause compliance report from NIT Delhi was due 2 days ago. Immediate follow-up required.",
            link=f"/aicte/cases/{case1.id if case1 else 1}",
            reference_id=f"SLA_WARN_RB_{case1.id if case1 else 1}",
            requires_acknowledgement=True
        )
        AICTEAlertService.send_alert(
            db=db,
            recipient_id=bureau_rb.id,
            category="TRANSFER_PENDING",
            severity="WARNING",
            title="Incoming Transfer Awaiting Acceptance: Case AICTE-2026-PGRC-002",
            message="PGRC initiated an inter-Bureau transfer to Regulation Bureau regarding certificate withholding.",
            link="/aicte/transfers",
            reference_id=f"TR_PENDING_RB_{case2.id if case2 else 2}",
            requires_acknowledgement=False
        )
        AICTEAlertService.send_alert(
            db=db,
            recipient_id=bureau_ab.id,
            category="OVERLAP_DETECTED",
            severity="WARNING",
            title="Potential Duplicate / Overlap Detected: SIMATS",
            message="Cases AICTE-2026-AB-003 and AICTE-2026-AB-004 have an 89% match score on unapproved intake.",
            link="/aicte/overlaps",
            reference_id=f"OVL_WARN_AB_{case3.id if case3 else 3}",
            requires_acknowledgement=False
        )
        AICTEAlertService.send_alert(
            db=db,
            recipient_id=ro_north.id,
            category="ESCALATION",
            severity="CRITICAL",
            title="Overdue Disposal: Case AICTE-2026-RON-005 (NIT Delhi)",
            message="Case expected disposal date passed 5 days ago. Physical inspection committee report required.",
            link=f"/aicte/cases/{case5.id if case5 else 5}",
            reference_id=f"DISP_WARN_RON_{case5.id if case5 else 5}",
            requires_acknowledgement=True
        )
        db.commit()
    except Exception as e:
        logger.warning("Could not dispatch demo alert notifications: %s", e)

    return created_cases

if __name__ == "__main__":
    db = SessionLocal()
    try:
        results = seed_demo_cases(db)
        print(f"Successfully seeded {len(results)} demo AICTE cases: {results}")
    finally:
        db.close()
