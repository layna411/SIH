import pytest
from datetime import datetime, timezone
from fastapi import status
from sqlalchemy.orm import Session

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseSourceTypeEnum,
    AICTEComplainantTypeEnum,
    AICTECaseActionTypeEnum,
    GrievancePriorityEnum,
    GrievanceStatusEnum,
)
from app.models.user import User
from app.models.institution import Institution
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.category import GrievanceCategory
from app.models.grievance import Grievance
from app.models.aicte_case import AICTECase, CaseAction
from app.services.bootstrap_service import seed_organizational_units
from app.core.security import hash_password, create_access_token


def auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seeded_units(db_session: Session):
    return seed_organizational_units(db_session)


@pytest.fixture
def superadmin_user(db_session: Session) -> User:
    admin = db_session.query(User).filter(User.email == "superadmin.phasec@eduresolve.ai").first()
    if not admin:
        admin = User(
            email="superadmin.phasec@eduresolve.ai",
            hashed_password=hash_password("SuperAdmin@Pass123"),
            full_name="Super Administrator Phase C",
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    return admin


@pytest.fixture
def bureau_officer_user(db_session: Session, seeded_units) -> User:
    officer = db_session.query(User).filter(User.email == "bureau.officer.rb@aicte.gov.in").first()
    if not officer:
        officer = User(
            email="bureau.officer.rb@aicte.gov.in",
            hashed_password=hash_password("BureauOfficer@123"),
            full_name="RB Scrutiny Officer",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(officer)
        db_session.commit()
        db_session.refresh(officer)

    # Assign to Regulation Bureau (RB)
    rb_unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB").first()
    assert rb_unit is not None
    mem = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == officer.id,
        BureauMembership.organizational_unit_id == rb_unit.id
    ).first()
    if not mem:
        mem = BureauMembership(
            user_id=officer.id,
            organizational_unit_id=rb_unit.id,
            membership_role="BUREAU_HEAD",
            is_active=True
        )
        db_session.add(mem)
        db_session.commit()
    return officer


@pytest.fixture
def other_bureau_officer(db_session: Session, seeded_units) -> User:
    officer = db_session.query(User).filter(User.email == "bureau.officer.pgrc@aicte.gov.in").first()
    if not officer:
        officer = User(
            email="bureau.officer.pgrc@aicte.gov.in",
            hashed_password=hash_password("BureauPGRC@123"),
            full_name="PGRC Handling Officer",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(officer)
        db_session.commit()
        db_session.refresh(officer)

    pgrc_unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC").first()
    assert pgrc_unit is not None
    mem = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == officer.id,
        BureauMembership.organizational_unit_id == pgrc_unit.id
    ).first()
    if not mem:
        mem = BureauMembership(
            user_id=officer.id,
            organizational_unit_id=pgrc_unit.id,
            membership_role="BUREAU_OFFICER",
            is_active=True
        )
        db_session.add(mem)
        db_session.commit()
    return officer


@pytest.fixture
def regular_student_user(db_session: Session) -> User:
    student = db_session.query(User).filter(User.email == "student.phasec@college.edu.in").first()
    if not student:
        student = User(
            email="student.phasec@college.edu.in",
            hashed_password=hash_password("StudentPass@123"),
            full_name="Regular Student Phase C",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
    return student


@pytest.fixture
def sample_institution(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "PHASEC-INST-01").first()
    if not inst:
        inst = Institution(
            code="PHASEC-INST-01",
            name="Delhi Institute of Advanced Robotics",
            state="Delhi",
            city="New Delhi",
            contact_email="grievances@diar.ac.in",
            aicte_permanent_id="1-9988776655",
            region="Northern",
            is_aicte_verified=True
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst


@pytest.fixture
def sample_grievance(db_session: Session, sample_institution: Institution, regular_student_user: User) -> Grievance:
    category = db_session.query(GrievanceCategory).filter(GrievanceCategory.code == "ACAD").first()
    if not category:
        category = GrievanceCategory(
            code="ACAD",
            name="Academic & Teaching Affairs",
            description="Curriculum, evaluations, lecture schedules",
            default_sla_days=7
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

    grv = db_session.query(Grievance).filter(Grievance.reference_number == "GRV-PHASEC-REF-01").first()
    if not grv:
        grv = Grievance(
            reference_number="GRV-PHASEC-REF-01",
            student_id=regular_student_user.id,
            institution_id=sample_institution.id,
            category_id=category.id,
            title="Non-refund of caution deposit upon withdrawal",
            description="Institution refused refund of laboratory caution deposit contrary to statutory guidelines.",
            status=GrievanceStatusEnum.SUBMITTED,
            priority=GrievancePriorityEnum.HIGH,
        )
        db_session.add(grv)
        db_session.commit()
        db_session.refresh(grv)
    return grv


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_authorized_direct_case_creation(client, superadmin_user: User, sample_institution: Institution, seeded_units):
    """SuperAdmin can create a direct AICTE case with automatic reference generation and intake action."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    payload = {
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "APPROVAL_VIOLATION",
        "subject": "Exceeding sanctioned intake quota in computer engineering",
        "description": "Inspection report indicates 60 additional admissions beyond approved AICTE sanction.",
        "complainant_type": "PUBLIC_AUTHORITY",
        "priority": "HIGH",
        "official_reference_number": "DEL-RO-2026-901"
    }

    res = client.post("/api/v1/aicte/cases", headers=headers, json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["case_reference"].startswith("AICTE-")
    assert data["institution_id"] == sample_institution.id
    assert data["current_unit_code"] == "RB"
    assert data["status"] == "RECEIVED"
    assert data["official_reference_number"] == "DEL-RO-2026-901"
    assert data["source_type"] == "DIRECT"
    assert data["source_grievance_id"] is None

    # Verify intake action in history
    case_id = data["id"]
    res_hist = client.get(f"/api/v1/aicte/cases/{case_id}/history", headers=headers)
    assert res_hist.status_code == status.HTTP_200_OK
    actions = res_hist.json()
    assert len(actions) == 1
    assert actions[0]["action_type"] == "INTAKE"


def test_unauthorized_user_cannot_create_case(client, regular_student_user: User, sample_institution: Institution, seeded_units):
    """Students and non-bureau users are forbidden from creating official AICTE cases."""
    headers = auth_headers(regular_student_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    payload = {
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "CAPITATION_FEE",
        "subject": "Illegal capitation fee demand",
        "description": "College demanded donation during admission process."
    }

    res = client.post("/api/v1/aicte/cases", headers=headers, json=payload)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_case_creation_validates_institution(client, superadmin_user: User, seeded_units):
    """Non-existent institution ID returns 404."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    payload = {
        "institution_id": 999999,
        "current_unit_id": rb_unit.id,
        "category": "APPROVAL_VIOLATION",
        "subject": "Invalid institution test",
        "description": "Description test."
    }

    res = client.post("/api/v1/aicte/cases", headers=headers, json=payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_bureau_officer_assignment_validation(client, superadmin_user: User, bureau_officer_user: User, sample_institution: Institution, seeded_units):
    """Assigning officer to case validates officer's membership in the handling unit."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    # Create case in RB
    res_case = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "FACULTY_IRREGULARITY",
        "subject": "Inadequate faculty cadre ratio in mechanical department",
        "description": "Faculty shortage reported."
    })
    case_id = res_case.json()["id"]

    # Assign bureau_officer_user (who has RB membership) -> should succeed
    res_assign = client.post(f"/api/v1/aicte/cases/{case_id}/assign", headers=headers, json={
        "assigned_officer_id": bureau_officer_user.id,
        "reason": "Designated scrutiny officer for northern mechanical colleges."
    })
    assert res_assign.status_code == status.HTTP_200_OK
    assert res_assign.json()["assigned_officer_id"] == bureau_officer_user.id

    # Try assigning regular student without bureau membership -> should be rejected with 400
    res_bad = client.post(f"/api/v1/aicte/cases/{case_id}/assign", headers=headers, json={
        "assigned_officer_id": 1  # Student ID
    })
    assert res_bad.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


def test_case_lifecycle_state_machine(client, superadmin_user: User, sample_institution: Institution, seeded_units):
    """Case lifecycle transitions must be validated server-side."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    # 1. Create case (initial status: RECEIVED)
    res_c = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "ACADEMIC_MALPRACTICE",
        "subject": "Fictitious attendance in exam hall",
        "description": "Internal test malpractice."
    })
    case_id = res_c.json()["id"]
    assert res_c.json()["status"] == "RECEIVED"

    # 2. Transition RECEIVED -> UNDER_PROCESS (valid)
    res_action1 = client.post(f"/api/v1/aicte/cases/{case_id}/actions", headers=headers, json={
        "action_type": "INITIAL_SCRUTINY",
        "action_title": "Preliminary Scrutiny Commenced",
        "new_status": "UNDER_PROCESS",
        "remarks": "Documents under examination."
    })
    assert res_action1.status_code == status.HTTP_201_CREATED
    assert res_action1.json()["new_status"] == "UNDER_PROCESS"

    # Verify case status updated
    res_get = client.get(f"/api/v1/aicte/cases/{case_id}", headers=headers)
    assert res_get.json()["status"] == "UNDER_PROCESS"

    # 3. Transition UNDER_PROCESS -> DISPOSED (valid)
    res_action2 = client.post(f"/api/v1/aicte/cases/{case_id}/actions", headers=headers, json={
        "action_type": "DISPOSAL_ORDER",
        "action_title": "Case Disposed with Penalty Order",
        "new_status": "DISPOSED",
        "remarks": "Penalty imposed."
    })
    assert res_action2.status_code == status.HTTP_201_CREATED

    res_disposed = client.get(f"/api/v1/aicte/cases/{case_id}", headers=headers)
    assert res_disposed.json()["status"] == "DISPOSED"
    assert res_disposed.json()["disposed_at"] is not None

    # 4. Attempt invalid transition from DISPOSED -> UNDER_PROCESS (not permitted without REOPENED)
    res_bad = client.post(f"/api/v1/aicte/cases/{case_id}/actions", headers=headers, json={
        "action_type": "STATUS_UPDATE",
        "action_title": "Attempt invalid jump",
        "new_status": "UNDER_PROCESS"
    })
    assert res_bad.status_code == status.HTTP_400_BAD_REQUEST


def test_campus_grievance_referral_workflow(client, superadmin_user: User, sample_grievance: Grievance, seeded_units, db_session: Session):
    """Campus grievance can be referred to AICTE, creating bridged aicte_case without duplicating or mutating original grievance."""
    headers = auth_headers(superadmin_user)
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    orig_grv_title = sample_grievance.title
    orig_grv_status = sample_grievance.status

    payload = {
        "source_grievance_id": sample_grievance.id,
        "destination_unit_id": pgrc_unit.id,
        "referral_reason": "Statutory refund violation requiring central AICTE Public Grievance Cell intervention.",
        "complainant_type": "STUDENT",
        "official_reference_number": "PGRC-REF-CAMPUS-001"
    }

    res = client.post("/api/v1/aicte/cases/refer-grievance", headers=headers, json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["source_type"] == "CAMPUS_REFERRAL"
    assert data["source_grievance_id"] == sample_grievance.id
    assert data["source_grievance_reference"] == sample_grievance.reference_number
    assert data["current_unit_code"] == "PGRC"
    assert "Statutory refund violation" in data["description"]

    # Verify original grievance was not corrupted or altered
    db_session.refresh(sample_grievance)
    assert sample_grievance.title == orig_grv_title
    assert sample_grievance.status == orig_grv_status

    # Verify duplicate referral of the same grievance is rejected
    res_dup = client.post("/api/v1/aicte/cases/refer-grievance", headers=headers, json=payload)
    assert res_dup.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been referred" in res_dup.json()["detail"]


def test_cross_bureau_isolation(client, bureau_officer_user: User, other_bureau_officer: User, sample_institution: Institution, seeded_units):
    """Officers in Bureau A cannot view or modify cases in Bureau B."""
    rb_headers = auth_headers(bureau_officer_user)      # Officer in RB
    pgrc_headers = auth_headers(other_bureau_officer)    # Officer in PGRC

    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    # RB officer creates case in RB
    res_rb_case = client.post("/api/v1/aicte/cases", headers=rb_headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "REGULATION_AUDIT",
        "subject": "Confidential governance review",
        "description": "Sensitive inquiry."
    })
    assert res_rb_case.status_code == status.HTTP_201_CREATED
    rb_case_id = res_rb_case.json()["id"]

    # PGRC officer attempts to view RB case -> 403 Forbidden
    res_forbidden_get = client.get(f"/api/v1/aicte/cases/{rb_case_id}", headers=pgrc_headers)
    assert res_forbidden_get.status_code == status.HTTP_403_FORBIDDEN

    # PGRC officer attempts to add action to RB case -> 403 Forbidden
    res_forbidden_action = client.post(f"/api/v1/aicte/cases/{rb_case_id}/actions", headers=pgrc_headers, json={
        "action_type": "NOTE_RECORDED",
        "action_title": "Unauthorized note",
        "remarks": "Should be blocked"
    })
    assert res_forbidden_action.status_code == status.HTTP_403_FORBIDDEN


def test_consolidated_institution_profile(client, superadmin_user: User, sample_institution: Institution, seeded_units):
    """Consolidated institution profile returns multi-bureau metrics, aliases, and recent cases."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]
    pgrc_unit = [u for u in seeded_units if u.code == "PGRC"][0]

    # Create cases across two bureaus for this institution
    client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "INFRASTRUCTURE_DEFICIT",
        "subject": "Library seating deficiency",
        "description": "Audit deficit."
    })
    client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": pgrc_unit.id,
        "category": "STUDENT_GRIEVANCE",
        "subject": "Hostel hygiene concern",
        "description": "Health and hygiene issue."
    })

    # Add alias
    client.post(f"/api/v1/institutions/{sample_institution.id}/aliases", headers=headers, json={
        "alias_name": "DIAR Robotics",
        "source": "COMMONLY_KNOWN_AS"
    })

    # Retrieve consolidated profile
    res = client.get(f"/api/v1/aicte/institutions/{sample_institution.id}/consolidated-history", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["institution_id"] == sample_institution.id
    assert data["aicte_permanent_id"] == sample_institution.aicte_permanent_id
    assert "DIAR Robotics" in data["aliases"]
    assert data["total_cases"] >= 2
    assert "RB" in data["unit_counts"]
    assert "PGRC" in data["unit_counts"]
    assert len(data["recent_cases"]) >= 2


def test_cases_search_and_pagination(client, superadmin_user: User, sample_institution: Institution, seeded_units):
    """Case directory supports text search, unit filtering, and pagination."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    # Create distinct cases for search testing
    res_a = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "FACULTY_NORMS",
        "subject": "Faculty cadre ratio non-compliance in mechanical",
        "description": "Cadre ratio deficient in mechanical engineering department."
    })
    assert res_a.status_code == status.HTTP_201_CREATED

    res_b = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "LAB_EQUIPMENT",
        "subject": "Deficient wind tunnel laboratory equipment",
        "description": "Aerospace wind tunnel facility not commissioned."
    })
    assert res_b.status_code == status.HTTP_201_CREATED

    # Search for mechanical
    res_search = client.get("/api/v1/aicte/cases?search=mechanical", headers=headers)
    assert res_search.status_code == status.HTTP_200_OK
    search_data = res_search.json()
    assert any("mechanical" in item["subject"].lower() for item in search_data["cases"])
    assert not any("wind tunnel" in item["subject"].lower() for item in search_data["cases"])

    # Test pagination
    res_paged = client.get("/api/v1/aicte/cases?page=1&page_size=1", headers=headers)
    assert res_paged.status_code == status.HTTP_200_OK
    paged_data = res_paged.json()
    assert len(paged_data["cases"]) == 1
    assert paged_data["total"] >= 2
    assert paged_data["page_size"] == 1


def test_case_metadata_update_and_invalid_transition(client, superadmin_user: User, sample_institution: Institution, seeded_units):
    """Permitted metadata can be patched and invalid lifecycle transitions are rejected."""
    headers = auth_headers(superadmin_user)
    rb_unit = [u for u in seeded_units if u.code == "RB"][0]

    res = client.post("/api/v1/aicte/cases", headers=headers, json={
        "institution_id": sample_institution.id,
        "current_unit_id": rb_unit.id,
        "category": "LAND_DEFICIT",
        "subject": "Original Title: Land document title dispute",
        "description": "Dispute on survey numbers for campus demarcation."
    })
    assert res.status_code == status.HTTP_201_CREATED
    case_id = res.json()["id"]

    # PATCH metadata
    res_patch = client.patch(f"/api/v1/aicte/cases/{case_id}", headers=headers, json={
        "subject": "Updated Title: Land document title dispute resolved by civil court",
        "next_action_required": "Scrutinize title deed copy",
        "priority": "HIGH"
    })
    assert res_patch.status_code == status.HTTP_200_OK
    assert "civil court" in res_patch.json()["subject"]
    assert res_patch.json()["next_action_required"] == "Scrutinize title deed copy"
    assert res_patch.json()["priority"] == "HIGH"

    # Attempt illegal status transition directly from RECEIVED to DISPOSED -> 400 Bad Request
    res_illegal_action = client.post(f"/api/v1/aicte/cases/{case_id}/actions", headers=headers, json={
        "action_type": "DISPOSAL_ORDER",
        "action_title": "Direct disposal attempt without review",
        "new_status": "DISPOSED"
    })
    assert res_illegal_action.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid AICTE case lifecycle transition" in res_illegal_action.json()["detail"]


