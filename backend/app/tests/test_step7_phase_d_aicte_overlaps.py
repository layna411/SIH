import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from sqlalchemy.orm import Session

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTECaseLinkTypeEnum,
    GrievancePriorityEnum,
)
from app.models.user import User
from app.models.institution import Institution
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.aicte_case import AICTECase
from app.models.aicte_overlap import AICTECaseOverlap, AICTECaseLink
from app.core.security import create_access_token, hash_password

# ---------------------------------------------------------------------------
# Test Fixtures and Helpers
# ---------------------------------------------------------------------------

def auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def superadmin_user(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_d_superadmin@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_d_superadmin@eduresolve.ai",
            hashed_password=hash_password("SuperSecret123!"),
            full_name="Phase D Super Administrator",
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def regular_student(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_d_student@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_d_student@eduresolve.ai",
            hashed_password=hash_password("StudentPass123!"),
            full_name="Phase D Student",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def seeded_units(db_session: Session) -> list:
    from app.services.bootstrap_service import seed_organizational_units
    seed_organizational_units(db_session)
    return db_session.query(OrganizationalUnit).all()

@pytest.fixture
def rb_officer(db_session: Session, seeded_units) -> User:
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    user = db_session.query(User).filter(User.email == "phase_d_rb_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_d_rb_officer@eduresolve.ai",
            hashed_password=hash_password("OfficerPass123!"),
            full_name="RB Scrutiny Officer",
            default_role=UserRoleEnum.COLLEGE_OFFICER,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        membership = BureauMembership(
            user_id=user.id,
            organizational_unit_id=rb_unit.id,
            membership_role="BUREAU_OFFICER",
            designation="Regulation Examiner",
            is_active=True,
            assigned_by_user_id=user.id
        )
        db_session.add(membership)
        db_session.commit()
    return user

@pytest.fixture
def pgrc_officer(db_session: Session, seeded_units) -> User:
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]
    user = db_session.query(User).filter(User.email == "phase_d_pgrc_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_d_pgrc_officer@eduresolve.ai",
            hashed_password=hash_password("PGRCPass123!"),
            full_name="PGRC Redressal Officer",
            default_role=UserRoleEnum.COLLEGE_OFFICER,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        membership = BureauMembership(
            user_id=user.id,
            organizational_unit_id=pgrc_unit.id,
            membership_role="BUREAU_OFFICER",
            designation="Public Grievance Officer",
            is_active=True,
            assigned_by_user_id=user.id
        )
        db_session.add(membership)
        db_session.commit()
    return user

@pytest.fixture
def sample_inst_a(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "PHD-INST-01").first()
    if not inst:
        inst = Institution(
            code="PHD-INST-01",
            name="Delhi Institute of Advanced Robotics",
            aicte_permanent_id="1-PHD-ROBOTICS-99",
            is_aicte_verified=True,
            region="Northern",
            state="Delhi",
            city="New Delhi",
            contact_email="director@diar.delhi.gov.in",
            contact_phone="+91-11-23456789",
            is_active=True,
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

@pytest.fixture
def sample_inst_b(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "PHD-INST-02").first()
    if not inst:
        inst = Institution(
            code="PHD-INST-02",
            name="Mumbai Aerospace Institute",
            aicte_permanent_id="1-PHD-AERO-88",
            is_aicte_verified=True,
            region="Western",
            state="Maharashtra",
            city="Mumbai",
            contact_email="director@mumbai-aero.ac.in",
            contact_phone="+91-22-98765432",
            is_active=True,
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_cross_bureau_duplicate_detection(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    1. Candidate detection flags two cases regarding the same institution in different Bureaus (RB vs PGRC)
       with highly similar allegations as POTENTIAL_DUPLICATE.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    # Create Case 1 in Regulation Bureau
    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "CAPITATION_FEE",
        "subject": "Illegal capitation fee demand during B.Tech admission counseling",
        "description": "The institution demanded mandatory donation in cash of Rs 5 Lakhs for admission.",
        "priority": "HIGH"
    })
    assert res1.status_code == status.HTTP_201_CREATED
    case1_id = res1.json()["id"]

    # Create Case 2 in PGRC with very similar allegations regarding same institution
    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "CAPITATION_FEE",
        "subject": "Capitation fee demand during admission counseling process",
        "description": "Student was asked to pay mandatory donation in cash of Rs 5 Lakhs before admission confirmation.",
        "priority": "HIGH"
    })
    assert res2.status_code == status.HTTP_201_CREATED
    case2_id = res2.json()["id"]

    # Run detection on case2
    res_detect = client.post(f"/api/v1/aicte/overlaps/detect/{case2_id}", headers=headers)
    assert res_detect.status_code == status.HTTP_200_OK
    detected = res_detect.json()
    assert len(detected) >= 1

    overlap = next(o for o in detected if (o["case_id_low"] == min(case1_id, case2_id) and o["case_id_high"] == max(case1_id, case2_id)))
    assert overlap["overlap_type"] == "POTENTIAL_DUPLICATE"
    assert overlap["match_score"] >= 0.50
    assert overlap["match_reasons"]["same_institution"] is True
    assert overlap["match_reasons"]["cross_bureau"] is True
    assert overlap["match_reasons"]["category_match"] is True
    assert overlap["review_status"] == "PENDING"


def test_institution_identity_alone_does_not_create_duplicate(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    2. Two cases for the same institution with entirely different categories and subjects
       must NOT be classified as POTENTIAL_DUPLICATE.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    # Case A: Land boundary issue
    res_a = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "LAND_DEFICIT",
        "subject": "Dispute regarding survey boundary of sports ground",
        "description": "Municipal encroachment on eastern perimeter boundary wall of the campus.",
        "priority": "NORMAL"
    })
    case_a_id = res_a.json()["id"]

    # Case B: Examination hall timetable
    res_b = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "EXAMINATION_CLASH",
        "subject": "Clash in semester exam date sheet between two subjects",
        "description": "Elective subject schedule overlaps with core mechanical mathematics paper.",
        "priority": "NORMAL"
    })
    case_b_id = res_b.json()["id"]

    # Run detection on Case B
    res_detect = client.post(f"/api/v1/aicte/overlaps/detect/{case_b_id}", headers=headers)
    assert res_detect.status_code == status.HTTP_200_OK
    detected = res_detect.json()

    # If an overlap was created, it must be RELATED_CASE or low score, NEVER POTENTIAL_DUPLICATE
    pair_match = [o for o in detected if o["case_id_low"] == min(case_a_id, case_b_id) and o["case_id_high"] == max(case_a_id, case_b_id)]
    if pair_match:
        assert pair_match[0]["overlap_type"] != "POTENTIAL_DUPLICATE"


def test_different_institutions_not_matched_despite_similar_text(client, superadmin_user: User, sample_inst_a: Institution, sample_inst_b: Institution, seeded_units):
    """
    3. Cases at different institutions with identical keywords must NOT be matched.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    # Institution A case
    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "FACULTY_NORMS",
        "subject": "Deficiency in computer engineering professors cadre ratio",
        "description": "Inspection report indicates insufficient senior faculty professors.",
    })
    case1_id = res1.json()["id"]

    # Institution B case with similar wording
    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_b.id,
        "current_unit_id": rb_unit.id,
        "category": "FACULTY_NORMS",
        "subject": "Deficiency in computer engineering professors cadre ratio",
        "description": "Inspection report indicates insufficient senior faculty professors.",
    })
    case2_id = res2.json()["id"]

    # Run detection on Case 2
    res_detect = client.post(f"/api/v1/aicte/overlaps/detect/{case2_id}", headers=headers)
    assert res_detect.status_code == status.HTTP_200_OK
    detected = res_detect.json()

    # Must NOT create an overlap pair between inst A and inst B
    pair_match = [o for o in detected if o["case_id_low"] == min(case1_id, case2_id) and o["case_id_high"] == max(case1_id, case2_id)]
    assert len(pair_match) == 0


def test_repeated_detection_is_idempotent(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    4. Re-running detection repeatedly does NOT create duplicate pair records in the database.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "HOSTEL_FEE",
        "subject": "Unlawful retention of mess caution deposit upon graduation",
        "description": "Graduating batch deposit withheld without cause.",
    })
    case1_id = res1.json()["id"]

    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "HOSTEL_FEE",
        "subject": "Retention of mess caution deposit upon graduation",
        "description": "Hostel caution money refund withheld by college management.",
    })
    case2_id = res2.json()["id"]

    # Run detection cycle 1
    res_det1 = client.post(f"/api/v1/aicte/overlaps/detect/{case2_id}", headers=headers)
    assert res_det1.status_code == status.HTTP_200_OK
    overlaps_1 = res_det1.json()
    assert len(overlaps_1) >= 1
    overlap_id = overlaps_1[0]["id"]

    # Run detection cycle 2
    res_det2 = client.post(f"/api/v1/aicte/overlaps/detect/{case2_id}", headers=headers)
    assert res_det2.status_code == status.HTTP_200_OK
    overlaps_2 = res_det2.json()
    assert any(o["id"] == overlap_id for o in overlaps_2)

    # Check queue count: only 1 record exists for this pair
    res_queue = client.get(f"/api/v1/aicte/overlaps?institution_id={sample_inst_a.id}", headers=headers)
    assert res_queue.status_code == status.HTTP_200_OK
    pair_records = [o for o in res_queue.json()["items"] if o["case_id_low"] == min(case1_id, case2_id) and o["case_id_high"] == max(case1_id, case2_id)]
    assert len(pair_records) == 1


def test_human_review_confirmation_and_case_link_creation(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    5. Reviewing an overlap:
       - Confirming DUPLICATE creates a DUPLICATE_OF case link.
       - NEVER merges or closes either case; both official dockets remain open and independent.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "INFRA_NORM",
        "subject": "Library deficit in journals and electronic databases",
        "description": "Library does not subscribe to IEEE and Springer journals required by norms.",
    })
    case1 = res1.json()

    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "INFRA_NORM",
        "subject": "Deficit in library journals and IEEE database access",
        "description": "Students unable to access IEEE journals required by curriculum.",
    })
    case2 = res2.json()

    # Detect
    res_det = client.post(f"/api/v1/aicte/overlaps/detect/{case2['id']}", headers=headers)
    overlap_id = res_det.json()[0]["id"]

    # Review as CONFIRMED_DUPLICATE
    res_review = client.post(f"/api/v1/aicte/overlaps/{overlap_id}/review", headers=headers, json={
        "action": "CONFIRMED_DUPLICATE",
        "review_notes": "Scrutiny confirms both petitions concern identical deficiency in IEEE subscription."
    })
    assert res_review.status_code == status.HTTP_200_OK
    rev_data = res_review.json()
    assert rev_data["review_status"] == "CONFIRMED_DUPLICATE"
    assert rev_data["review_notes"] == "Scrutiny confirms both petitions concern identical deficiency in IEEE subscription."
    assert rev_data["active_link_type"] == "DUPLICATE_OF"

    # Verify both cases retain their independent status and references
    get_c1 = client.get(f"/api/v1/aicte/cases/{case1['id']}", headers=headers).json()
    get_c2 = client.get(f"/api/v1/aicte/cases/{case2['id']}", headers=headers).json()
    assert get_c1["status"] == "RECEIVED"
    assert get_c2["status"] == "RECEIVED"
    assert get_c1["case_reference"] != get_c2["case_reference"]

    # Verify confirmed relationship appears in case links endpoint
    res_links = client.get(f"/api/v1/aicte/overlaps/cases/{case1['id']}/links", headers=headers)
    assert res_links.status_code == status.HTTP_200_OK
    links = res_links.json()
    assert len(links) == 1
    assert links[0]["link_type"] == "DUPLICATE_OF"
    assert links[0]["linked_case_id"] == case2["id"]


def test_rejection_deactivates_links_and_preserves_case_statuses(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    6. Rejecting a candidate overlap marks it REJECTED, deactivates any existing link,
       and does NOT change the official statuses of either case.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "FIRE_SAFETY",
        "subject": "Fire safety clearance certificate expired for workshop block",
        "description": "Workshop block fire NOC has lapsed.",
    })
    c1_id = res1.json()["id"]

    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "FIRE_SAFETY",
        "subject": "Fire safety extinguisher refill overdue in main building",
        "description": "Extinguishers not refilled.",
    })
    c2_id = res2.json()["id"]

    res_det = client.post(f"/api/v1/aicte/overlaps/detect/{c2_id}", headers=headers)
    overlap_id = res_det.json()[0]["id"]

    # Reject overlap
    res_rej = client.post(f"/api/v1/aicte/overlaps/{overlap_id}/review", headers=headers, json={
        "action": "REJECTED",
        "review_notes": "Distinct buildings and independent statutory compliance issues; separate handling required."
    })
    assert res_rej.status_code == status.HTTP_200_OK
    assert res_rej.json()["review_status"] == "REJECTED"

    # Verify no active links exist
    res_links = client.get(f"/api/v1/aicte/overlaps/cases/{c1_id}/links", headers=headers)
    assert res_links.status_code == status.HTTP_200_OK
    assert len(res_links.json()) == 0

    # Verify case status untouched
    assert client.get(f"/api/v1/aicte/cases/{c1_id}", headers=headers).json()["status"] == "RECEIVED"
    assert client.get(f"/api/v1/aicte/cases/{c2_id}", headers=headers).json()["status"] == "RECEIVED"


def test_redetection_preserves_human_review_decisions(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    7. Re-running detection after a human reviewer has confirmed/rejected a match
       does NOT revert or erase the human decision.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "SALARY_DISPUTE",
        "subject": "Delayed faculty 7th CPC salary disbursement",
        "description": "Faculty salaries in arrears for 3 months.",
    })
    c1_id = res1.json()["id"]

    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "SALARY_DISPUTE",
        "subject": "Delayed faculty salary payment for technical staff",
        "description": "Salaries unpaid for quarter.",
    })
    c2_id = res2.json()["id"]

    res_det = client.post(f"/api/v1/aicte/overlaps/detect/{c2_id}", headers=headers)
    overlap_id = res_det.json()[0]["id"]

    # Confirm RELATED
    client.post(f"/api/v1/aicte/overlaps/{overlap_id}/review", headers=headers, json={
        "action": "CONFIRMED_RELATED",
        "review_notes": "Related campus financial distress; coordinate between RB and PGRC."
    })

    # Trigger re-detection
    res_redet = client.post(f"/api/v1/aicte/overlaps/detect/{c2_id}", headers=headers)
    assert res_redet.status_code == status.HTTP_200_OK

    # Verify review_status remained CONFIRMED_RELATED
    res_get = client.get(f"/api/v1/aicte/overlaps/{overlap_id}", headers=headers)
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["review_status"] == "CONFIRMED_RELATED"
    assert "coordinate between RB and PGRC" in res_get.json()["review_notes"]


def test_cross_bureau_confidentiality_masking(client, superadmin_user: User, rb_officer: User, pgrc_officer: User, sample_inst_a: Institution, seeded_units):
    """
    8. A Bureau officer reviewing an overlap involving another Bureau receives
       shielded metadata: confidential description and complainant details are masked.
    """
    admin_headers = auth_headers(superadmin_user)
    rb_headers = auth_headers(rb_officer)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    # Create RB case with confidential whistleblower description
    res_rb = client.post("/api/v1/aicte/cases", headers=admin_headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "GOVERNANCE_FRAUD",
        "subject": "Fictitious student enrollment fraud for grant claims",
        "description": "Whistleblower report: 150 ghost students enrolled to fraudulently draw AICTE scholarship funds.",
        "complainant_name": "Dr. Confidential Whistleblower",
        "complainant_email": "whistleblower@secure.org",
        "complainant_phone": "+91-9999988888"
    })
    rb_case_id = res_rb.json()["id"]

    # Create PGRC case
    res_pgrc = client.post("/api/v1/aicte/cases", headers=admin_headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": pgrc_unit.id,
        "category": "GOVERNANCE_FRAUD",
        "subject": "Scholarship grant delay for computer science students",
        "description": "Scholarship disbursement stalled by finance office.",
        "complainant_name": "Rohan Kumar",
        "complainant_email": "rohan@student.org"
    })
    pgrc_case_id = res_pgrc.json()["id"]

    res_det = client.post(f"/api/v1/aicte/overlaps/detect/{pgrc_case_id}", headers=admin_headers)
    overlap_id = res_det.json()[0]["id"]

    # RB Officer views overlap
    res_rb_view = client.get(f"/api/v1/aicte/overlaps/{overlap_id}", headers=rb_headers)
    assert res_rb_view.status_code == status.HTTP_200_OK
    data = res_rb_view.json()

    # Low case is RB, High case is PGRC
    low = data["case_low"] if data["case_id_low"] == rb_case_id else data["case_high"]
    foreign = data["case_high"] if data["case_id_low"] == rb_case_id else data["case_low"]

    # RB officer has full access to their own case
    assert low["has_full_access"] is True
    assert "150 ghost students" in low["description"]
    assert low["complainant_name"] == "Dr. Confidential Whistleblower"

    # RB officer does NOT have access to foreign PGRC case description
    assert foreign["has_full_access"] is False
    assert "[CONFIDENTIAL" in foreign["description"]
    assert foreign["complainant_name"] == "[PROTECTED]"
    assert foreign["complainant_email"] is None


def test_unauthorized_user_cannot_access_overlap_endpoints(client, regular_student: User, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    9. Students and unprivileged users are forbidden from viewing or reviewing overlaps.
    """
    student_headers = auth_headers(regular_student)
    admin_headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    res_case = client.post("/api/v1/aicte/cases", headers=admin_headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "TEST_CASE",
        "subject": "Testing access controls",
        "description": "Checking student restrictions.",
    })
    case_id = res_case.json()["id"]

    # Student cannot run detection -> 403
    res1 = client.post(f"/api/v1/aicte/overlaps/detect/{case_id}", headers=student_headers)
    assert res1.status_code == status.HTTP_403_FORBIDDEN

    # Student cannot list queue -> 403
    res2 = client.get("/api/v1/aicte/overlaps", headers=student_headers)
    assert res2.status_code == status.HTTP_403_FORBIDDEN


def test_manual_case_linking_workflow(client, superadmin_user: User, sample_inst_a: Institution, seeded_units):
    """
    10. Manual case link creation enforces canonical order, prevents self-linking, and supports deactivation.
    """
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    res1 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "INQUIRY_A",
        "subject": "Inquiry A regarding laboratory safety",
        "description": "Chemical storage compliance.",
    })
    c1_id = res1.json()["id"]

    res2 = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_inst_a.id,
        "current_unit_id": rb_unit.id,
        "category": "INQUIRY_B",
        "subject": "Inquiry B regarding laboratory ventilation",
        "description": "Fume hood maintenance audit.",
    })
    c2_id = res2.json()["id"]

    # Prevent self-linking -> 400 Bad Request
    res_self = client.post(f"/api/v1/aicte/overlaps/cases/{c1_id}/links", headers=headers, json={
        "target_case_id": c1_id,
        "link_type": "RELATED_TO"
    })
    assert res_self.status_code == status.HTTP_400_BAD_REQUEST

    # Successfully create manual link
    res_link = client.post(f"/api/v1/aicte/overlaps/cases/{c1_id}/links", headers=headers, json={
        "target_case_id": c2_id,
        "link_type": "RELATED_TO",
        "notes": "Manual administrative link between lab safety and ventilation inquiries."
    })
    assert res_link.status_code == status.HTTP_201_CREATED
    link_data = res_link.json()
    assert link_data["link_type"] == "RELATED_TO"
    assert link_data["is_active"] is True
    link_id = link_data["id"]

    # Deactivate link via PATCH
    res_patch = client.patch(f"/api/v1/aicte/overlaps/links/{link_id}", headers=headers, json={
        "is_active": False,
        "notes": "Relationship severed after administrative review."
    })
    assert res_patch.status_code == status.HTTP_200_OK
    assert res_patch.json()["is_active"] is False

    # Check case links list -> active only, so should be empty
    res_links_active = client.get(f"/api/v1/aicte/overlaps/cases/{c1_id}/links", headers=headers)
    assert len(res_links_active.json()) == 0
