import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRoleEnum, GrievancePriorityEnum, AICTECaseStatusEnum, GrievanceStatusEnum
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.grievance import Grievance, GrievanceCategory
from app.models.aicte_case import AICTECase, CaseAction
from app.core.security import hash_password, create_access_token
from app.services.bootstrap_service import seed_organizational_units

@pytest.fixture
def seeded_units(db_session: Session):
    return seed_organizational_units(db_session)

@pytest.fixture
def super_admin(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "superadmin.phase_i@aicte.gov.in").first()
    if not user:
        user = User(
            email="superadmin.phase_i@aicte.gov.in",
            hashed_password=hash_password("SuperAdmin@123"),
            full_name="Super Administrator Phase I",
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def institution_a(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "INST_A_PI").first()
    if not inst:
        inst = Institution(
            name="Alpha Engineering Institute Phase I",
            code="INST_A_PI",
            aicte_permanent_id="1-PHASE-I-ALPHA",
            state="Maharashtra",
            region="Western",
            contact_email="contact@inst-a.edu",
            is_active=True,
            is_verified=True
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

@pytest.fixture
def institution_b(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "INST_B_PI").first()
    if not inst:
        inst = Institution(
            name="Beta Institute of Technology Phase I",
            code="INST_B_PI",
            aicte_permanent_id="1-PHASE-I-BETA",
            state="Karnataka",
            region="Southern",
            contact_email="contact@inst-b.edu",
            is_active=True,
            is_verified=True
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

@pytest.fixture
def bureau_officer_rb(db_session: Session, seeded_units) -> User:
    user = db_session.query(User).filter(User.email == "officer.rb.phase_i@aicte.gov.in").first()
    if not user:
        user = User(
            email="officer.rb.phase_i@aicte.gov.in",
            hashed_password=hash_password("BureauPass@123"),
            full_name="RB Bureau Officer Phase I",
            default_role=UserRoleEnum.COLLEGE_OFFICER,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    rb_unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB").first()
    mem = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == user.id,
        BureauMembership.organizational_unit_id == rb_unit.id
    ).first()
    if not mem:
        mem = BureauMembership(
            user_id=user.id,
            organizational_unit_id=rb_unit.id,
            membership_role="BUREAU_OFFICER",
            is_active=True
        )
        db_session.add(mem)
        db_session.commit()
    return user

@pytest.fixture
def head_user(db_session: Session, institution_a) -> User:
    user = db_session.query(User).filter(User.email == "head.phase_i@inst-a.edu").first()
    if not user:
        user = User(
            email="head.phase_i@inst-a.edu",
            hashed_password=hash_password("HeadPass@123"),
            full_name="Institution Head Phase I",
            default_role=UserRoleEnum.INSTITUTION_HEAD,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    mem = db_session.query(InstitutionMembership).filter(
        InstitutionMembership.user_id == user.id,
        InstitutionMembership.institution_id == institution_a.id
    ).first()
    if not mem:
        mem = InstitutionMembership(
            user_id=user.id,
            institution_id=institution_a.id,
            role=UserRoleEnum.INSTITUTION_HEAD,
            department="Executive Office",
            is_active=True
        )
        db_session.add(mem)
        db_session.commit()
    return user

@pytest.fixture
def officer_inst_a(db_session: Session, institution_a) -> User:
    user = db_session.query(User).filter(User.email == "officer.a.phase_i@inst-a.edu").first()
    if not user:
        user = User(
            email="officer.a.phase_i@inst-a.edu",
            hashed_password=hash_password("OfficerPass@123"),
            full_name="College Officer Inst A Phase I",
            default_role=UserRoleEnum.COLLEGE_OFFICER,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    mem = db_session.query(InstitutionMembership).filter(
        InstitutionMembership.user_id == user.id,
        InstitutionMembership.institution_id == institution_a.id
    ).first()
    if not mem:
        mem = InstitutionMembership(
            user_id=user.id,
            institution_id=institution_a.id,
            role=UserRoleEnum.COLLEGE_OFFICER,
            department="Student Affairs",
            is_active=True
        )
        db_session.add(mem)
        db_session.commit()
    return user

@pytest.fixture
def student_user_1(db_session: Session, institution_a) -> User:
    user = db_session.query(User).filter(User.email == "student1.phase_i@inst-a.edu").first()
    if not user:
        user = User(
            email="student1.phase_i@inst-a.edu",
            hashed_password=hash_password("StudentPass@123"),
            full_name="Student One Phase I",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    mem = db_session.query(InstitutionMembership).filter(
        InstitutionMembership.user_id == user.id,
        InstitutionMembership.institution_id == institution_a.id
    ).first()
    if not mem:
        mem = InstitutionMembership(
            user_id=user.id,
            institution_id=institution_a.id,
            role=UserRoleEnum.STUDENT,
            department="Computer Science",
            is_active=True
        )
        db_session.add(mem)
        db_session.commit()
    return user

@pytest.fixture
def student_user_2(db_session: Session, institution_b) -> User:
    user = db_session.query(User).filter(User.email == "student2.phase_i@inst-b.edu").first()
    if not user:
        user = User(
            email="student2.phase_i@inst-b.edu",
            hashed_password=hash_password("StudentPass@123"),
            full_name="Student Two Phase I",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

def _auth_header(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.default_role.value, "email": user.email}
    )
    return {"Authorization": f"Bearer {token}"}

# ==============================================================================
# TESTS
# ==============================================================================

def test_auth_me_serializes_bureau_memberships(client: TestClient, bureau_officer_rb: User):
    """Verify /auth/me returns active bureau_memberships with unit codes and roles."""
    headers = _auth_header(bureau_officer_rb)
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "bureau_memberships" in data
    assert len(data["bureau_memberships"]) >= 1
    bm = data["bureau_memberships"][0]
    assert bm["unit_code"] == "RB"
    assert bm["membership_role"] == "BUREAU_OFFICER"
    assert bm["is_active"] is True

def test_bureau_officer_can_access_authorized_case(
    client: TestClient, 
    db_session: Session, 
    bureau_officer_rb: User, 
    institution_a: Institution, 
    seeded_units
):
    """Bureau officer can list cases and inspect case detail belonging to their unit."""
    rb_unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB").first()
    case = AICTECase(
        case_reference="AICTE-PI-TEST-001",
        institution_id=institution_a.id,
        current_unit_id=rb_unit.id,
        subject="Regulatory Fee Cap Violation",
        description="Detailed description of regulatory fee cap violation for Phase I test.",
        category="FEE_REFUND",
        status=AICTECaseStatusEnum.PENDING_REVIEW,
        priority=GrievancePriorityEnum.HIGH,
        created_by_user_id=bureau_officer_rb.id,
        received_at=datetime.now(timezone.utc)
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    headers = _auth_header(bureau_officer_rb)
    # 1. List cases
    res = client.get("/api/v1/aicte/cases", headers=headers)
    assert res.status_code == 200
    cases = res.json()["cases"]
    assert any(c["case_reference"] == "AICTE-PI-TEST-001" for c in cases)

    # 2. Get case detail
    res_det = client.get(f"/api/v1/aicte/cases/{case.id}", headers=headers)
    assert res_det.status_code == 200
    assert res_det.json()["case_reference"] == "AICTE-PI-TEST-001"

    # 3. Get case history
    res_hist = client.get(f"/api/v1/aicte/cases/{case.id}/history", headers=headers)
    assert res_hist.status_code == 200

def test_bureau_officer_denied_access_to_unrelated_bureau_case(
    client: TestClient,
    db_session: Session,
    bureau_officer_rb: User,
    institution_a: Institution,
    seeded_units
):
    """Bureau officer in RB cannot access case belonging exclusively to Approval Bureau (AB)."""
    ab_unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "AB").first()
    case = AICTECase(
        case_reference="AICTE-PI-TEST-AB-001",
        institution_id=institution_a.id,
        current_unit_id=ab_unit.id,
        subject="Approval Norms Discrepancy",
        description="Detailed description of approval norms discrepancy for Phase I test.",
        category="FACULTY_NORMS",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        priority=GrievancePriorityEnum.NORMAL,
        created_by_user_id=bureau_officer_rb.id,
        received_at=datetime.now(timezone.utc)
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    headers = _auth_header(bureau_officer_rb)
    # Attempt detail
    res = client.get(f"/api/v1/aicte/cases/{case.id}", headers=headers)
    assert res.status_code == 403

def test_unauthorized_student_denied_aicte_cases(
    client: TestClient,
    student_user_1: User
):
    """Students cannot access backend AICTE case management endpoints."""
    headers = _auth_header(student_user_1)
    res = client.get("/api/v1/aicte/cases", headers=headers)
    assert res.status_code == 403

def test_unauthorized_college_officer_denied_aicte_cases_without_membership(
    client: TestClient,
    officer_inst_a: User
):
    """Campus officer without Bureau membership cannot access AICTE case directory."""
    headers = _auth_header(officer_inst_a)
    res = client.get("/api/v1/aicte/cases", headers=headers)
    assert res.status_code == 403

def test_institution_head_can_refer_grievance_to_aicte(
    client: TestClient,
    db_session: Session,
    head_user: User,
    student_user_1: User,
    institution_a: Institution,
    seeded_units
):
    """Institution Head can refer an escalated grievance of their campus to AICTE."""
    cat = db_session.query(GrievanceCategory).filter(GrievanceCategory.code == "FEE_PI").first()
    if not cat:
        cat = GrievanceCategory(
            name="Fee Grievances PI",
            code="FEE_PI",
            default_sla_days=2,
            is_active=True
        )
        db_session.add(cat)
        db_session.commit()

    grievance = Grievance(
        reference_number="GRV-PI-HEAD-REF",
        institution_id=institution_a.id,
        category_id=cat.id,
        student_id=student_user_1.id,
        title="Unlawful Security Deposit Retention",
        description="Campus withholding security deposit beyond regulatory permissible period.",
        status=GrievanceStatusEnum.ESCALATED,
        priority=GrievancePriorityEnum.HIGH,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(grievance)
    db_session.commit()
    db_session.refresh(grievance)

    pgrc_unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC").first()
    headers = _auth_header(head_user)
    payload = {
        "source_grievance_id": grievance.id,
        "destination_unit_id": pgrc_unit.id,
        "referral_reason": "Escalated campus grievance requiring central PGRC intervention and oversight.",
        "complainant_type": "STUDENT",
        "priority": "HIGH"
    }
    res = client.post("/api/v1/aicte/cases/refer-grievance", json=payload, headers=headers)
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["source_grievance_id"] == grievance.id
    assert data["current_unit_code"] == "PGRC"

def test_institutional_isolation_college_officer(
    client: TestClient,
    db_session: Session,
    officer_inst_a: User,
    student_user_2: User,
    institution_b: Institution
):
    """College Officer of Institution A cannot access grievance of Institution B."""
    cat_b = db_session.query(GrievanceCategory).filter(GrievanceCategory.code == "HOSTEL_B_PI").first()
    if not cat_b:
        cat_b = GrievanceCategory(
            name="Hostel B PI",
            code="HOSTEL_B_PI",
            default_sla_days=3,
            is_active=True
        )
        db_session.add(cat_b)
        db_session.commit()

    grv_b = Grievance(
        reference_number="GRV-PI-INST-B-001",
        institution_id=institution_b.id,
        category_id=cat_b.id,
        student_id=student_user_2.id,
        title="Campus B Private Maintenance Issue",
        description="Private grievance belonging solely to Beta Institute.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.NORMAL,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(grv_b)
    db_session.commit()
    db_session.refresh(grv_b)

    headers = _auth_header(officer_inst_a)
    res = client.get(f"/api/v1/grievances/{grv_b.id}", headers=headers)
    assert res.status_code == 403

def test_student_isolation(
    client: TestClient,
    db_session: Session,
    student_user_1: User,
    student_user_2: User,
    institution_b: Institution
):
    """Student 1 cannot access Student 2's grievance."""
    cat = db_session.query(GrievanceCategory).filter(GrievanceCategory.code == "ACAD_PI").first()
    if not cat:
        cat = GrievanceCategory(
            name="Academics PI",
            code="ACAD_PI",
            default_sla_days=2,
            is_active=True
        )
        db_session.add(cat)
        db_session.commit()

    grv = Grievance(
        reference_number="GRV-PI-STUDENT-2",
        institution_id=institution_b.id,
        category_id=cat.id,
        student_id=student_user_2.id,
        title="Student 2 Personal Grievance",
        description="Strictly confidential student grievance.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.NORMAL,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(grv)
    db_session.commit()
    db_session.refresh(grv)

    headers = _auth_header(student_user_1)
    res = client.get(f"/api/v1/grievances/{grv.id}", headers=headers)
    assert res.status_code == 403

def test_super_admin_has_full_nationwide_oversight(
    client: TestClient,
    super_admin: User
):
    """Super Admin can access system admin, organizational units, users, and AICTE cases."""
    headers = _auth_header(super_admin)

    # 1. Units list
    res_units = client.get("/api/v1/organizational-units", headers=headers)
    assert res_units.status_code == 200

    # 2. Users list
    res_users = client.get("/api/v1/users", headers=headers)
    assert res_users.status_code == 200

    # 3. AICTE cases
    res_cases = client.get("/api/v1/aicte/cases", headers=headers)
    assert res_cases.status_code == 200

    # 4. Overlaps
    res_overlaps = client.get("/api/v1/aicte/overlaps", headers=headers)
    assert res_overlaps.status_code == 200

    # 5. Transfers
    res_transfers = client.get("/api/v1/aicte/transfers/incoming", headers=headers)
    assert res_transfers.status_code == 200
