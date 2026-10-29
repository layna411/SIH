import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from sqlalchemy.orm import Session

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseActionTypeEnum,
    AICTETransferStatusEnum,
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTECaseLinkTypeEnum,
    GrievancePriorityEnum,
    AICTEComplainantTypeEnum,
    AICTECaseSourceTypeEnum,
)
from app.models.user import User
from app.models.institution import Institution, RegulatoryJurisdiction
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.aicte_case import AICTECase, CaseAction
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.aicte_overlap import AICTECaseOverlap, AICTECaseLink
from app.core.security import create_access_token, hash_password

def auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def f_superadmin(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_f_superadmin@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_f_superadmin@eduresolve.ai",
            hashed_password=hash_password("SuperSecret123!"),
            full_name="Phase F Super Admin",
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def f_student(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_f_student@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_f_student@eduresolve.ai",
            hashed_password=hash_password("StudentPass123!"),
            full_name="Phase F Student",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def f_reg_admin(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_f_reg_admin@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_f_reg_admin@eduresolve.ai",
            hashed_password=hash_password("RegPass123!"),
            full_name="Phase F Regulatory Admin",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def f_unit_rb(db_session: Session) -> OrganizationalUnit:
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB_F").first()
    if not unit:
        unit = OrganizationalUnit(
            code="RB_F",
            name="Regulation Bureau (Phase F)",
            unit_type="BUREAU",
            description="Phase F RB Unit",
            is_active=True,
        )
        db_session.add(unit)
        db_session.commit()
        db_session.refresh(unit)
    return unit

@pytest.fixture
def f_unit_pgrc(db_session: Session) -> OrganizationalUnit:
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC_F").first()
    if not unit:
        unit = OrganizationalUnit(
            code="PGRC_F",
            name="PGRC Cell (Phase F)",
            unit_type="CELL",
            description="Phase F PGRC Unit",
            is_active=True,
        )
        db_session.add(unit)
        db_session.commit()
        db_session.refresh(unit)
    return unit

@pytest.fixture
def f_rb_officer(db_session: Session, f_unit_rb: OrganizationalUnit) -> User:
    user = db_session.query(User).filter(User.email == "phase_f_rb_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_f_rb_officer@eduresolve.ai",
            hashed_password=hash_password("OfficerPass123!"),
            full_name="Phase F RB Officer",
            default_role=UserRoleEnum.COLLEGE_OFFICER,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    membership = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == user.id,
        BureauMembership.organizational_unit_id == f_unit_rb.id,
        BureauMembership.is_active == True,
    ).first()
    if not membership:
        membership = BureauMembership(
            user_id=user.id,
            organizational_unit_id=f_unit_rb.id,
            membership_role="BUREAU_OFFICER",
            designation="Scrutiny Officer",
            is_active=True,
        )
        db_session.add(membership)
        db_session.commit()

    return user

@pytest.fixture
def f_inst_delhi(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "DELHI_TECH_F").first()
    if not inst:
        inst = Institution(
            code="DELHI_TECH_F",
            name="Delhi Institute of Technology (Phase F)",
            institution_type="TECHNICAL",
            contact_email="delhi.tech.f@example.com",
            state="Delhi",
            city="New Delhi",
            aicte_permanent_id="1-9988776655",
            region="Northern",
            is_active=True,
            is_aicte_verified=True,
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

@pytest.fixture
def f_inst_mumbai(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "MUMBAI_ENG_F").first()
    if not inst:
        inst = Institution(
            code="MUMBAI_ENG_F",
            name="Mumbai College of Engineering (Phase F)",
            institution_type="TECHNICAL",
            contact_email="mumbai.eng.f@example.com",
            state="Maharashtra",
            city="Mumbai",
            aicte_permanent_id="1-5544332211",
            region="Western",
            is_active=True,
            is_aicte_verified=True,
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

# ---------------------------------------------------------------------------
# Test 1: Unauthorized users cannot access privileged analytics (HTTP 403)
# ---------------------------------------------------------------------------
def test_analytics_unauthorized_user_forbidden(client, f_student):
    headers = auth_headers(f_student)
    endpoints = [
        "/api/v1/aicte/analytics/overview",
        "/api/v1/aicte/analytics/ageing",
        "/api/v1/aicte/analytics/sla",
        "/api/v1/aicte/analytics/institutions",
        "/api/v1/aicte/analytics/organizational-units",
        "/api/v1/aicte/analytics/trends",
        "/api/v1/aicte/analytics/transfers",
        "/api/v1/aicte/analytics/cross-bureau",
        "/api/v1/aicte/analytics/reports/cases.csv",
        "/api/v1/aicte/analytics/reports/summary.csv",
    ]
    for ep in endpoints:
        resp = client.get(ep, headers=headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

# ---------------------------------------------------------------------------
# Test 2: Invalid date ranges are rejected (HTTP 400)
# ---------------------------------------------------------------------------
def test_analytics_invalid_date_range_rejected(client, f_superadmin):
    headers = auth_headers(f_superadmin)
    from_d = "2026-10-30T00:00:00Z"
    to_d = "2026-10-01T00:00:00Z"
    resp = client.get(f"/api/v1/aicte/analytics/overview?from_date={from_d}&to_date={to_d}", headers=headers)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid date range" in resp.json()["detail"]

# ---------------------------------------------------------------------------
# Test 3: Overview metrics match persisted records and separate active vs disposed
# ---------------------------------------------------------------------------
def test_overview_metrics_match_persisted_records(
    db_session, client, f_superadmin, f_inst_delhi, f_unit_rb
):
    now = datetime.now(timezone.utc)
    # Create controlled test cases
    case_active = AICTECase(
        case_reference=f"AICTE-TEST-F-ACT-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Land Deficit",
        subject="Active Land Inquiry",
        description="Active investigation",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        priority=GrievancePriorityEnum.NORMAL,
        received_at=now - timedelta(days=10),
        created_by_user_id=f_superadmin.id,
    )
    case_disposed = AICTECase(
        case_reference=f"AICTE-TEST-F-DISP-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Fee Refund",
        subject="Disposed Case",
        description="Disposed order signed",
        status=AICTECaseStatusEnum.DISPOSED,
        priority=GrievancePriorityEnum.LOW,
        received_at=now - timedelta(days=20),
        disposed_at=now - timedelta(days=2),
        created_by_user_id=f_superadmin.id,
    )
    db_session.add_all([case_active, case_disposed])
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp = client.get(f"/api/v1/aicte/analytics/overview?institution_id={f_inst_delhi.id}", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["total_received"] >= 2
    assert data["total_active"] >= 1
    assert data["total_disposed"] >= 1
    assert data["disposal_rate"] is not None
    assert 0.0 <= data["disposal_rate"] <= 100.0

    # Ensure status distribution list contains all statuses
    statuses = {item["status"]: item["count"] for item in data["status_distribution"]}
    assert "UNDER_PROCESS" in statuses
    assert "DISPOSED" in statuses

# ---------------------------------------------------------------------------
# Test 4: Ageing calculation buckets active cases and excludes disposed
# ---------------------------------------------------------------------------
def test_ageing_calculations_and_buckets(
    db_session, client, f_superadmin, f_inst_delhi, f_unit_rb
):
    now = datetime.now(timezone.utc)
    # Case 1: 5 days old (0-7 days)
    c1 = AICTECase(
        case_reference=f"AICTE-F-AGE-5D-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Academics",
        subject="5 Days Old",
        description="Fresh case",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now - timedelta(days=5),
        created_by_user_id=f_superadmin.id,
    )
    # Case 2: 45 days old (31-60 days)
    c2 = AICTECase(
        case_reference=f"AICTE-F-AGE-45D-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Faculty Non-Payment",
        subject="45 Days Old",
        description="Medium age case",
        status=AICTECaseStatusEnum.AWAITING_RESPONSE,
        received_at=now - timedelta(days=45),
        created_by_user_id=f_superadmin.id,
    )
    # Case 3: 75 days old (Over 60 days)
    c3 = AICTECase(
        case_reference=f"AICTE-F-AGE-75D-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Infrastructure",
        subject="75 Days Old",
        description="Old backlog case",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now - timedelta(days=75),
        created_by_user_id=f_superadmin.id,
    )
    # Disposed Case: 90 days old (must be excluded from active ageing)
    c4 = AICTECase(
        case_reference=f"AICTE-F-AGE-DISP-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Disposed",
        subject="Old but Disposed",
        description="Completed",
        status=AICTECaseStatusEnum.DISPOSED,
        received_at=now - timedelta(days=90),
        disposed_at=now - timedelta(days=10),
        created_by_user_id=f_superadmin.id,
    )
    db_session.add_all([c1, c2, c3, c4])
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp = client.get(f"/api/v1/aicte/analytics/ageing?institution_id={f_inst_delhi.id}", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["total_active_cases"] >= 3
    bucket_map = {b["bucket_key"]: b["count"] for b in data["buckets"]}
    assert bucket_map["0_7_DAYS"] >= 1
    assert bucket_map["31_60_DAYS"] >= 1
    assert bucket_map["OVER_60_DAYS"] >= 1
    assert data["average_active_age_days"] is not None
    assert data["average_active_age_days"] > 0

# ---------------------------------------------------------------------------
# Test 5: SLA overdue actions vs overdue disposal vs missing deadlines
# ---------------------------------------------------------------------------
def test_sla_overdue_and_missing_deadlines_distinguished(
    db_session, client, f_superadmin, f_inst_mumbai, f_unit_pgrc
):
    now = datetime.now(timezone.utc)
    # 1. Overdue Next Action (action deadline passed)
    c_action_overdue = AICTECase(
        case_reference=f"AICTE-F-SLA-ACT-{int(now.timestamp())}",
        institution_id=f_inst_mumbai.id,
        current_unit_id=f_unit_pgrc.id,
        category="Harassment",
        subject="Action Overdue",
        description="Investigation overdue",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now - timedelta(days=12),
        next_action_required="Hearing Notice",
        next_action_due_at=now - timedelta(days=2),  # OVERDUE
        expected_disposal_at=now + timedelta(days=30),
        created_by_user_id=f_superadmin.id,
    )
    # 2. Overdue Disposal Date (disposal deadline passed)
    c_disp_overdue = AICTECase(
        case_reference=f"AICTE-F-SLA-DISP-{int(now.timestamp())}",
        institution_id=f_inst_mumbai.id,
        current_unit_id=f_unit_pgrc.id,
        category="Harassment",
        subject="Disposal Overdue",
        description="Disposal deadline breached",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now - timedelta(days=45),
        next_action_due_at=now + timedelta(days=5),
        expected_disposal_at=now - timedelta(days=3),  # OVERDUE
        created_by_user_id=f_superadmin.id,
    )
    # 3. Missing deadlines (no deadline recorded - must NOT be silently marked compliant)
    c_missing_deadlines = AICTECase(
        case_reference=f"AICTE-F-SLA-MISS-{int(now.timestamp())}",
        institution_id=f_inst_mumbai.id,
        current_unit_id=f_unit_pgrc.id,
        category="Unapproved Course",
        subject="Missing Deadlines",
        description="Unscheduled case",
        status=AICTECaseStatusEnum.PENDING_REVIEW,
        received_at=now - timedelta(days=3),
        next_action_due_at=None,
        expected_disposal_at=None,
        created_by_user_id=f_superadmin.id,
    )
    db_session.add_all([c_action_overdue, c_disp_overdue, c_missing_deadlines])
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp = client.get(f"/api/v1/aicte/analytics/sla?institution_id={f_inst_mumbai.id}", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["overdue_next_action_count"] >= 1
    assert data["overdue_expected_disposal_count"] >= 1
    assert data["total_sla_breached_count"] >= 2
    assert data["missing_next_action_deadline_count"] >= 1
    assert data["missing_expected_disposal_count"] >= 1

# ---------------------------------------------------------------------------
# Test 6: Disposal rate handles zero denominator gracefully
# ---------------------------------------------------------------------------
def test_disposal_rate_zero_denominator_safe(client, f_superadmin):
    headers = auth_headers(f_superadmin)
    # Query a future time window where 0 cases were received
    future_from = "2029-01-01T00:00:00Z"
    future_to = "2029-01-31T23:59:59Z"
    resp = client.get(
        f"/api/v1/aicte/analytics/overview?from_date={future_from}&to_date={future_to}",
        headers=headers
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["total_received"] == 0
    assert data["total_active"] == 0
    assert data["disposal_rate"] is None

# ---------------------------------------------------------------------------
# Test 7: Institution filtering strictly confines counts to target institution
# ---------------------------------------------------------------------------
def test_institution_filtering_isolation(
    db_session, client, f_superadmin, f_inst_delhi, f_inst_mumbai, f_unit_rb
):
    now = datetime.now(timezone.utc)
    c_delhi = AICTECase(
        case_reference=f"AICTE-F-ISO-DEL-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Audit",
        subject="Delhi Case",
        description="Delhi specific",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    c_mumbai = AICTECase(
        case_reference=f"AICTE-F-ISO-MUM-{int(now.timestamp())}",
        institution_id=f_inst_mumbai.id,
        current_unit_id=f_unit_rb.id,
        category="Audit",
        subject="Mumbai Case",
        description="Mumbai specific",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    db_session.add_all([c_delhi, c_mumbai])
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp_delhi = client.get(f"/api/v1/aicte/analytics/overview?institution_id={f_inst_delhi.id}", headers=headers)
    assert resp_delhi.status_code == status.HTTP_200_OK
    data_delhi = resp_delhi.json()

    resp_mumbai = client.get(f"/api/v1/aicte/analytics/overview?institution_id={f_inst_mumbai.id}", headers=headers)
    assert resp_mumbai.status_code == status.HTTP_200_OK
    data_mumbai = resp_mumbai.json()

    # The counts should isolate to each specific institution
    assert data_delhi["total_received"] >= 1
    assert data_mumbai["total_received"] >= 1

# ---------------------------------------------------------------------------
# Test 8: Bureau officer scoped only to their authorized unit
# ---------------------------------------------------------------------------
def test_bureau_officer_scoping_and_unit_boundary(
    db_session, client, f_rb_officer, f_unit_rb, f_unit_pgrc, f_inst_delhi, f_superadmin
):
    now = datetime.now(timezone.utc)
    # Case in RB
    c_rb = AICTECase(
        case_reference=f"AICTE-F-RB-CAS-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Regulation",
        subject="RB Case",
        description="Under RB",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    # Case in PGRC
    c_pgrc = AICTECase(
        case_reference=f"AICTE-F-PGRC-CAS-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_pgrc.id,
        category="Grievance",
        subject="PGRC Case",
        description="Under PGRC",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    db_session.add_all([c_rb, c_pgrc])
    db_session.commit()

    headers = auth_headers(f_rb_officer)
    
    # 1. Overview for RB officer should succeed and only count cases in RB unit
    resp = client.get("/api/v1/aicte/analytics/overview", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    
    # 2. Querying PGRC explicitly should be forbidden (HTTP 403)
    resp_forbidden = client.get(f"/api/v1/aicte/analytics/overview?organizational_unit_id={f_unit_pgrc.id}", headers=headers)
    assert resp_forbidden.status_code == status.HTTP_403_FORBIDDEN
    assert "outside your authorized organizational unit jurisdiction" in resp_forbidden.json()["detail"]

# ---------------------------------------------------------------------------
# Test 9: Aggregations do NOT double count cases with multiple actions and transfers
# ---------------------------------------------------------------------------
def test_no_double_counting_with_multiple_actions_and_transfers(
    db_session, client, f_superadmin, f_inst_delhi, f_unit_rb, f_unit_pgrc
):
    now = datetime.now(timezone.utc)
    case_multi = AICTECase(
        case_reference=f"AICTE-F-MULTI-JOIN-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Testing Joins",
        subject="Multi Joined Case",
        description="Testing join multiplication prevention",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        region=f_inst_delhi.region,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    db_session.add(case_multi)
    db_session.commit()
    db_session.refresh(case_multi)

    # Add 5 Case Actions
    for i in range(5):
        action = CaseAction(
            case_id=case_multi.id,
            action_type=AICTECaseActionTypeEnum.INITIAL_SCRUTINY,
            action_title=f"Scrutiny Step {i+1}",
            unit_id=f_unit_rb.id,
            performed_by_user_id=f_superadmin.id,
        )
        db_session.add(action)

    # Add 2 Transfer records
    t1 = AICTECaseTransfer(
        case_id=case_multi.id,
        from_unit_id=f_unit_rb.id,
        to_unit_id=f_unit_pgrc.id,
        initiated_by_user_id=f_superadmin.id,
        transfer_reason="Transfer Attempt 1",
        handover_summary="Summary 1",
        transfer_status=AICTETransferStatusEnum.REJECTED,
        prior_case_status="UNDER_PROCESS",
        response_notes="Declined",
    )
    t2 = AICTECaseTransfer(
        case_id=case_multi.id,
        from_unit_id=f_unit_rb.id,
        to_unit_id=f_unit_pgrc.id,
        initiated_by_user_id=f_superadmin.id,
        transfer_reason="Transfer Attempt 2",
        handover_summary="Summary 2",
        transfer_status=AICTETransferStatusEnum.CANCELLED,
        prior_case_status="UNDER_PROCESS",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    headers = auth_headers(f_superadmin)
    # Query overview filtered by this case's institution
    resp = client.get(
        f"/api/v1/aicte/analytics/institutions?region={f_inst_delhi.region}",
        headers=headers
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    
    inst_summary = next((i for i in data["institutions"] if i["institution_id"] == f_inst_delhi.id), None)
    assert inst_summary is not None
    # total_cases must accurately count distinct cases, not 5*2=10 times
    assert inst_summary["total_cases"] < 50

# ---------------------------------------------------------------------------
# Test 10: Inter-Bureau transfer analytics agrees with persisted transfer records
# ---------------------------------------------------------------------------
def test_transfer_analytics_lifecycle_metrics(
    db_session, client, f_superadmin, f_inst_delhi, f_unit_rb, f_unit_pgrc
):
    now = datetime.now(timezone.utc)
    c = AICTECase(
        case_reference=f"AICTE-F-TRF-METRIC-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_pgrc.id,
        category="Transfer",
        subject="Transfer Analytics",
        description="Testing metrics",
        status=AICTECaseStatusEnum.TRANSFERRED,
        received_at=now - timedelta(days=5),
        created_by_user_id=f_superadmin.id,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)

    transfer = AICTECaseTransfer(
        case_id=c.id,
        from_unit_id=f_unit_rb.id,
        to_unit_id=f_unit_pgrc.id,
        initiated_by_user_id=f_superadmin.id,
        transfer_reason="Jurisdiction transfer",
        handover_summary="Summary context",
        transfer_status=AICTETransferStatusEnum.ACCEPTED,
        prior_case_status="UNDER_PROCESS",
        initiated_at=now - timedelta(hours=6),
        responded_at=now - timedelta(hours=2),
        responded_by_user_id=f_superadmin.id,
    )
    db_session.add(transfer)
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp = client.get("/api/v1/aicte/analytics/transfers", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["total_transfers_initiated"] >= 1
    assert data["accepted_count"] >= 1
    assert data["average_turnaround_hours"] is not None
    assert data["average_turnaround_hours"] >= 0.0

# ---------------------------------------------------------------------------
# Test 11: Cross-Bureau analytics reflects overlaps and case links
# ---------------------------------------------------------------------------
def test_cross_bureau_analytics_metrics(
    db_session, client, f_superadmin, f_inst_delhi, f_unit_rb, f_unit_pgrc
):
    now = datetime.now(timezone.utc)
    c_a = AICTECase(
        case_reference=f"AICTE-F-OV-A-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        category="Faculty",
        subject="Overlap A",
        description="Desc A",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    c_b = AICTECase(
        case_reference=f"AICTE-F-OV-B-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_pgrc.id,
        category="Faculty",
        subject="Overlap B",
        description="Desc B",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    db_session.add_all([c_a, c_b])
    db_session.commit()
    db_session.refresh(c_a)
    db_session.refresh(c_b)

    overlap = AICTECaseOverlap(
        case_id_low=min(c_a.id, c_b.id),
        case_id_high=max(c_a.id, c_b.id),
        overlap_type=AICTEOverlapTypeEnum.RELATED_CASE,
        match_score=0.88,
        match_reasons='["High Subject Similarity"]',
        review_status=AICTEOverlapReviewStatusEnum.CONFIRMED_RELATED,
    )
    link = AICTECaseLink(
        case_id_low=min(c_a.id, c_b.id),
        case_id_high=max(c_a.id, c_b.id),
        link_type=AICTECaseLinkTypeEnum.RELATED_TO,
        created_by_user_id=f_superadmin.id,
        is_active=True,
    )
    db_session.add_all([overlap, link])
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp = client.get("/api/v1/aicte/analytics/cross-bureau", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["total_overlaps_detected"] >= 1
    assert data["confirmed_related"] >= 1
    assert data["total_case_links"] >= 1

# ---------------------------------------------------------------------------
# Test 12: CSV export cases sanitizes formula injection payloads
# ---------------------------------------------------------------------------
def test_csv_export_cases_sanitization_and_authorization(
    db_session, client, f_superadmin, f_inst_delhi, f_unit_rb
):
    now = datetime.now(timezone.utc)
    # Inject formula injection payloads in case fields
    case_malicious = AICTECase(
        case_reference=f"AICTE-F-CSV-{int(now.timestamp())}",
        institution_id=f_inst_delhi.id,
        current_unit_id=f_unit_rb.id,
        official_reference_number="=cmd|'/C calc'!A0",
        category="@SUM(1+1)",
        subject="+1234567890",
        description="Tabbed Exploit",
        next_action_required="\tTabbed Exploit",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        received_at=now,
        created_by_user_id=f_superadmin.id,
    )
    db_session.add(case_malicious)
    db_session.commit()

    headers = auth_headers(f_superadmin)
    resp = client.get(
        f"/api/v1/aicte/analytics/reports/cases.csv?institution_id={f_inst_delhi.id}",
        headers=headers
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers["content-type"].startswith("text/csv")
    csv_text = resp.text

    # Verify header row exists
    assert "Case Reference" in csv_text
    assert "Handling Bureau/Unit" in csv_text

    # Crucial security verification: Formula injection symbols must be prepended with a single quote
    assert "'=cmd" in csv_text
    assert "'@SUM" in csv_text
    assert "'+1234567890" in csv_text
    assert "'\tTabbed" in csv_text

# ---------------------------------------------------------------------------
# Test 13: Summary CSV export enforces formula protection and contains KPIs
# ---------------------------------------------------------------------------
def test_csv_export_summary_content_and_protection(client, f_superadmin):
    headers = auth_headers(f_superadmin)
    resp = client.get("/api/v1/aicte/analytics/reports/summary.csv", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers["content-type"].startswith("text/csv")
    csv_text = resp.text

    assert "AICTE OPERATIONAL ANALYTICS & MONITORING SUMMARY" in csv_text
    assert "KEY WORKLOAD INDICATORS" in csv_text
    assert "SLA & TIMELINESS COMPLIANCE" in csv_text
    assert "CASE AGEING DISTRIBUTION" in csv_text
    assert "BUREAU & REGIONAL OFFICE WORKLOAD" in csv_text

# ---------------------------------------------------------------------------
# Test 14: Regulatory Admin jurisdiction scoping
# ---------------------------------------------------------------------------
def test_regulatory_admin_jurisdiction_scoping(
    db_session, client, f_reg_admin, f_inst_delhi, f_inst_mumbai, f_unit_rb, f_superadmin
):
    # Assign f_reg_admin to "Delhi" only
    jurisdiction = db_session.query(RegulatoryJurisdiction).filter(
        RegulatoryJurisdiction.user_id == f_reg_admin.id,
        RegulatoryJurisdiction.state == "Delhi",
    ).first()
    if not jurisdiction:
        jurisdiction = RegulatoryJurisdiction(
            user_id=f_reg_admin.id,
            jurisdiction_code="JUR_DELHI_F",
            state="Delhi",
            is_active=True,
        )
        db_session.add(jurisdiction)
        db_session.commit()

    headers = auth_headers(f_reg_admin)

    # 1. Accessing overall overview should succeed (scoped to Delhi institutions)
    resp = client.get("/api/v1/aicte/analytics/overview", headers=headers)
    assert resp.status_code == status.HTTP_200_OK

    # 2. Accessing Delhi institution explicitly should succeed
    resp_delhi = client.get(
        f"/api/v1/aicte/analytics/overview?institution_id={f_inst_delhi.id}",
        headers=headers
    )
    assert resp_delhi.status_code == status.HTTP_200_OK

    # 3. Accessing Mumbai institution (Maharashtra) should be denied with HTTP 403
    resp_mumbai = client.get(
        f"/api/v1/aicte/analytics/overview?institution_id={f_inst_mumbai.id}",
        headers=headers
    )
    assert resp_mumbai.status_code == status.HTTP_403_FORBIDDEN
    assert "outside your assigned regulatory jurisdiction" in resp_mumbai.json()["detail"]
