import pytest
from datetime import datetime, timezone
from fastapi import status
from sqlalchemy.orm import Session

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseActionTypeEnum,
    AICTETransferStatusEnum,
    GrievancePriorityEnum,
    AICTEComplainantTypeEnum,
    AICTECaseSourceTypeEnum,
)
from app.models.user import User
from app.models.institution import Institution
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.aicte_case import AICTECase, CaseAction
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.audit import AuditLog
from app.models.notification import NotificationOutbox
from app.core.security import create_access_token, hash_password

def auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def superadmin_user(db_session: Session) -> User:
    user = db_session.query(User).filter(User.email == "phase_e_superadmin@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_e_superadmin@eduresolve.ai",
            hashed_password=hash_password("SuperSecret123!"),
            full_name="Phase E Super Administrator",
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
    user = db_session.query(User).filter(User.email == "phase_e_student@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_e_student@eduresolve.ai",
            hashed_password=hash_password("StudentPass123!"),
            full_name="Phase E Student",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def rb_unit(db_session: Session) -> OrganizationalUnit:
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB_E").first()
    if not unit:
        unit = OrganizationalUnit(
            code="RB_E",
            name="Regulation Bureau (Phase E)",
            unit_type="BUREAU",
            description="Regulatory and compliance bureau for testing",
            is_active=True
        )
        db_session.add(unit)
        db_session.commit()
        db_session.refresh(unit)
    return unit

@pytest.fixture
def pgrc_unit(db_session: Session) -> OrganizationalUnit:
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC_E").first()
    if not unit:
        unit = OrganizationalUnit(
            code="PGRC_E",
            name="Public Grievance Redressal Cell (Phase E)",
            unit_type="CELL",
            description="Public grievance cell for testing",
            is_active=True
        )
        db_session.add(unit)
        db_session.commit()
        db_session.refresh(unit)
    return unit

@pytest.fixture
def ab_unit(db_session: Session) -> OrganizationalUnit:
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "AB_E").first()
    if not unit:
        unit = OrganizationalUnit(
            code="AB_E",
            name="Approval Bureau (Phase E)",
            unit_type="BUREAU",
            description="Approval Bureau for testing",
            is_active=True
        )
        db_session.add(unit)
        db_session.commit()
        db_session.refresh(unit)
    return unit

@pytest.fixture
def rb_officer(db_session: Session, rb_unit: OrganizationalUnit) -> User:
    user = db_session.query(User).filter(User.email == "phase_e_rb_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_e_rb_officer@eduresolve.ai",
            hashed_password=hash_password("OfficerPass123!"),
            full_name="Phase E RB Officer",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    membership = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == user.id,
        BureauMembership.organizational_unit_id == rb_unit.id
    ).first()
    if not membership:
        db_session.add(BureauMembership(
            user_id=user.id,
            organizational_unit_id=rb_unit.id,
            membership_role="BUREAU_OFFICER",
            is_active=True
        ))
        db_session.commit()
    return user

@pytest.fixture
def rb_head(db_session: Session, rb_unit: OrganizationalUnit) -> User:
    user = db_session.query(User).filter(User.email == "phase_e_rb_head@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_e_rb_head@eduresolve.ai",
            hashed_password=hash_password("HeadPass123!"),
            full_name="Phase E RB Bureau Head",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    membership = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == user.id,
        BureauMembership.organizational_unit_id == rb_unit.id
    ).first()
    if not membership:
        db_session.add(BureauMembership(
            user_id=user.id,
            organizational_unit_id=rb_unit.id,
            membership_role="BUREAU_HEAD",
            is_active=True
        ))
        db_session.commit()
    return user

@pytest.fixture
def pgrc_officer(db_session: Session, pgrc_unit: OrganizationalUnit) -> User:
    user = db_session.query(User).filter(User.email == "phase_e_pgrc_officer@eduresolve.ai").first()
    if not user:
        user = User(
            email="phase_e_pgrc_officer@eduresolve.ai",
            hashed_password=hash_password("OfficerPass123!"),
            full_name="Phase E PGRC Officer",
            default_role=UserRoleEnum.REGULATORY_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    membership = db_session.query(BureauMembership).filter(
        BureauMembership.user_id == user.id,
        BureauMembership.organizational_unit_id == pgrc_unit.id
    ).first()
    if not membership:
        db_session.add(BureauMembership(
            user_id=user.id,
            organizational_unit_id=pgrc_unit.id,
            membership_role="BUREAU_OFFICER",
            is_active=True
        ))
        db_session.commit()
    return user

@pytest.fixture
def test_institution(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "INST_PHASE_E").first()
    if not inst:
        inst = Institution(
            name="Delhi Institute of Engineering and Technology (Phase E)",
            code="INST_PHASE_E",
            aicte_permanent_id="1-9999888877",
            is_aicte_verified=True,
            contact_email="director@diet-e.edu.in",
            contact_phone="+91-11-23456789",
            state="Delhi",
            district="New Delhi",
            city="New Delhi",
            address="Phase E Campus",
            institution_type="ENGINEERING",
            is_active=True,
            is_verified=True,
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst

@pytest.fixture
def sample_case_in_rb(
    db_session: Session,
    test_institution: Institution,
    rb_unit: OrganizationalUnit,
    superadmin_user: User,
    rb_officer: User
) -> AICTECase:
    case = db_session.query(AICTECase).filter(AICTECase.case_reference == "AICTE-TEST-E-001").first()
    if not case:
        case = AICTECase(
            case_reference="AICTE-TEST-E-001",
            institution_id=test_institution.id,
            current_unit_id=rb_unit.id,
            assigned_officer_id=rb_officer.id,
            created_by_user_id=superadmin_user.id,
            subject="Unauthorized student intake and excessive capitation fees",
            description="Institution enrolled 60 students beyond the AICTE approved intake quota for B.Tech CS.",
            category="ADMISSION_IRREGULARITY",
            status=AICTECaseStatusEnum.UNDER_PROCESS,
            priority=GrievancePriorityEnum.HIGH,
            source_type=AICTECaseSourceTypeEnum.DIRECT,
            complainant_type=AICTEComplainantTypeEnum.STAKEHOLDER,
            received_at=datetime.now(timezone.utc),
            last_action_at=datetime.now(timezone.utc),
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
    else:
        # Reset state for clean test run
        case.current_unit_id = rb_unit.id
        case.assigned_officer_id = rb_officer.id
        case.status = AICTECaseStatusEnum.UNDER_PROCESS
        db_session.commit()
    return case


# ---------------------------------------------------------------------------
# Phase E Tests
# ---------------------------------------------------------------------------

def test_initiate_transfer_authorized_success(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    rb_officer: User,
    db_session: Session
):
    """Authorized officer in originating unit can initiate an inter-bureau transfer proposal."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    payload = {
        "to_unit_id": pgrc_unit.id,
        "transfer_reason": "Jurisdictional review indicates student grievance issues belong under PGRC oversight.",
        "handover_summary": "Preliminary inquiry completed. Documents attached in case docket."
    }

    res = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json=payload,
        headers=auth_headers(rb_officer)
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["case_id"] == sample_case_in_rb.id
    assert data["from_unit_id"] == sample_case_in_rb.current_unit_id
    assert data["to_unit_id"] == pgrc_unit.id
    assert data["transfer_status"] == "PENDING_ACCEPTANCE"
    assert data["prior_case_status"] == "UNDER_PROCESS"

    # Case must move to TRANSFER_PENDING, but current_unit_id and assigned_officer_id remain unchanged
    db_session.refresh(sample_case_in_rb)
    assert sample_case_in_rb.status == AICTECaseStatusEnum.TRANSFER_PENDING
    assert sample_case_in_rb.current_unit_id == data["from_unit_id"]
    assert sample_case_in_rb.assigned_officer_id == rb_officer.id


def test_initiate_transfer_unauthorized_user_forbidden(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    regular_student: User
):
    """Students and unprivileged campus users are rejected with HTTP 403."""
    payload = {
        "to_unit_id": pgrc_unit.id,
        "transfer_reason": "Attempting unauthorized transfer without Bureau credentials."
    }
    res = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json=payload,
        headers=auth_headers(regular_student)
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_initiate_transfer_invalid_or_identical_destination(
    client,
    sample_case_in_rb: AICTECase,
    rb_unit: OrganizationalUnit,
    rb_officer: User
):
    """Transfer to same unit or non-existent unit returns error."""
    # Same unit
    res_same = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={
            "to_unit_id": rb_unit.id,
            "transfer_reason": "Transferring back to same unit is invalid."
        },
        headers=auth_headers(rb_officer)
    )
    assert res_same.status_code == status.HTTP_400_BAD_REQUEST

    # Non-existent unit
    res_none = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={
            "to_unit_id": 999999,
            "transfer_reason": "Transferring to invalid unit."
        },
        headers=auth_headers(rb_officer)
    )
    assert res_none.status_code == status.HTTP_404_NOT_FOUND


def test_initiate_transfer_proposed_assignee_validation(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    rb_officer: User
):
    """Proposed assignee must possess active membership in the destination unit."""
    payload = {
        "to_unit_id": pgrc_unit.id,
        "proposed_assignee_id": rb_officer.id,
        "transfer_reason": "Transfer with invalid assignee."
    }
    res = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json=payload,
        headers=auth_headers(rb_officer)
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_duplicate_pending_transfer_prevention(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    ab_unit: OrganizationalUnit,
    rb_officer: User,
    db_session: Session
):
    """A case cannot have more than one active PENDING_ACCEPTANCE transfer at a time."""
    # Ensure there is an active pending transfer
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    # First proposal succeeds
    res_first = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={
            "to_unit_id": pgrc_unit.id,
            "transfer_reason": "First valid transfer proposal in progress."
        },
        headers=auth_headers(rb_officer)
    )
    assert res_first.status_code == status.HTTP_201_CREATED

    # Second concurrent proposal fails with 409 Conflict
    res_second = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={
            "to_unit_id": ab_unit.id,
            "transfer_reason": "Attempting second concurrent transfer proposal."
        },
        headers=auth_headers(rb_officer)
    )
    assert res_second.status_code == status.HTTP_409_CONFLICT


def test_accept_transfer_unauthorized_unit_forbidden(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    rb_officer: User,
    db_session: Session
):
    """An officer in the originating unit cannot accept their own transfer proposal."""
    # Ensure a pending transfer exists to PGRC
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={"to_unit_id": pgrc_unit.id, "transfer_reason": "Transfer awaiting acceptance."},
        headers=auth_headers(rb_officer)
    )
    assert res_init.status_code == status.HTTP_201_CREATED
    transfer_id = res_init.json()["id"]

    # Originating officer attempts to accept
    res = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/accept",
        json={"response_notes": "Originating officer illegally trying to accept."},
        headers=auth_headers(rb_officer)
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_accept_transfer_by_receiving_unit_officer_success(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    pgrc_officer: User,
    rb_officer: User,
    db_session: Session
):
    """Authorized receiving unit official accepts transfer atomically updating responsibility."""
    # Ensure fresh pending transfer
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={"to_unit_id": pgrc_unit.id, "transfer_reason": "Transfer awaiting acceptance."},
        headers=auth_headers(rb_officer)
    )
    assert res_init.status_code == status.HTTP_201_CREATED
    transfer_id = res_init.json()["id"]

    res = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/accept",
        json={
            "response_notes": "Accepted under PGRC jurisdiction. Assigned to intake cell.",
            "accepted_assignee_id": pgrc_officer.id
        },
        headers=auth_headers(pgrc_officer)
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["transfer_status"] == "ACCEPTED"
    assert data["accepted_assignee_id"] == pgrc_officer.id

    # Verify atomic update on case
    db_session.refresh(sample_case_in_rb)
    assert sample_case_in_rb.current_unit_id == pgrc_unit.id
    assert sample_case_in_rb.assigned_officer_id == pgrc_officer.id
    assert sample_case_in_rb.status == AICTECaseStatusEnum.TRANSFERRED


def test_cannot_decide_already_accepted_transfer(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    pgrc_officer: User,
    rb_officer: User,
    db_session: Session
):
    """Attempting to accept or reject an already decided transfer returns HTTP 409 Conflict."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={"to_unit_id": pgrc_unit.id, "transfer_reason": "Transfer to be accepted and then rejected."},
        headers=auth_headers(rb_officer)
    )
    transfer_id = res_init.json()["id"]

    # First accept
    res_acc = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/accept",
        json={"response_notes": "Accepted."},
        headers=auth_headers(pgrc_officer)
    )
    assert res_acc.status_code == status.HTTP_200_OK

    # Subsequent reject attempt
    res_rej = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/reject",
        json={"rejection_reason": "Trying to reject already accepted transfer."},
        headers=auth_headers(pgrc_officer)
    )
    assert res_rej.status_code == status.HTTP_409_CONFLICT


def test_reject_transfer_preserves_unit_and_restores_prior_status(
    client,
    sample_case_in_rb: AICTECase,
    rb_officer: User,
    pgrc_officer: User,
    rb_unit: OrganizationalUnit,
    pgrc_unit: OrganizationalUnit,
    db_session: Session
):
    """Rejection preserves original handling unit and restores prior case status."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.current_unit_id = rb_unit.id
    sample_case_in_rb.assigned_officer_id = rb_officer.id
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    # Initiate new transfer from RB to PGRC
    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={
            "to_unit_id": pgrc_unit.id,
            "transfer_reason": "Proposal that will be declined by PGRC."
        },
        headers=auth_headers(rb_officer)
    )
    assert res_init.status_code == status.HTTP_201_CREATED
    transfer_id = res_init.json()["id"]

    # PGRC officer rejects transfer
    res_rej = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/reject",
        json={"rejection_reason": "Allegation does not involve students or faculty grievances; belongs in RB."},
        headers=auth_headers(pgrc_officer)
    )
    assert res_rej.status_code == status.HTTP_200_OK
    assert res_rej.json()["transfer_status"] == "REJECTED"

    # Verify case state is restored to UNDER_PROCESS, current_unit_id stays RB
    db_session.refresh(sample_case_in_rb)
    assert sample_case_in_rb.status == AICTECaseStatusEnum.UNDER_PROCESS
    assert sample_case_in_rb.current_unit_id == rb_unit.id
    assert sample_case_in_rb.assigned_officer_id == rb_officer.id


def test_cancel_transfer_by_initiator_success(
    client,
    sample_case_in_rb: AICTECase,
    rb_officer: User,
    ab_unit: OrganizationalUnit,
    rb_unit: OrganizationalUnit,
    db_session: Session
):
    """Initiator can withdraw/cancel a pending transfer before a decision is made."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.current_unit_id = rb_unit.id
    sample_case_in_rb.assigned_officer_id = rb_officer.id
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={
            "to_unit_id": ab_unit.id,
            "transfer_reason": "Transfer mistakenly initiated."
        },
        headers=auth_headers(rb_officer)
    )
    assert res_init.status_code == status.HTTP_201_CREATED
    transfer_id = res_init.json()["id"]

    # Cancel transfer
    res_cancel = client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/cancel",
        json={"cancellation_reason": "Correct jurisdiction was already verified; cancelling proposal."},
        headers=auth_headers(rb_officer)
    )
    assert res_cancel.status_code == status.HTTP_200_OK
    assert res_cancel.json()["transfer_status"] == "CANCELLED"

    # Verify case returned to prior status
    db_session.refresh(sample_case_in_rb)
    assert sample_case_in_rb.status == AICTECaseStatusEnum.UNDER_PROCESS
    assert sample_case_in_rb.current_unit_id == rb_unit.id


def test_case_action_and_audit_history_recorded(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    rb_officer: User,
    pgrc_officer: User,
    db_session: Session
):
    """Every transfer milestone is permanently recorded in CaseAction and AuditLog."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    # 1. Initiate
    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={"to_unit_id": pgrc_unit.id, "transfer_reason": "Testing action history logging."},
        headers=auth_headers(rb_officer)
    )
    transfer_id = res_init.json()["id"]

    # 2. Accept
    client.post(
        f"/api/v1/aicte/transfers/{transfer_id}/accept",
        json={"response_notes": "Accepted for history testing."},
        headers=auth_headers(pgrc_officer)
    )

    actions = db_session.query(CaseAction).filter(
        CaseAction.case_id == sample_case_in_rb.id,
        CaseAction.action_type.in_([
            AICTECaseActionTypeEnum.TRANSFER_INITIATED,
            AICTECaseActionTypeEnum.TRANSFER_ACCEPTED
        ])
    ).all()
    assert len(actions) >= 2

    audit_entries = db_session.query(AuditLog).filter(
        AuditLog.action.in_([
            "AICTE_TRANSFER_INITIATED",
            "AICTE_TRANSFER_ACCEPTED"
        ])
    ).all()
    assert len(audit_entries) >= 2


def test_incoming_and_outgoing_queues(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    pgrc_officer: User,
    rb_officer: User,
    db_session: Session
):
    """Queue endpoints return incoming and outgoing transfers scoped by user unit."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    # Initiate a transfer from RB to PGRC
    res_init = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={"to_unit_id": pgrc_unit.id, "transfer_reason": "Testing queue listings."},
        headers=auth_headers(rb_officer)
    )
    assert res_init.status_code == status.HTTP_201_CREATED

    # Outgoing for RB officer
    res_out = client.get(
        "/api/v1/aicte/transfers/outgoing",
        headers=auth_headers(rb_officer)
    )
    assert res_out.status_code == status.HTTP_200_OK
    assert res_out.json()["total"] >= 1

    # Incoming for PGRC officer
    res_in = client.get(
        "/api/v1/aicte/transfers/incoming",
        headers=auth_headers(pgrc_officer)
    )
    assert res_in.status_code == status.HTTP_200_OK
    assert res_in.json()["total"] >= 1


def test_notifications_queued_in_outbox(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    pgrc_officer: User,
    rb_officer: User,
    db_session: Session
):
    """Transfer events enqueue notifications in NotificationOutbox without failing."""
    db_session.query(AICTECaseTransfer).filter(AICTECaseTransfer.case_id == sample_case_in_rb.id).delete()
    sample_case_in_rb.status = AICTECaseStatusEnum.UNDER_PROCESS
    db_session.commit()

    client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/transfers",
        json={"to_unit_id": pgrc_unit.id, "transfer_reason": "Testing outbox notifications dispatch."},
        headers=auth_headers(rb_officer)
    )

    outbox_entries = db_session.query(NotificationOutbox).filter(
        NotificationOutbox.subject.ilike("%Transfer%")
    ).all()
    assert len(outbox_entries) >= 1


def test_direct_assignment_cannot_bypass_interbureau_transfer(
    client,
    sample_case_in_rb: AICTECase,
    pgrc_unit: OrganizationalUnit,
    rb_head: User
):
    """Bureau supervisors cannot use /assign to bypass the formal inter-Bureau transfer workflow."""
    res = client.post(
        f"/api/v1/aicte/cases/{sample_case_in_rb.id}/assign",
        json={"current_unit_id": pgrc_unit.id, "reason": "Bypassing transfer"},
        headers=auth_headers(rb_head)
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Inter-bureau transfers cannot be performed via direct assignment" in res.json()["detail"]
