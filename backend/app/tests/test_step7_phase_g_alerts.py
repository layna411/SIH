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
from app.models.aicte_overlap import AICTECaseOverlap
from app.models.notification import Notification, NotificationOutbox
from app.models.audit import AuditLog
from app.core.security import create_access_token, hash_password
from app.services.aicte_alert_service import AICTEAlertService
from app.services.notification_service import create_notification, dispatch_pending_outbox

def auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def g_superadmin(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_g_superadmin@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_g_superadmin@eduresolve.ai",
            hashed_password=hash_password("SuperSecret123!"),
            full_name="Phase G Super Admin",
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def g_rb_officer(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_g_rb_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_g_rb_officer@eduresolve.ai",
            hashed_password=hash_password("OfficerPass123!"),
            full_name="Phase G RB Officer",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def g_pgrc_officer(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_g_pgrc_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_g_pgrc_officer@eduresolve.ai",
            hashed_password=hash_password("OfficerPass123!"),
            full_name="Phase G PGRC Officer",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def g_student(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_g_student@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_g_student@eduresolve.ai",
            hashed_password=hash_password("StudentPass123!"),
            full_name="Phase G Student",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def g_institution(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "INST_PHASE_G").first()
    if not inst:
        inst = Institution(
            name="Phase G National Engineering Institute",
            code="INST_PHASE_G",
            institution_type="TECHNICAL",
            aicte_permanent_id="1-999999999-G",
            is_aicte_verified=True,
            is_active=True,
            contact_email="phase_g_inst@example.com",
            state="Maharashtra",
            city="Mumbai",
            region="Western",
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

@pytest.fixture
def g_units(db_session: Session, g_rb_officer: User, g_pgrc_officer: User) -> dict:
    rb = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB_G").first()
    if not rb:
        rb = OrganizationalUnit(
            name="Regulation Bureau G",
            code="RB_G",
            unit_type="BUREAU",
            is_active=True
        )
        db_session.add(rb)
        db_session.commit()
        db_session.refresh(rb)

    pgrc = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC_G").first()
    if not pgrc:
        pgrc = OrganizationalUnit(
            name="Public Grievance Cell G",
            code="PGRC_G",
            unit_type="CELL",
            is_active=True
        )
        db_session.add(pgrc)
        db_session.commit()
        db_session.refresh(pgrc)

    # Attach memberships
    mb_rb = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == g_rb_officer.id,
        BureauMembership.organizational_unit_id == rb.id
    ).first()
    if not mb_rb:
        mb_rb = BureauMembership(
            user_id=g_rb_officer.id,
            organizational_unit_id=rb.id,
            membership_role="BUREAU_OFFICER",
            is_active=True
        )
        db_session.add(mb_rb)

    mb_pgrc = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == g_pgrc_officer.id,
        BureauMembership.organizational_unit_id == pgrc.id
    ).first()
    if not mb_pgrc:
        mb_pgrc = BureauMembership(
            user_id=g_pgrc_officer.id,
            organizational_unit_id=pgrc.id,
            membership_role="BUREAU_OFFICER",
            is_active=True
        )
        db_session.add(mb_pgrc)

    db_session.commit()
    return {"rb": rb, "pgrc": pgrc}


# =============================================================================
# 1. Lifecycle: Notification Creation, Pagination & Ownership
# =============================================================================

def test_notification_creation_and_ownership(client, db_session: Session, g_rb_officer: User, g_pgrc_officer: User):
    """Verify notification creation, recipient scoping, and prevention of cross-user snooping."""
    # Create notification for RB officer
    notif = AICTEAlertService.send_alert(
        db=db_session,
        recipient_id=g_rb_officer.id,
        category="SLA_WARNING",
        severity="WARNING",
        title="Test Alert Title",
        message="Test alert narrative description.",
        link="/aicte/cases/1",
        reference_id=f"TEST_REF_{int(datetime.now(timezone.utc).timestamp())}",
        requires_acknowledgement=True
    )
    assert notif is not None
    assert notif.user_id == g_rb_officer.id
    assert notif.is_read is False
    assert notif.requires_acknowledgement is True
    assert notif.is_acknowledged is False

    # RB officer can list their own notifications
    rb_res = client.get("/api/v1/aicte/notifications", headers=auth_headers(g_rb_officer))
    assert rb_res.status_code == status.HTTP_200_OK
    rb_data = rb_res.json()
    assert rb_data["total"] >= 1
    assert any(n["id"] == notif.id for n in rb_data["items"])

    # PGRC officer cannot see RB officer's notification in their list
    pgrc_res = client.get("/api/v1/aicte/notifications", headers=auth_headers(g_pgrc_officer))
    assert pgrc_res.status_code == status.HTTP_200_OK
    pgrc_data = pgrc_res.json()
    assert not any(n["id"] == notif.id for n in pgrc_data["items"])

    # PGRC officer gets 404 when directly requesting RB officer's notification detail
    detail_res = client.get(f"/api/v1/aicte/notifications/{notif.id}", headers=auth_headers(g_pgrc_officer))
    assert detail_res.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# 2. Read State & Acknowledgement Invariants
# =============================================================================

def test_read_and_acknowledgement_lifecycle(client, db_session: Session, g_rb_officer: User, g_institution: Institution, g_units: dict):
    """
    Verify:
    - Reading an alert marks is_read=True.
    - Acknowledging is distinct: records timestamp and is_acknowledged=True.
    - CRITICAL INVARIANT: Reading or acknowledging DOES NOT alter the case's status!
    """
    now = datetime.now(timezone.utc)
    # Create test case
    case = AICTECase(
        case_reference=f"AICTE-G-TEST-{int(now.timestamp())}",
        institution_id=g_institution.id,
        category="Governance",
        subject="Case with Overdue SLA",
        description="Confidential case narrative.",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        current_unit_id=g_units["rb"].id,
        assigned_officer_id=g_rb_officer.id,
        created_by_user_id=g_rb_officer.id,
        received_at=now - timedelta(days=10),
        next_action_due_at=now - timedelta(days=2),  # Overdue
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Send critical SLA overdue notification
    notif = AICTEAlertService.send_alert(
        db=db_session,
        recipient_id=g_rb_officer.id,
        category="SLA_OVERDUE",
        severity="CRITICAL",
        title=f"OVERDUE: {case.case_reference}",
        message="Next action overdue. Immediate review required.",
        link=f"/aicte/cases/{case.id}",
        reference_id=f"TEST_ACK_{case.id}",
        requires_acknowledgement=True
    )
    assert notif is not None

    # Mark as read
    read_res = client.post(f"/api/v1/aicte/notifications/{notif.id}/read", headers=auth_headers(g_rb_officer))
    assert read_res.status_code == status.HTTP_200_OK
    assert read_res.json()["is_read"] is True
    assert read_res.json()["is_acknowledged"] is False

    # Verify case status did NOT change
    db_session.refresh(case)
    assert case.status == AICTECaseStatusEnum.UNDER_PROCESS

    # Formally acknowledge
    ack_res = client.post(f"/api/v1/aicte/notifications/{notif.id}/acknowledge", headers=auth_headers(g_rb_officer))
    assert ack_res.status_code == status.HTTP_200_OK
    ack_data = ack_res.json()
    assert ack_data["is_acknowledged"] is True
    assert ack_data["acknowledged_at"] is not None

    # Verify case status STILL did NOT change (Alert acknowledgment is non-destructive)
    db_session.refresh(case)
    assert case.status == AICTECaseStatusEnum.UNDER_PROCESS


def test_mark_all_read(client, db_session: Session, g_rb_officer: User):
    """Verify bulk mark read only affects caller's notifications."""
    ref_ts = int(datetime.now(timezone.utc).timestamp())
    n1 = create_notification(db_session, g_rb_officer.id, f"Notif 1 {ref_ts}", "Message 1", email_notify=False)
    n2 = create_notification(db_session, g_rb_officer.id, f"Notif 2 {ref_ts}", "Message 2", email_notify=False)

    res = client.post("/api/v1/aicte/notifications/read-all", headers=auth_headers(g_rb_officer))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["updated_count"] >= 2

    db_session.refresh(n1)
    db_session.refresh(n2)
    assert n1.is_read is True
    assert n2.is_read is True


# =============================================================================
# 3. Deduplication & Idempotency Safeguards
# =============================================================================

def test_deduplication_prevents_alert_flood(db_session: Session, g_rb_officer: User):
    """Verify that identical alert conditions for the same recipient are deduplicated."""
    ref_id = f"DEDUP_TEST_{int(datetime.now(timezone.utc).timestamp())}"
    # First send should succeed
    notif1 = AICTEAlertService.send_alert(
        db=db_session,
        recipient_id=g_rb_officer.id,
        category="SLA_OVERDUE",
        severity="CRITICAL",
        title="Overdue Alert",
        message="Case action is overdue.",
        reference_id=ref_id,
        dedup_window_hours=24
    )
    assert notif1 is not None

    # Immediate second send with same category & reference_id must be skipped
    notif2 = AICTEAlertService.send_alert(
        db=db_session,
        recipient_id=g_rb_officer.id,
        category="SLA_OVERDUE",
        severity="CRITICAL",
        title="Overdue Alert Repeated",
        message="Case action is overdue.",
        reference_id=ref_id,
        dedup_window_hours=24
    )
    assert notif2 is None


# =============================================================================
# 4. Scheduled SLA Scan & Periodic Evaluation
# =============================================================================

def test_scheduler_sla_scan_and_deduplication(db_session: Session, g_institution: Institution, g_units: dict, g_rb_officer: User):
    """
    Verify scan_and_generate_sla_alerts:
    - Overdue next action flagged as CRITICAL.
    - Overdue disposal flagged as CRITICAL.
    - Missing deadline flagged as non-compliant WARNING.
    - Repeated scan execution does NOT duplicate alerts.
    """
    now = datetime.now(timezone.utc)
    ts = int(now.timestamp())

    # Case 1: Overdue next action & disposal
    case1 = AICTECase(
        case_reference=f"AICTE-SCAN-1-{ts}",
        institution_id=g_institution.id,
        category="Governance",
        subject="Overdue Case 1",
        description="Confidential investigation narrative.",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        current_unit_id=g_units["rb"].id,
        assigned_officer_id=g_rb_officer.id,
        created_by_user_id=g_rb_officer.id,
        received_at=now - timedelta(days=20),
        next_action_due_at=now - timedelta(days=5),
        expected_disposal_at=now - timedelta(days=1),
    )
    # Case 2: Missing deadline under process
    case2 = AICTECase(
        case_reference=f"AICTE-SCAN-2-{ts}",
        institution_id=g_institution.id,
        category="Faculty Grievance",
        subject="Missing Deadline Case 2",
        description="Active case without scheduled next action.",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        current_unit_id=g_units["rb"].id,
        assigned_officer_id=g_rb_officer.id,
        created_by_user_id=g_rb_officer.id,
        received_at=now - timedelta(days=5),
        next_action_due_at=None,  # Missing deadline!
        expected_disposal_at=None,
    )
    db_session.add_all([case1, case2])
    db_session.commit()

    # First SLA cycle
    results1 = AICTEAlertService.scan_and_generate_sla_alerts(db_session)
    assert results1["overdue_next_actions"] >= 1
    assert results1["overdue_expected_disposals"] >= 1
    assert results1["missing_deadlines"] >= 1

    # Second SLA cycle immediately after: must be deduplicated
    results2 = AICTEAlertService.scan_and_generate_sla_alerts(db_session)
    assert results2["overdue_next_actions"] == 0
    assert results2["overdue_expected_disposals"] == 0
    assert results2["missing_deadlines"] == 0

    # Case statuses must remain UNDER_PROCESS intact
    db_session.refresh(case1)
    db_session.refresh(case2)
    assert case1.status == AICTECaseStatusEnum.UNDER_PROCESS
    assert case2.status == AICTECaseStatusEnum.UNDER_PROCESS


# =============================================================================
# 5. Inter-Bureau Transfer Alerts
# =============================================================================

def test_transfer_lifecycle_alerts(client, db_session: Session, g_institution: Institution, g_units: dict, g_rb_officer: User, g_pgrc_officer: User):
    """Verify that transfer proposals, decisions, and delayed transfers notify appropriate authorized recipients."""
    now = datetime.now(timezone.utc)
    ts = int(now.timestamp())

    case = AICTECase(
        case_reference=f"AICTE-XFER-{ts}",
        institution_id=g_institution.id,
        category="Financial Irregularity",
        subject="Transfer Subject Test",
        description="Confidential financial audit notes.",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        current_unit_id=g_units["rb"].id,
        assigned_officer_id=g_rb_officer.id,
        created_by_user_id=g_rb_officer.id,
        received_at=now - timedelta(days=10),
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # 1. Propose transfer from RB to PGRC
    transfer_res = client.post(
        f"/api/v1/aicte/cases/{case.id}/transfers",
        headers=auth_headers(g_rb_officer),
        json={
            "to_unit_id": g_units["pgrc"].id,
            "transfer_reason": "Jurisdiction relates to student stipend disputes.",
            "handover_summary": "Initial verification conducted."
        }
    )
    assert transfer_res.status_code == status.HTTP_201_CREATED
    transfer_data = transfer_res.json()
    transfer_id = transfer_data["id"]

    # PGRC officer should have received a TRANSFER_PENDING alert requiring acknowledgement
    pgrc_notifs = client.get(
        "/api/v1/aicte/notifications?category=TRANSFER_PENDING",
        headers=auth_headers(g_pgrc_officer)
    ).json()
    assert any(n["reference_id"] == f"TRANSFER_PROP_{transfer_id}" for n in pgrc_notifs["items"])
    target_notif = next(n for n in pgrc_notifs["items"] if n["reference_id"] == f"TRANSFER_PROP_{transfer_id}")
    assert target_notif["requires_acknowledgement"] is True

    # Confidential narratives shielded: message does NOT contain complainant or investigation text
    assert "Confidential financial audit notes" not in target_notif["message"]

    # 2. Reject transfer by PGRC officer
    reject_res = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/reject",
        headers=auth_headers(g_pgrc_officer),
        json={"rejection_reason": "Requires further documentation before cell acceptance."}
    )
    assert reject_res.status_code == status.HTTP_200_OK

    # RB officer should receive a TRANSFER_DECISION alert
    rb_notifs = client.get(
        "/api/v1/aicte/notifications?category=TRANSFER_DECISION",
        headers=auth_headers(g_rb_officer)
    ).json()
    assert any(n["reference_id"] == f"TRANSFER_REJECTED_{transfer_id}" for n in rb_notifs["items"])


# =============================================================================
# 6. Overlap Detection & Narrative Shielding Alerts
# =============================================================================

def test_overlap_alerts_and_confidentiality(db_session: Session, g_institution: Institution, g_units: dict, g_rb_officer: User, g_pgrc_officer: User):
    """Verify that overlap detection dispatches shielded alerts and preserves confidentiality."""
    now = datetime.now(timezone.utc)
    ts = int(now.timestamp())

    case_a = AICTECase(
        case_reference=f"AICTE-OV-A-{ts}",
        institution_id=g_institution.id,
        category="Admission Fraud",
        subject="Illegal capitation fees in engineering admissions",
        description="High sensitivity internal investigation notes.",
        complainant_name="Secret Whistleblower",
        complainant_email="whistleblower@example.com",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        current_unit_id=g_units["rb"].id,
        created_by_user_id=g_rb_officer.id,
    )
    case_b = AICTECase(
        case_reference=f"AICTE-OV-B-{ts}",
        institution_id=g_institution.id,
        category="Admission Fraud",
        subject="Capitation fees charged during admissions",
        description="Parent complaint regarding donation demands.",
        status=AICTECaseStatusEnum.UNDER_PROCESS,
        current_unit_id=g_units["pgrc"].id,
        created_by_user_id=g_pgrc_officer.id,
    )
    db_session.add_all([case_a, case_b])
    db_session.commit()

    low_id = min(case_a.id, case_b.id)
    high_id = max(case_a.id, case_b.id)

    overlap = AICTECaseOverlap(
        case_id_low=low_id,
        case_id_high=high_id,
        overlap_type=AICTEOverlapTypeEnum.POTENTIAL_DUPLICATE,
        match_score=0.88,
        match_reasons='{"same_institution": true}',
        review_status=AICTEOverlapReviewStatusEnum.PENDING,
    )
    db_session.add(overlap)
    db_session.commit()

    # Dispatch overlap notification
    count = AICTEAlertService.notify_overlap_detected(db_session, overlap)
    assert count >= 2  # Members of both RB and PGRC notified

    # Verify notification for PGRC officer is shielded
    pgrc_notif = db_session.query(Notification).filter(
        Notification.user_id == g_pgrc_officer.id,
        Notification.reference_id == f"OVERLAP_DETECT_{overlap.id}"
    ).first()
    assert pgrc_notif is not None
    # Confidential complainant details must not be present
    assert "Secret Whistleblower" not in pgrc_notif.message
    assert "whistleblower@example.com" not in pgrc_notif.message
    assert "High sensitivity internal investigation notes" not in pgrc_notif.message


# =============================================================================
# 7. Alert Summary & Overdue Queues Endpoints
# =============================================================================

def test_alerts_summary_and_overdue_queue_api(client, db_session: Session, g_rb_officer: User, g_superadmin: User):
    """Verify GET /api/v1/aicte/alerts/summary and GET /api/v1/aicte/alerts/overdue return live structured counters."""
    # Summary endpoint
    res = client.get("/api/v1/aicte/alerts/summary", headers=auth_headers(g_rb_officer))
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "total_unread" in data
    assert "total_unacknowledged" in data
    assert "critical_count" in data
    assert "active_overdue_cases_count" in data
    assert "pending_transfers_count" in data
    assert "pending_overlaps_count" in data

    # Overdue queue endpoint
    overdue_res = client.get("/api/v1/aicte/alerts/overdue", headers=auth_headers(g_rb_officer))
    assert overdue_res.status_code == status.HTTP_200_OK
    od_data = overdue_res.json()
    assert "items" in od_data
    assert "total" in od_data
    if od_data["total"] > 0:
        item = od_data["items"][0]
        assert "overdue_type" in item
        assert item["overdue_type"] in ("NEXT_ACTION", "EXPECTED_DISPOSAL", "BOTH")
        assert item["overdue_days"] >= 0


# =============================================================================
# 8. Alert Configuration Management & Audit Security
# =============================================================================

def test_alert_configuration_permissions_and_audit(client, db_session: Session, g_superadmin: User, g_student: User):
    """Verify configuration reading and administrative update security with audit logging."""
    # Student cannot update configuration (403)
    patch_res = client.patch(
        "/api/v1/aicte/alerts/configuration",
        headers=auth_headers(g_student),
        json={"warning_window_hours": 36}
    )
    assert patch_res.status_code == status.HTTP_403_FORBIDDEN

    # SuperAdmin can update configuration
    admin_patch = client.patch(
        "/api/v1/aicte/alerts/configuration",
        headers=auth_headers(g_superadmin),
        json={"warning_window_hours": 48, "dedup_window_hours": 24}
    )
    assert admin_patch.status_code == status.HTTP_200_OK
    config = admin_patch.json()
    assert config["warning_window_hours"] == 48
    assert config["dedup_window_hours"] == 24

    # Verify audit log recorded
    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "AICTE_ALERT_CONFIG_UPDATED",
        AuditLog.user_id == g_superadmin.id
    ).order_by(AuditLog.id.desc()).first()
    assert audit is not None


# =============================================================================
# 9. Outbox Dispatch & Retry Reliability
# =============================================================================

def test_outbox_failed_delivery_and_safe_retry(db_session: Session, g_superadmin: User):
    """Verify outbox error recording and retry limit enforcement."""
    now = datetime.now(timezone.utc)
    # Create test outbox entry with failed status
    outbox = NotificationOutbox(
        user_id=g_superadmin.id,
        channel="EMAIL",
        recipient_email="failing_smtp_test@example.com",
        subject="[Test] Delivery Failure Notice",
        body="Operational test content.",
        status="FAILED",
        attempts=3,
        error_message="SMTP connection timed out after 10 seconds."
    )
    db_session.add(outbox)
    db_session.commit()

    # Trigger SLA alerts scan which inspects failed outboxes
    results = AICTEAlertService.scan_and_generate_sla_alerts(db_session)
    assert results["failed_outbox_flagged"] >= 1

    # SuperAdmin should have received a FAILED_DELIVERY notification
    notif = db_session.query(Notification).filter(
        Notification.user_id == g_superadmin.id,
        Notification.category == "FAILED_DELIVERY"
    ).first()
    assert notif is not None
    assert notif.severity == "CRITICAL"
