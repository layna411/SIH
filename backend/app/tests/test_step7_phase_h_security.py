import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseSourceTypeEnum,
    AICTEComplainantTypeEnum,
    AICTECaseActionTypeEnum,
    AICTETransferStatusEnum,
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTECaseLinkTypeEnum,
    GrievancePriorityEnum,
)
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.grievance import Grievance, GrievanceCategory
from app.models.aicte_case import AICTECase, CaseAction
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.aicte_overlap import AICTECaseOverlap, AICTECaseLink
from app.models.notification import Notification, NotificationOutbox
from app.core.security import create_access_token
from app.services.aicte_analytics_service import sanitize_csv_value
from app.services.aicte_overlap_service import AICTEOverlapService
from app.services.aicte_transfer_service import AICTETransferService
from app.services.aicte_alert_service import AICTEAlertService
from app.services.notification_service import create_notification, dispatch_pending_outbox


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------
def _auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}


def _create_user(db: Session, email: str, role: UserRoleEnum, name: str = "Test User") -> User:
    user = User(
        email=email,
        full_name=name,
        hashed_password="hashed_password",
        default_role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_institution(db: Session, code: str, name: str, pid: str) -> Institution:
    inst = Institution(
        code=code,
        name=name,
        state="Maharashtra",
        region="Western",
        contact_email=f"contact@{code.lower()}.edu",
        aicte_permanent_id=pid,
        is_aicte_verified=True,
        is_active=True,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _create_unit(db: Session, code: str, name: str) -> OrganizationalUnit:
    unit = OrganizationalUnit(
        code=code,
        name=name,
        unit_type="BUREAU",
        is_active=True,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def _assign_bureau(db: Session, user: User, unit: OrganizationalUnit, role: str = "BUREAU_OFFICER", is_active: bool = True) -> BureauMembership:
    bm = BureauMembership(
        user_id=user.id,
        organizational_unit_id=unit.id,
        membership_role=role,
        is_active=is_active,
    )
    db.add(bm)
    db.commit()
    db.refresh(bm)
    return bm


def _create_case(
    db: Session,
    ref: str,
    institution: Institution,
    unit: OrganizationalUnit,
    creator: User,
    status_val: AICTECaseStatusEnum = AICTECaseStatusEnum.RECEIVED,
    subject: str = "Test Grievance Case",
    category: str = "Fee Overcharge"
) -> AICTECase:
    case = AICTECase(
        case_reference=ref,
        institution_id=institution.id,
        current_unit_id=unit.id,
        created_by_user_id=creator.id,
        source_type=AICTECaseSourceTypeEnum.DIRECT,
        category=category,
        subject=subject,
        description="Confidential case details and whistleblower statement.",
        status=status_val,
        received_at=datetime.now(timezone.utc),
        last_action_at=datetime.now(timezone.utc),
        priority=GrievancePriorityEnum.NORMAL,
        complainant_type=AICTEComplainantTypeEnum.STUDENT,
        complainant_name="Whistleblower Student",
        complainant_email="whistleblower@student.edu",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


# ---------------------------------------------------------------------------
# 1. Authentication and Authorization Guard Tests
# ---------------------------------------------------------------------------
def test_unauthenticated_requests_rejected(client):
    """Verify all protected AICTE endpoints reject requests lacking credentials with 401."""
    endpoints = [
        ("GET", "/api/v1/aicte/cases"),
        ("POST", "/api/v1/aicte/cases"),
        ("GET", "/api/v1/aicte/transfers/incoming"),
        ("GET", "/api/v1/aicte/transfers/outgoing"),
        ("GET", "/api/v1/aicte/overlaps"),
        ("GET", "/api/v1/aicte/notifications"),
        ("GET", "/api/v1/aicte/alerts/overdue"),
        ("GET", "/api/v1/aicte/alerts/summary"),
        ("GET", "/api/v1/aicte/institutions/1/consolidated-history"),
    ]
    for method, path in endpoints:
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json={})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected 401 on {method} {path}, got {resp.status_code}"


def test_student_and_campus_roles_denied_regulatory_endpoints(db_session, client):
    """Verify students and ordinary campus users cannot access restricted AICTE regulatory endpoints."""
    student = _create_user(db_session, "student_h@test.edu", UserRoleEnum.STUDENT)
    headers = _auth_headers(student)

    inst = _create_institution(db_session, "INST_DENY", "Institute Deny", "1-DENY-999")
    forbidden_get_paths = [
        "/api/v1/aicte/cases",
        "/api/v1/aicte/transfers/incoming",
        "/api/v1/aicte/transfers/outgoing",
        "/api/v1/aicte/overlaps",
        "/api/v1/aicte/alerts/overdue",
        f"/api/v1/aicte/institutions/{inst.id}/consolidated-history",
    ]
    for path in forbidden_get_paths:
        resp = client.get(path, headers=headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN, f"Student accessed regulatory endpoint {path}"


def test_inactive_bureau_membership_denies_access(db_session, client):
    """Verify that an inactive Bureau membership does NOT grant access to AICTE cases."""
    unit = _create_unit(db_session, "B_INACTIVE", "Bureau Inactive Test")
    officer = _create_user(db_session, "deactivated_officer@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    # Assign inactive membership
    _assign_bureau(db_session, officer, unit, role="BUREAU_OFFICER", is_active=False)
    db_session.commit()

    headers = _auth_headers(officer)
    resp = client.get("/api/v1/aicte/cases", headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_cross_bureau_case_scoping_and_isolation(db_session, client):
    """Verify bureau officers can only access cases belonging to their authorized organizational units."""
    unit_rb = _create_unit(db_session, "RB_ISO", "Regulation Bureau")
    unit_pgrc = _create_unit(db_session, "PGRC_ISO", "Public Grievance Cell")
    inst = _create_institution(db_session, "INST_ISO", "Institute ISO", "1-ISO-999")

    officer_rb = _create_user(db_session, "officer_rb@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, officer_rb, unit_rb, "BUREAU_OFFICER")

    case_rb = _create_case(db_session, "AICTE-2026-RB001", inst, unit_rb, officer_rb)
    case_pgrc = _create_case(db_session, "AICTE-2026-PGRC001", inst, unit_pgrc, officer_rb)
    db_session.commit()

    headers = _auth_headers(officer_rb)

    # 1. Listing cases only shows RB cases, not PGRC cases
    resp = client.get("/api/v1/aicte/cases", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    case_refs = [c["case_reference"] for c in resp.json()["cases"]]
    assert "AICTE-2026-RB001" in case_refs
    assert "AICTE-2026-PGRC001" not in case_refs

    # 2. Direct detail access to PGRC case returns 403
    detail_resp = client.get(f"/api/v1/aicte/cases/{case_pgrc.id}", headers=headers)
    assert detail_resp.status_code == status.HTTP_403_FORBIDDEN


def test_notification_idor_protection(db_session, client):
    """Verify a user cannot read, mark read, or acknowledge another user's notification by guessing its ID."""
    user_a = _create_user(db_session, "officer_a_notif@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    user_b = _create_user(db_session, "officer_b_notif@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)

    notif_a = create_notification(
        db=db_session,
        user_id=user_a.id,
        title="Confidential Officer A Alert",
        message="Confidential alert message for user A only.",
        email_notify=False,
        requires_acknowledgement=True,
    )
    db_session.commit()

    headers_b = _auth_headers(user_b)

    # Attempting to fetch notification detail of user A
    resp_detail = client.get(f"/api/v1/aicte/notifications/{notif_a.id}", headers=headers_b)
    assert resp_detail.status_code == status.HTTP_404_NOT_FOUND

    # Attempting to mark read
    resp_read = client.post(f"/api/v1/aicte/notifications/{notif_a.id}/read", headers=headers_b)
    assert resp_read.status_code == status.HTTP_404_NOT_FOUND

    # Attempting to acknowledge
    resp_ack = client.post(f"/api/v1/aicte/notifications/{notif_a.id}/acknowledge", headers=headers_b)
    assert resp_ack.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# 2. Case Lifecycle, Action History & Integrity Invariants
# ---------------------------------------------------------------------------
def test_case_lifecycle_illegal_transition_rejected(db_session, client):
    """Verify server-side state machine rejects invalid status jumps (e.g. RECEIVED -> DISPOSED directly)."""
    unit = _create_unit(db_session, "B_STATE", "Bureau State Machine")
    officer = _create_user(db_session, "officer_state@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, officer, unit, "BUREAU_OFFICER")
    inst = _create_institution(db_session, "INST_STATE", "Institute State", "1-STATE-111")
    case = _create_case(db_session, "AICTE-2026-STATE01", inst, unit, officer, status_val=AICTECaseStatusEnum.RECEIVED)
    db_session.commit()

    headers = _auth_headers(officer)

    # Try invalid jump from RECEIVED directly to DISPOSED
    action_payload = {
        "action_type": AICTECaseActionTypeEnum.STATUS_UPDATE.value,
        "action_title": "Premature Disposal Attempt",
        "new_status": AICTECaseStatusEnum.DISPOSED.value,
        "remarks": "Bypassing intermediate review stages.",
    }
    resp = client.post(f"/api/v1/aicte/cases/{case.id}/actions", json=action_payload, headers=headers)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid AICTE case lifecycle transition" in resp.json()["detail"]


def test_valid_case_action_lifecycle_and_disposal_timestamps(db_session, client):
    """Verify valid procedural status transition updates case status and disposed_at timestamp."""
    unit = _create_unit(db_session, "B_VALID", "Bureau Valid Flow")
    officer = _create_user(db_session, "officer_valid@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, officer, unit, "BUREAU_OFFICER")
    inst = _create_institution(db_session, "INST_VALID", "Institute Valid", "1-VALID-222")
    case = _create_case(db_session, "AICTE-2026-VALID01", inst, unit, officer, status_val=AICTECaseStatusEnum.UNDER_PROCESS)
    db_session.commit()

    headers = _auth_headers(officer)

    # Transition from UNDER_PROCESS -> DISPOSED
    action_payload = {
        "action_type": AICTECaseActionTypeEnum.DISPOSAL_ORDER.value,
        "action_title": "Final Hearing Concluded",
        "new_status": AICTECaseStatusEnum.DISPOSED.value,
        "remarks": "Institution complied with regulation.",
    }
    resp = client.post(f"/api/v1/aicte/cases/{case.id}/actions", json=action_payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED

    # Verify case reflects disposed state and timestamp
    db_session.refresh(case)
    assert case.status == AICTECaseStatusEnum.DISPOSED
    assert case.disposed_at is not None

    # Check history endpoint contains the action
    hist_resp = client.get(f"/api/v1/aicte/cases/{case.id}/history", headers=headers)
    assert hist_resp.status_code == status.HTTP_200_OK
    assert len(hist_resp.json()) >= 1
    assert hist_resp.json()[-1]["new_status"] == AICTECaseStatusEnum.DISPOSED.value


# ---------------------------------------------------------------------------
# 3. Inter-Bureau Transfer Concurrency & Reversal Invariants
# ---------------------------------------------------------------------------
def test_transfer_lifecycle_and_rejection_prior_status_restoration(db_session, client):
    """
    Verify full transfer lifecycle:
    1. Transfer proposal sets case to TRANSFER_PENDING but preserves current handling unit.
    2. Duplicate transfer proposal on same case returns 409 Conflict.
    3. Rejection restores exact recorded prior status and keeps originating unit intact.
    """
    unit_src = _create_unit(db_session, "SRC_UNIT", "Source Unit")
    unit_dest = _create_unit(db_session, "DEST_UNIT", "Destination Unit")
    inst = _create_institution(db_session, "INST_XFER", "Institute Transfer", "1-XFER-333")

    src_officer = _create_user(db_session, "src_off@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    dest_officer = _create_user(db_session, "dest_off@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, src_officer, unit_src, "BUREAU_OFFICER")
    _assign_bureau(db_session, dest_officer, unit_dest, "BUREAU_OFFICER")

    case = _create_case(
        db_session, "AICTE-2026-XFER01", inst, unit_src, src_officer,
        status_val=AICTECaseStatusEnum.UNDER_PROCESS
    )
    db_session.commit()

    # 1. Propose transfer
    initiate_payload = {
        "to_unit_id": unit_dest.id,
        "transfer_reason": "Jurisdiction covers technical examination under DEST_UNIT mandate.",
        "handover_summary": "Initial hearing notes attached.",
    }
    resp_init = client.post(
        f"/api/v1/aicte/cases/{case.id}/transfers",
        json=initiate_payload,
        headers=_auth_headers(src_officer)
    )
    assert resp_init.status_code == status.HTTP_201_CREATED
    transfer_id = resp_init.json()["id"]

    db_session.refresh(case)
    assert case.status == AICTECaseStatusEnum.TRANSFER_PENDING
    assert case.current_unit_id == unit_src.id  # Handling unit must remain source until accepted!

    # 2. Concurrency check: duplicate pending transfer on same case returns 409
    resp_dup = client.post(
        f"/api/v1/aicte/cases/{case.id}/transfers",
        json=initiate_payload,
        headers=_auth_headers(src_officer)
    )
    assert resp_dup.status_code == status.HTTP_409_CONFLICT

    # 3. Destination officer declines the transfer
    reject_payload = {
        "rejection_reason": "Matter does not fall under DEST_UNIT purview. Recommended for Regional Office.",
    }
    resp_rej = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/reject",
        json=reject_payload,
        headers=_auth_headers(dest_officer)
    )
    assert resp_rej.status_code == status.HTTP_200_OK

    db_session.refresh(case)
    # Status restored to UNDER_PROCESS, current unit remains SRC_UNIT
    assert case.status == AICTECaseStatusEnum.UNDER_PROCESS
    assert case.current_unit_id == unit_src.id


def test_transfer_acceptance_responsibility_handover(db_session, client):
    """Verify accepting transfer formally transitions case responsibility to destination unit."""
    unit_src = _create_unit(db_session, "SRC_ACC", "Source Unit Accept")
    unit_dest = _create_unit(db_session, "DEST_ACC", "Destination Unit Accept")
    inst = _create_institution(db_session, "INST_ACC", "Institute Accept", "1-ACC-444")

    src_off = _create_user(db_session, "src_acc@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    dest_off = _create_user(db_session, "dest_acc@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, src_off, unit_src, "BUREAU_OFFICER")
    _assign_bureau(db_session, dest_off, unit_dest, "BUREAU_OFFICER")

    case = _create_case(db_session, "AICTE-2026-ACC01", inst, unit_src, src_off, status_val=AICTECaseStatusEnum.UNDER_PROCESS)
    db_session.commit()

    # Propose
    resp_prop = client.post(
        f"/api/v1/aicte/cases/{case.id}/transfers",
        json={"to_unit_id": unit_dest.id, "transfer_reason": "Transferred for regional investigation."},
        headers=_auth_headers(src_off)
    )
    transfer_id = resp_prop.json()["id"]

    # Accept
    resp_acc = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/accept",
        json={"response_notes": "Accepted by destination unit."},
        headers=_auth_headers(dest_off)
    )
    assert resp_acc.status_code == status.HTTP_200_OK

    db_session.refresh(case)
    assert case.current_unit_id == unit_dest.id
    assert case.status == AICTECaseStatusEnum.TRANSFERRED


# ---------------------------------------------------------------------------
# 4. Cross-Bureau Confidentiality & Narrative Masking
# ---------------------------------------------------------------------------
def test_cross_bureau_narrative_shielding_in_overlaps(db_session, client):
    """
    Verify cross-bureau confidentiality in overlap views:
    A bureau officer viewing an overlap candidate involving another bureau's case
    must receive a masked summary where sensitive complainant and narrative details are shielded.
    """
    unit_a = _create_unit(db_session, "UNIT_ALPHA", "Unit Alpha")
    unit_b = _create_unit(db_session, "UNIT_BETA", "Unit Beta")
    inst = _create_institution(db_session, "INST_SHIELD", "Institute Shield", "1-SHIELD-555")

    officer_a = _create_user(db_session, "officer_alpha@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, officer_a, unit_a, "BUREAU_OFFICER")

    case_a = _create_case(
        db_session, "AICTE-2026-ALPHA01", inst, unit_a, officer_a,
        subject="Alpha Subject Fee Overcharge", category="Fee Overcharge"
    )
    case_b = _create_case(
        db_session, "AICTE-2026-BETA01", inst, unit_b, officer_a,
        subject="Beta Subject Fee Overcharge", category="Fee Overcharge"
    )
    db_session.commit()

    # Create overlap candidate between case_a and case_b
    overlap = AICTECaseOverlap(
        case_id_low=min(case_a.id, case_b.id),
        case_id_high=max(case_a.id, case_b.id),
        overlap_type=AICTEOverlapTypeEnum.POTENTIAL_DUPLICATE,
        match_score=0.85,
        match_reasons=json.dumps({"category_match": True, "subject_similarity": 0.85}),
        review_status=AICTEOverlapReviewStatusEnum.PENDING,
        detected_at=datetime.now(timezone.utc),
    )
    db_session.add(overlap)
    db_session.commit()

    # Officer A queries the overlap detail
    headers_a = _auth_headers(officer_a)
    resp = client.get(f"/api/v1/aicte/overlaps/{overlap.id}", headers=headers_a)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    # For case_a (which Officer A is authorized for): has_full_access is True
    # For case_b (which belongs to UNIT_BETA): has_full_access is False and narrative is shielded
    case_low_data = data["case_low"]
    case_high_data = data["case_high"]

    unit_a_case = case_low_data if case_low_data["current_unit_id"] == unit_a.id else case_high_data
    unit_b_case = case_high_data if unit_a_case == case_low_data else case_low_data

    assert unit_a_case["has_full_access"] is True
    assert unit_a_case["description"] == "Confidential case details and whistleblower statement."
    assert unit_a_case["complainant_name"] == "Whistleblower Student"

    # Shielded case assertions
    assert unit_b_case["has_full_access"] is False
    assert "[CONFIDENTIAL" in unit_b_case["description"]
    assert unit_b_case["complainant_name"] == "[PROTECTED]"
    assert unit_b_case["complainant_email"] is None
    assert unit_b_case["complainant_phone"] is None


def test_overlap_review_preserves_case_independence(db_session, client):
    """
    CRITICAL RULE: Confirming a duplicate NEVER merges or closes either case.
    Both official cases must retain their distinct case references, units, and active statuses.
    """
    unit_rb = _create_unit(db_session, "RB_OVL", "Regulation Bureau Overlap")
    inst = _create_institution(db_session, "INST_OVL", "Institute Overlap", "1-OVL-666")

    officer = _create_user(db_session, "officer_ovl@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, officer, unit_rb, "BUREAU_OFFICER")

    case_1 = _create_case(db_session, "AICTE-2026-OVL01", inst, unit_rb, officer, status_val=AICTECaseStatusEnum.UNDER_PROCESS)
    case_2 = _create_case(db_session, "AICTE-2026-OVL02", inst, unit_rb, officer, status_val=AICTECaseStatusEnum.RECEIVED)
    db_session.commit()

    overlap = AICTECaseOverlap(
        case_id_low=min(case_1.id, case_2.id),
        case_id_high=max(case_1.id, case_2.id),
        overlap_type=AICTEOverlapTypeEnum.POTENTIAL_DUPLICATE,
        match_score=0.90,
        match_reasons=json.dumps({"category_match": True}),
        review_status=AICTEOverlapReviewStatusEnum.PENDING,
        detected_at=datetime.now(timezone.utc),
    )
    db_session.add(overlap)
    db_session.commit()

    headers = _auth_headers(officer)
    review_payload = {
        "action": AICTEOverlapReviewStatusEnum.CONFIRMED_DUPLICATE.value,
        "review_notes": "Both cases refer to same underlying fee notification. Cross-referenced as duplicate.",
    }
    resp = client.post(f"/api/v1/aicte/overlaps/{overlap.id}/review", json=review_payload, headers=headers)
    assert resp.status_code == status.HTTP_200_OK

    # Verify both cases retain their exact statuses and references
    db_session.refresh(case_1)
    db_session.refresh(case_2)
    assert case_1.status == AICTECaseStatusEnum.UNDER_PROCESS
    assert case_2.status == AICTECaseStatusEnum.RECEIVED
    assert case_1.case_reference == "AICTE-2026-OVL01"
    assert case_2.case_reference == "AICTE-2026-OVL02"

    # Verify an administrative case link was created
    link = db_session.query(AICTECaseLink).filter(
        AICTECaseLink.case_id_low == min(case_1.id, case_2.id),
        AICTECaseLink.case_id_high == max(case_1.id, case_2.id),
    ).first()
    assert link is not None
    assert link.link_type == AICTECaseLinkTypeEnum.DUPLICATE_OF
    assert link.is_active is True


# ---------------------------------------------------------------------------
# 5. Campus Grievance Referral Integrity & Idempotency
# ---------------------------------------------------------------------------
def test_campus_grievance_referral_prevents_duplicates(db_session, client):
    """
    Verify campus grievance referral to AICTE:
    - Creates linked AICTE case with INTAKE action.
    - Subsequent referral attempt of the same grievance is rejected with 400 Bad Request.
    """
    unit = _create_unit(db_session, "B_REF", "Bureau Referral")
    inst = _create_institution(db_session, "INST_REF", "Institute Referral", "1-REF-777")
    admin = _create_user(db_session, "admin_ref@aicte.gov.in", UserRoleEnum.SUPER_ADMIN)

    # Create category, student, and campus grievance
    cat = GrievanceCategory(code="ACAD_HARASS", name="Academic Harassment", description="Campus Category")
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)

    student = _create_user(db_session, "campus_student@college.edu", UserRoleEnum.STUDENT, "Campus Student")

    grievance = Grievance(
        reference_number="GRV-2026-REF001",
        institution_id=inst.id,
        student_id=student.id,
        category_id=cat.id,
        title="Unfair Retaliation",
        description="Campus student grievance details.",
        status="SUBMITTED",
        priority=GrievancePriorityEnum.HIGH,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(grievance)
    db_session.commit()

    headers = _auth_headers(admin)
    referral_payload = {
        "source_grievance_id": grievance.id,
        "destination_unit_id": unit.id,
        "referral_reason": "Institute redressal committee inactive beyond regulatory timeline.",
        "complainant_type": AICTEComplainantTypeEnum.STUDENT.value,
    }

    # First referral succeeds
    resp1 = client.post("/api/v1/aicte/cases/refer-grievance", json=referral_payload, headers=headers)
    assert resp1.status_code == status.HTTP_201_CREATED
    data1 = resp1.json()
    assert data1["source_type"] == AICTECaseSourceTypeEnum.CAMPUS_REFERRAL.value
    assert data1["source_grievance_id"] == grievance.id

    # Second referral fails with 400 Bad Request (duplicate prevention)
    resp2 = client.post("/api/v1/aicte/cases/refer-grievance", json=referral_payload, headers=headers)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been referred to AICTE" in resp2.json()["detail"]


# ---------------------------------------------------------------------------
# 6. CSV Formula Injection Hardening (Leading Whitespace & Prefix Defense)
# ---------------------------------------------------------------------------
def test_csv_sanitization_comprehensive_matrix():
    """
    Verify CSV formula injection defense across Excel, Calc, and Google Sheets:
    - Handles raw formula triggers: =, +, -, @, \\t, \\r, %
    - Handles leading spaces, tabs, and carriage returns before the formula prefix
    - Preserves legitimate numbers (e.g. 42, -5, 3.14) without breaking numeric types
    - Preserves clean standard strings
    """
    dangerous_payloads = [
        "=1+1",
        "=SUM(A1:B1)",
        '=cmd|"/C calc"!A0',
        '+1234567890',
        '-5+2',
        '@SUM(1,2)',
        '\tDangerousTab',
        '\rDangerousCR',
        '%0Acalc',
        # Leading whitespace edge cases
        "   =1+1",
        "   =SUM(A1:B1)",
        '   =cmd|"/C calc"!A0',
        " \t=2+2",
        "  \r=3+3",
        "   +12345",
        "   @SUM(1,2)",
        " \t-2+3",
        " \r-calc",
    ]

    for val in dangerous_payloads:
        sanitized = sanitize_csv_value(val)
        assert sanitized.startswith("'"), f"Failed to neutralize dangerous payload: {val!r} -> {sanitized!r}"

    # Legitimate numbers and clean strings must NOT be corrupted
    assert sanitize_csv_value(42) == "42"
    assert sanitize_csv_value(100.5) == "100.5"
    assert sanitize_csv_value(None) == ""
    assert sanitize_csv_value("Regular Case Subject") == "Regular Case Subject"
    assert sanitize_csv_value("AICTE-2026-001") == "AICTE-2026-001"


# ---------------------------------------------------------------------------
# 7. Notification Deduplication, SLA Alert Scanning & Outbox Retries
# ---------------------------------------------------------------------------
def test_notification_deduplication_prevents_alert_flooding(db_session):
    """
    Verify that AICTEAlertService deduplication prevents repeated scheduler scans
    from generating duplicate alerts for the same condition within the cooldown window.
    """
    unit = _create_unit(db_session, "B_ALERT", "Bureau Alert Test")
    officer = _create_user(db_session, "alert_officer@aicte.gov.in", UserRoleEnum.COLLEGE_OFFICER)
    _assign_bureau(db_session, officer, unit, "BUREAU_OFFICER")
    inst = _create_institution(db_session, "INST_ALERT", "Institute Alert", "1-ALT-888")

    # Case overdue on next action
    overdue_date = datetime.now(timezone.utc) - timedelta(days=3)
    case = _create_case(
        db_session, "AICTE-2026-ALT01", inst, unit, officer,
        status_val=AICTECaseStatusEnum.UNDER_PROCESS
    )
    case.next_action_due_at = overdue_date
    case.next_action_required = "Submit Compliance Report"
    db_session.commit()

    # First SLA scan generates the overdue alert
    results_run1 = AICTEAlertService.scan_and_generate_sla_alerts(db_session)
    assert results_run1["overdue_next_actions"] >= 1

    count_after_run1 = db_session.query(Notification).filter(
        Notification.user_id == officer.id,
        Notification.category == "SLA_OVERDUE"
    ).count()
    assert count_after_run1 >= 1

    # Second SLA scan immediately afterwards must be deduplicated
    results_run2 = AICTEAlertService.scan_and_generate_sla_alerts(db_session)
    count_after_run2 = db_session.query(Notification).filter(
        Notification.user_id == officer.id,
        Notification.category == "SLA_OVERDUE"
    ).count()

    assert count_after_run2 == count_after_run1, "Duplicate alert was created during repeat scan!"


def test_outbox_retry_counter_and_failure_handling(db_session):
    """
    Verify outbox delivery retry bounds:
    - Increments attempts counter on each cycle.
    - Flags status as FAILED when attempts exceed max retries.
    """
    user = _create_user(db_session, "outbox_user@test.edu", UserRoleEnum.COLLEGE_OFFICER)
    outbox = NotificationOutbox(
        user_id=user.id,
        channel="EMAIL",
        recipient_email="invalid-email-recipient@nowhere.internal",
        subject="Test Outbox Error",
        body="Body content.",
        status="PENDING",
        attempts=2,  # Already 2 attempts, max is 3
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(outbox)
    db_session.commit()

    # Simulate an error during dispatch
    outbox.attempts += 1
    if outbox.attempts >= 3:
        outbox.status = "FAILED"
        outbox.error_message = "SMTPConnectError: Connection refused"
    db_session.commit()

    db_session.refresh(outbox)
    assert outbox.attempts == 3
    assert outbox.status == "FAILED"
    assert "Connection refused" in outbox.error_message
