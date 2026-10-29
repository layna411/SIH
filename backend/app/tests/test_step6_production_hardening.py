import pytest
import hashlib
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.role import Role
from app.models.institution import Institution, InstitutionMembership
from app.models.grievance import Grievance
from app.models.category import GrievanceCategory
from app.models.notification import Notification, NotificationOutbox
from app.models.email_verification import EmailVerificationToken
from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum
from app.core.security import hash_password, create_access_token
from app.services.email_service import email_service
from app.services.notification_service import create_notification, dispatch_pending_outbox
from app.services.escalation_service import escalation_service
from app.api.v1.analytics import sanitize_csv_value

def get_or_create_category(db, code="AUDIT_CAT", name="Audit Category"):
    cat = db.query(GrievanceCategory).filter(GrievanceCategory.code == code).first()
    if not cat:
        cat = GrievanceCategory(code=code, name=name, default_sla_days=7, is_active=True)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat

def create_user(db, email, role_name=UserRoleEnum.STUDENT, full_name="Test Student", is_verified=True, is_email_verified=False):
    role = db.query(Role).filter(Role.name == role_name.value if hasattr(role_name, 'value') else role_name).first()
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        full_name=full_name,
        is_active=True,
        is_verified=is_verified,
        is_email_verified=is_email_verified,
        default_role=role_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_institution(db, name="Audit University", code="AUDIT_U", state="Delhi"):
    inst = Institution(
        name=name,
        code=code,
        state=state,
        district="New Delhi",
        city="New Delhi",
        contact_email=f"info@{code.lower()}.edu",
        institution_type="COLLEGE",
        is_active=True,
        is_verified=True
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst

def get_auth_headers(user):
    token = create_access_token(subject=user.id, extra_claims={"role": user.default_role.value if hasattr(user.default_role, 'value') else user.default_role, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

# 1. Email Verification Token Generation, Expiration, Single-use, Replay Rejection
def test_email_verification_token_lifecycle(db_session, client):
    user = create_user(db_session, "verify_student@audit.edu")

    # Generate token
    raw_token, token_record = email_service.generate_verification_token(db_session, user)
    assert raw_token is not None
    assert token_record.is_used is False
    assert token_record.token_hash == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Verify successfully
    verify_resp = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "success"

    db_session.refresh(user)
    db_session.refresh(token_record)
    assert user.is_email_verified is True
    assert token_record.is_used is True
    assert token_record.used_at is not None

    # Replay attempt fails (single-use constraint)
    replay_resp = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert replay_resp.status_code == 400
    assert "already been used" in replay_resp.json()["detail"].lower()

# 2. Expired Verification Token Rejection
def test_expired_verification_token_rejected(db_session, client):
    user = create_user(db_session, "expired_student@audit.edu")
    raw_token, token_record = email_service.generate_verification_token(db_session, user)

    # Backdate expiration
    token_record.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.commit()

    resp = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()

# 3. Resend Verification Cooldown and Enumeration Protection
def test_resend_verification_cooldown_and_enumeration(db_session, client):
    user = create_user(db_session, "cooldown_student@audit.edu")

    # First request succeeds
    resp1 = client.post("/api/v1/auth/resend-verification", json={"email": user.email})
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "success"

    # Rapid second request triggers 429 cooldown
    resp2 = client.post("/api/v1/auth/resend-verification", json={"email": user.email})
    assert resp2.status_code == 429
    assert "wait" in resp2.json()["detail"].lower()

    # Non-existent user returns generic response to prevent account enumeration
    ghost_resp = client.post("/api/v1/auth/resend-verification", json={"email": "nonexistent_99@test.edu"})
    assert ghost_resp.status_code == 200
    assert ghost_resp.json()["status"] == "success"

# 4. Email Verification Status Endpoint
def test_verification_status_endpoint(db_session, client):
    user = create_user(db_session, "status_student@audit.edu", is_email_verified=False)
    headers = get_auth_headers(user)

    status_resp = client.get("/api/v1/auth/verification-status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["is_email_verified"] is False

    user.is_email_verified = True
    db_session.commit()

    status_resp2 = client.get("/api/v1/auth/verification-status", headers=headers)
    assert status_resp2.status_code == 200
    assert status_resp2.json()["is_email_verified"] is True

# 5. Persistent Notifications: Ownership, Unread Count, Pagination, and Mark Read
def test_notifications_ownership_and_pagination(db_session, client):
    student_a = create_user(db_session, "student_a_notif@audit.edu")
    student_b = create_user(db_session, "student_b_notif@audit.edu")

    # Create notifications for student A
    for i in range(5):
        create_notification(
            db=db_session,
            user_id=student_a.id,
            title=f"Notification A-{i+1}",
            message=f"Message body {i+1}",
            notification_type="STATUS_UPDATE",
            email_notify=False
        )

    # Create notification for student B
    notif_b = create_notification(
        db=db_session,
        user_id=student_b.id,
        title="Notification B-1",
        message="Message body for B",
        notification_type="STATUS_UPDATE",
        email_notify=False
    )

    headers_a = get_auth_headers(student_a)
    headers_b = get_auth_headers(student_b)

    # Student A unread count is 5
    count_resp = client.get("/api/v1/notifications/unread-count", headers=headers_a)
    assert count_resp.status_code == 200
    assert count_resp.json()["unread_count"] == 5

    # Pagination test: fetch limit=2
    list_resp = client.get("/api/v1/notifications?limit=2&skip=0", headers=headers_a)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 2

    # Recipient ownership isolation: Student A cannot mark Student B's notification as read
    unauth_read = client.put(f"/api/v1/notifications/{notif_b.id}/read", headers=headers_a)
    assert unauth_read.status_code == 404

    # Student A marks one notification as read
    first_notif_id = items[0]["id"]
    mark_resp = client.put(f"/api/v1/notifications/{first_notif_id}/read", headers=headers_a)
    assert mark_resp.status_code == 200
    assert mark_resp.json()["is_read"] is True

    # Unread count decremented to 4
    count_resp2 = client.get("/api/v1/notifications/unread-count", headers=headers_a)
    assert count_resp2.json()["unread_count"] == 4

    # Mark all read for Student A
    read_all_resp = client.put("/api/v1/notifications/read-all", headers=headers_a)
    assert read_all_resp.status_code == 200
    assert read_all_resp.json()["marked_count"] == 4

    # Verify zero unread
    count_resp3 = client.get("/api/v1/notifications/unread-count", headers=headers_a)
    assert count_resp3.json()["unread_count"] == 0

# 6. Transactional Outbox Delivery and Retry Mechanics
def test_transactional_outbox_processing(db_session, client):
    user = create_user(db_session, "outbox_student@audit.edu")

    # Create notification with email notification requested
    notif = create_notification(
        db=db_session,
        user_id=user.id,
        title="Grievance Received",
        message="Your grievance GRV-999 has been recorded.",
        notification_type="SUBMITTED",
        email_notify=True
    )

    # Verify outbox record created transactionally
    outbox_entries = db_session.query(NotificationOutbox).filter(
        NotificationOutbox.notification_id == notif.id
    ).all()
    assert len(outbox_entries) == 1
    entry = outbox_entries[0]
    assert entry.status == "PENDING"
    assert entry.recipient_email == user.email

    # Dispatch outbox
    dispatched = dispatch_pending_outbox(db_session, max_batch=10)
    assert dispatched >= 1

    db_session.refresh(entry)
    assert entry.status in ["SENT", "FAILED"]
    assert entry.attempts >= 1

# 7. SLA Warnings Process without premature escalation
def test_sla_warnings_generation(db_session):
    inst = create_institution(db_session, "SLA Warning Inst", "SLA_WARN_U")
    student = create_user(db_session, "sla_warn_student@audit.edu")

    # Grievance with deadline approaching (e.g. deadline is 12 hours from now)
    now = datetime.now(timezone.utc)
    deadline_soon = now + timedelta(hours=12)

    cat = get_or_create_category(db_session, code="CAT_WARN", name="Warning Category")
    grievance = Grievance(
        reference_number="GRV-WARN-001",
        title="Delay in library book issuance",
        description="Book request pending for a long time.",
        status=GrievanceStatusEnum.UNDER_REVIEW,
        priority=GrievancePriorityEnum.NORMAL,
        student_id=student.id,
        institution_id=inst.id,
        category_id=cat.id,
        due_date=deadline_soon,
        sla_warning_sent=False
    )
    db_session.add(grievance)
    db_session.commit()

    # Run SLA warning scan
    warned_refs = escalation_service.process_sla_warnings(db_session)
    assert "GRV-WARN-001" in warned_refs

    db_session.refresh(grievance)
    assert grievance.sla_warning_sent is True
    # Verify grievance status remains UNDER_REVIEW (no premature escalation)
    assert grievance.status == GrievanceStatusEnum.UNDER_REVIEW

    # Second run should be idempotent (no duplicate warning)
    warned_refs_second = escalation_service.process_sla_warnings(db_session)
    assert "GRV-WARN-001" not in warned_refs_second

# 8. SLA Overdue Escalations
def test_sla_overdue_escalations(db_session):
    inst = create_institution(db_session, "SLA Overdue Inst", "SLA_OVERDUE_U")
    student = create_user(db_session, "sla_overdue_student@audit.edu")
    cat = get_or_create_category(db_session, code="CAT_OVERDUE", name="Overdue Category")

    # Grievance with past deadline
    past_deadline = datetime.now(timezone.utc) - timedelta(hours=5)

    grievance = Grievance(
        reference_number="GRV-OVERDUE-001",
        title="Urgent laboratory safety concern",
        description="Chemical fume hood not working.",
        status=GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
        priority=GrievancePriorityEnum.URGENT,
        student_id=student.id,
        institution_id=inst.id,
        category_id=cat.id,
        due_date=past_deadline
    )
    db_session.add(grievance)
    db_session.commit()

    # Process overdue escalations
    escalated_refs = escalation_service.process_overdue_escalations(db_session)
    assert "GRV-OVERDUE-001" in escalated_refs

    db_session.refresh(grievance)
    assert grievance.status == GrievanceStatusEnum.ESCALATED

    # Idempotent: re-running does not duplicate escalation
    escalated_second = escalation_service.process_overdue_escalations(db_session)
    assert "GRV-OVERDUE-001" not in escalated_second

# 9. CSV Formula Injection Sanitization
def test_csv_formula_injection_defense():
    dangerous_inputs = [
        '=cmd|"/C calc"!A0',
        '+1234567890',
        '-5+2',
        '@SUM(1,2)',
        '\tDangerousTab',
        '\rDangerousCR'
    ]

    for val in dangerous_inputs:
        sanitized = sanitize_csv_value(val)
        assert sanitized.startswith("'"), f"Failed to escape dangerous character in: {val}"

    safe_input = "Standard grievance title without formulas"
    assert sanitize_csv_value(safe_input) == safe_input

# 10. Analytics and Export Tenant Isolation
def test_analytics_cross_tenant_isolation(db_session, client):
    inst_a = create_institution(db_session, "College Alpha", "CLG_ALPHA")
    inst_b = create_institution(db_session, "College Beta", "CLG_BETA")

    head_a = create_user(db_session, "head_alpha@audit.edu", role_name=UserRoleEnum.INSTITUTION_HEAD)
    membership_a = InstitutionMembership(
        user_id=head_a.id,
        institution_id=inst_a.id,
        role=UserRoleEnum.INSTITUTION_HEAD,
        is_active=True
    )
    db_session.add(membership_a)
    db_session.commit()

    headers_head_a = get_auth_headers(head_a)

    # Querying own institution stats succeeds
    resp_own = client.get(f"/api/v1/analytics/dashboard?institution_id={inst_a.id}", headers=headers_head_a)
    assert resp_own.status_code == 200

    # Querying foreign institution stats receives 403 Forbidden
    resp_foreign = client.get(f"/api/v1/analytics/dashboard?institution_id={inst_b.id}", headers=headers_head_a)
    assert resp_foreign.status_code == 403

    # Exporting foreign institution grievances receives 403 Forbidden
    resp_export_foreign = client.get(f"/api/v1/analytics/export/csv?institution_id={inst_b.id}", headers=headers_head_a)
    assert resp_export_foreign.status_code == 403

# 11. Security Headers and Safeguards
def test_security_headers_and_safeguards(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

# 12. Rate Limiting on Sensitive Auth Routes
def test_auth_rate_limiting_enforcement(client):
    headers = {"X-Test-Rate-Limit": "true"}

    # Repeated login attempts hit rate limit
    got_429 = False
    for _ in range(15):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimit_test@audit.edu", "password": "WrongPassword123!"},
            headers=headers
        )
        if resp.status_code == 429:
            got_429 = True
            break

    assert got_429 is True, "Rate limiter did not throttle excessive authentication requests."

# 13. System Scheduler Telemetry and Manual Trigger
def test_scheduler_telemetry_and_manual_trigger(db_session, client):
    super_admin = create_user(db_session, "superadmin_scheduler@audit.edu", role_name=UserRoleEnum.SUPER_ADMIN)
    student = create_user(db_session, "student_scheduler@audit.edu", role_name=UserRoleEnum.STUDENT)

    headers_admin = get_auth_headers(super_admin)
    headers_student = get_auth_headers(student)

    # Student cannot view scheduler telemetry
    student_resp = client.get("/api/v1/system/scheduler-status", headers=headers_student)
    assert student_resp.status_code == 403

    # Super Admin can view scheduler telemetry
    admin_resp = client.get("/api/v1/system/scheduler-status", headers=headers_admin)
    assert admin_resp.status_code == 200
    status_data = admin_resp.json()
    assert "is_enabled" in status_data
    assert "total_runs" in status_data

    # Super Admin can trigger manual scheduler cycle
    run_resp = client.post("/api/v1/system/scheduler-run", headers=headers_admin)
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "SUCCESS"
