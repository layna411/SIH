import math
import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database.connection import get_db
from app.core.permissions import (
    get_current_active_user,
    require_super_admin,
    get_user_bureau_unit_ids,
    check_bureau_access,
)
from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseSourceTypeEnum,
    AICTEComplainantTypeEnum,
    AICTECaseActionTypeEnum,
    GrievancePriorityEnum,
)
from app.models.user import User
from app.models.institution import Institution, InstitutionAlias
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.grievance import Grievance
from app.models.aicte_case import AICTECase, CaseAction
from app.models.audit import AuditLog
from app.utils.reference import generate_reference_number
from app.schemas.aicte_case import (
    AICTECaseCreate,
    AICTECaseUpdate,
    AICTECaseAssign,
    AICTECaseReferGrievance,
    CaseActionCreate,
    CaseActionResponse,
    AICTECaseResponse,
    AICTECaseDetailResponse,
    AICTECaseListResponse,
    InstitutionConsolidatedHistoryResponse,
)

router = APIRouter(prefix="/aicte", tags=["AICTE Case Management"])

def _generate_unique_case_reference(db: Session) -> str:
    """Generate a collision-free AICTE case reference."""
    for _ in range(10):
        ref = generate_reference_number(prefix="AICTE")
        existing = db.query(AICTECase).filter(AICTECase.case_reference == ref).first()
        if not existing:
            return ref
    # Fallback with timestamp
    ts = int(datetime.now(timezone.utc).timestamp())
    return f"AICTE-{datetime.now().year}-{ts}"

def _map_case_to_response(case: AICTECase) -> AICTECaseResponse:
    """Map AICTECase ORM entity to response schema with related metadata."""
    return AICTECaseResponse(
        id=case.id,
        case_reference=case.case_reference,
        institution_id=case.institution_id,
        institution_name=case.institution.name if case.institution else None,
        institution_code=case.institution.code if case.institution else None,
        aicte_permanent_id=case.institution.aicte_permanent_id if case.institution else None,
        source_grievance_id=case.source_grievance_id,
        source_grievance_reference=case.source_grievance.reference_number if case.source_grievance else None,
        source_type=case.source_type,
        official_reference_number=case.official_reference_number,
        received_at=case.received_at,
        complainant_type=case.complainant_type,
        complainant_name=case.complainant_name,
        complainant_email=case.complainant_email,
        complainant_phone=case.complainant_phone,
        category=case.category,
        subject=case.subject,
        description=case.description,
        status=case.status,
        current_unit_id=case.current_unit_id,
        current_unit_code=case.current_unit.code if case.current_unit else None,
        current_unit_name=case.current_unit.name if case.current_unit else None,
        assigned_officer_id=case.assigned_officer_id,
        assigned_officer_name=case.assigned_officer.full_name if case.assigned_officer else None,
        region=case.region,
        priority=case.priority,
        last_action_at=case.last_action_at,
        next_action_required=case.next_action_required,
        next_action_due_at=case.next_action_due_at,
        expected_disposal_at=case.expected_disposal_at,
        disposed_at=case.disposed_at,
        created_by_user_id=case.created_by_user_id,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )

def _map_action_to_response(action: CaseAction) -> CaseActionResponse:
    """Map CaseAction ORM entity to response schema."""
    return CaseActionResponse(
        id=action.id,
        case_id=action.case_id,
        action_type=action.action_type,
        action_title=action.action_title,
        action_description=action.action_description,
        previous_status=action.previous_status,
        new_status=action.new_status,
        unit_id=action.unit_id,
        unit_code=action.unit.code if action.unit else None,
        unit_name=action.unit.name if action.unit else None,
        performed_by_user_id=action.performed_by_user_id,
        performed_by_name=action.performed_by_user.full_name if action.performed_by_user else None,
        performed_by_email=action.performed_by_user.email if action.performed_by_user else None,
        action_at=action.action_at,
        remarks=action.remarks,
        supporting_document_ref=action.supporting_document_ref,
        next_action_required=action.next_action_required,
        next_action_due_at=action.next_action_due_at,
    )

def _validate_lifecycle_transition(current_status: AICTECaseStatusEnum, new_status: AICTECaseStatusEnum):
    """Validate server-side state machine for AICTE cases."""
    if current_status == new_status:
        return

    allowed_transitions = {
        AICTECaseStatusEnum.RECEIVED: {
            AICTECaseStatusEnum.PENDING_REVIEW,
            AICTECaseStatusEnum.UNDER_PROCESS,
            AICTECaseStatusEnum.TRANSFER_PENDING,
            AICTECaseStatusEnum.CLOSED,
        },
        AICTECaseStatusEnum.PENDING_REVIEW: {
            AICTECaseStatusEnum.UNDER_PROCESS,
            AICTECaseStatusEnum.AWAITING_RESPONSE,
            AICTECaseStatusEnum.TRANSFER_PENDING,
            AICTECaseStatusEnum.DISPOSED,
            AICTECaseStatusEnum.CLOSED,
        },
        AICTECaseStatusEnum.UNDER_PROCESS: {
            AICTECaseStatusEnum.AWAITING_RESPONSE,
            AICTECaseStatusEnum.TRANSFER_PENDING,
            AICTECaseStatusEnum.ESCALATED,
            AICTECaseStatusEnum.DISPOSED,
            AICTECaseStatusEnum.CLOSED,
        },
        AICTECaseStatusEnum.AWAITING_RESPONSE: {
            AICTECaseStatusEnum.UNDER_PROCESS,
            AICTECaseStatusEnum.ESCALATED,
            AICTECaseStatusEnum.DISPOSED,
            AICTECaseStatusEnum.CLOSED,
        },
        AICTECaseStatusEnum.TRANSFER_PENDING: {
            AICTECaseStatusEnum.TRANSFERRED,
            AICTECaseStatusEnum.UNDER_PROCESS,
            AICTECaseStatusEnum.CLOSED,
        },
        AICTECaseStatusEnum.TRANSFERRED: {
            AICTECaseStatusEnum.RECEIVED,
            AICTECaseStatusEnum.PENDING_REVIEW,
            AICTECaseStatusEnum.UNDER_PROCESS,
        },
        AICTECaseStatusEnum.ESCALATED: {
            AICTECaseStatusEnum.UNDER_PROCESS,
            AICTECaseStatusEnum.DISPOSED,
            AICTECaseStatusEnum.CLOSED,
        },
        AICTECaseStatusEnum.DISPOSED: {
            AICTECaseStatusEnum.CLOSED,
            AICTECaseStatusEnum.REOPENED,
        },
        AICTECaseStatusEnum.CLOSED: {
            AICTECaseStatusEnum.REOPENED,
        },
        AICTECaseStatusEnum.REOPENED: {
            AICTECaseStatusEnum.UNDER_PROCESS,
            AICTECaseStatusEnum.PENDING_REVIEW,
        },
    }

    allowed = allowed_transitions.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AICTE case lifecycle transition from {current_status.value} to {new_status.value}."
        )


# ---------------------------------------------------------------------------
# 1. List Cases (Authorized & Filtered)
# ---------------------------------------------------------------------------
@router.get("/cases", response_model=AICTECaseListResponse)
def list_aicte_cases(
    status_filter: Optional[AICTECaseStatusEnum] = Query(None, alias="status"),
    unit_id: Optional[int] = Query(None),
    institution_id: Optional[int] = Query(None),
    priority: Optional[GrievancePriorityEnum] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List AICTE cases with multi-criteria filtering and server-side RBAC scoping:
    - SuperAdmin sees all cases nationwide.
    - Bureau members see cases assigned to the organizational units they belong to.
    - Unauthorized roles (students, college officers without Bureau roles) are denied.
    """
    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    if not authorized_unit_ids and current_user.default_role != UserRoleEnum.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess an active AICTE Bureau membership."
        )

    query = db.query(AICTECase)

    # Unit boundary scoping
    if current_user.default_role != UserRoleEnum.SUPER_ADMIN:
        query = query.filter(AICTECase.current_unit_id.in_(authorized_unit_ids))

    if unit_id:
        if current_user.default_role != UserRoleEnum.SUPER_ADMIN and unit_id not in authorized_unit_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden to the requested organizational unit."
            )
        query = query.filter(AICTECase.current_unit_id == unit_id)

    if institution_id:
        query = query.filter(AICTECase.institution_id == institution_id)

    if status_filter:
        query = query.filter(AICTECase.status == status_filter)

    if priority:
        query = query.filter(AICTECase.priority == priority)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.join(AICTECase.institution).filter(
            or_(
                AICTECase.case_reference.ilike(search_pattern),
                AICTECase.official_reference_number.ilike(search_pattern),
                AICTECase.subject.ilike(search_pattern),
                AICTECase.category.ilike(search_pattern),
                Institution.name.ilike(search_pattern),
                Institution.code.ilike(search_pattern),
                Institution.aicte_permanent_id.ilike(search_pattern)
            )
        )

    total = query.count()
    cases = query.order_by(desc(AICTECase.last_action_at)).offset((page - 1) * page_size).limit(page_size).all()

    return AICTECaseListResponse(
        cases=[_map_case_to_response(c) for c in cases],
        total=total,
        page=page,
        page_size=page_size
    )


# ---------------------------------------------------------------------------
# 2. Direct AICTE Case Intake
# ---------------------------------------------------------------------------
@router.post("/cases", response_model=AICTECaseResponse, status_code=status.HTTP_201_CREATED)
def create_aicte_case(
    payload: AICTECaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Direct case intake into an AICTE Bureau/Cell:
    - Verifies institution exists.
    - Validates responsible organizational unit.
    - Verifies caller has active Bureau membership in the destination unit or is SuperAdmin.
    - Validates assigned officer has active membership in destination unit if specified.
    - Generates collision-free case reference and records initial INTAKE action.
    """
    # 1. Validate Institution
    institution = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution with ID {payload.institution_id} does not exist."
        )

    # 2. Validate Unit
    unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == payload.current_unit_id, OrganizationalUnit.is_active == True).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active organizational unit with ID {payload.current_unit_id} not found."
        )

    # 3. Check caller authorization
    if not check_bureau_access(current_user, payload.current_unit_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not possess authorized Bureau membership in the destination unit."
        )

    # 4. Validate assigned officer if provided
    if payload.assigned_officer_id:
        officer = db.query(User).filter(User.id == payload.assigned_officer_id, User.is_active == True).first()
        if not officer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assigned user ID {payload.assigned_officer_id} not found."
            )
        # Check active membership in unit
        has_membership = any(
            bm.organizational_unit_id == payload.current_unit_id and bm.is_active
            for bm in officer.bureau_memberships
        ) or officer.default_role == UserRoleEnum.SUPER_ADMIN
        if not has_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {officer.full_name} does not have an active membership in {unit.code}."
            )

    region_val = payload.region or institution.region

    # 5. Create AICTE Case
    case_ref = _generate_unique_case_reference(db)
    new_case = AICTECase(
        case_reference=case_ref,
        institution_id=institution.id,
        source_grievance_id=None,
        source_type=AICTECaseSourceTypeEnum.DIRECT,
        official_reference_number=payload.official_reference_number,
        received_at=datetime.now(timezone.utc),
        complainant_type=payload.complainant_type,
        complainant_name=payload.complainant_name,
        complainant_email=payload.complainant_email,
        complainant_phone=payload.complainant_phone,
        category=payload.category.strip(),
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        status=AICTECaseStatusEnum.RECEIVED,
        current_unit_id=unit.id,
        assigned_officer_id=payload.assigned_officer_id,
        region=region_val,
        priority=payload.priority,
        last_action_at=datetime.now(timezone.utc),
        next_action_required=payload.next_action_required,
        next_action_due_at=payload.next_action_due_at,
        expected_disposal_at=payload.expected_disposal_at,
        created_by_user_id=current_user.id,
    )
    db.add(new_case)
    db.flush()

    # 6. Record Initial INTAKE Action
    intake_action = CaseAction(
        case_id=new_case.id,
        action_type=AICTECaseActionTypeEnum.INTAKE,
        action_title="Direct Case Intake Registered",
        action_description=f"Case received into {unit.name} ({unit.code}). Category: {new_case.category}.",
        previous_status=None,
        new_status=new_case.status.value,
        unit_id=unit.id,
        performed_by_user_id=current_user.id,
        action_at=datetime.now(timezone.utc),
        remarks=f"Intake registered by {current_user.full_name}.",
        next_action_required=payload.next_action_required,
        next_action_due_at=payload.next_action_due_at,
    )
    db.add(intake_action)

    # 7. Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="AICTE_CASE_CREATED",
        entity_type="AICTE_CASE",
        entity_id=str(new_case.id),
        details=json.dumps({
            "case_reference": new_case.case_reference,
            "institution_id": institution.id,
            "unit_code": unit.code,
            "category": new_case.category
        })
    ))

    db.commit()
    db.refresh(new_case)
    return _map_case_to_response(new_case)


# ---------------------------------------------------------------------------
# 3. Case Details & Authorized History
# ---------------------------------------------------------------------------
@router.get("/cases/{case_id}", response_model=AICTECaseDetailResponse)
def get_aicte_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve full details of an AICTE case including chronological action log."""
    case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AICTE Case #{case_id} not found."
        )

    if not check_bureau_access(current_user, case.current_unit_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized membership in the handling Bureau."
        )

    resp = _map_case_to_response(case)
    actions = [_map_action_to_response(a) for a in case.actions]
    return AICTECaseDetailResponse(**resp.model_dump(), actions=actions)


# ---------------------------------------------------------------------------
# 4. Update Case Metadata
# ---------------------------------------------------------------------------
@router.patch("/cases/{case_id}", response_model=AICTECaseResponse)
def update_aicte_case(
    case_id: int,
    payload: AICTECaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update permitted metadata on an AICTE case."""
    case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AICTE Case #{case_id} not found."
        )

    if not check_bureau_access(current_user, case.current_unit_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you cannot modify cases outside your Bureau."
        )

    if payload.subject is not None:
        case.subject = payload.subject.strip()
    if payload.description is not None:
        case.description = payload.description.strip()
    if payload.category is not None:
        case.category = payload.category.strip()
    if payload.priority is not None:
        case.priority = payload.priority
    if payload.official_reference_number is not None:
        case.official_reference_number = payload.official_reference_number.strip() or None
    if payload.region is not None:
        case.region = payload.region.strip() or None
    if payload.expected_disposal_at is not None:
        case.expected_disposal_at = payload.expected_disposal_at
    if payload.next_action_required is not None:
        case.next_action_required = payload.next_action_required.strip() or None
    if payload.next_action_due_at is not None:
        case.next_action_due_at = payload.next_action_due_at

    case.last_action_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(case)
    return _map_case_to_response(case)


# ---------------------------------------------------------------------------
# 5. Case Assignment & Responsible Officer
# ---------------------------------------------------------------------------
@router.post("/cases/{case_id}/assign", response_model=AICTECaseResponse)
def assign_aicte_case(
    case_id: int,
    payload: AICTECaseAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign or reassign an AICTE case to a Bureau unit and/or officer:
    - User must hold Bureau Head privileges or be SuperAdmin.
    - Validates that the assigned officer has an active membership in the responsible unit.
    - Records an ASSIGNMENT action in the procedural action history.
    """
    case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AICTE Case #{case_id} not found."
        )

    # Check caller has supervisory authority
    if not check_bureau_access(current_user, case.current_unit_id, db, require_head=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assignment requires supervisory Bureau Head or Super Administrator privileges."
        )

    new_unit_id = payload.current_unit_id or case.current_unit_id
    if new_unit_id != case.current_unit_id:
        if current_user.default_role != UserRoleEnum.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inter-bureau transfers cannot be performed via direct assignment. Please initiate a formal inter-Bureau transfer proposal instead."
            )
        target_unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == new_unit_id, OrganizationalUnit.is_active == True).first()
        if not target_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target organizational unit #{new_unit_id} not found or inactive."
            )
        case.current_unit_id = new_unit_id

    assigned_officer = None
    if payload.assigned_officer_id:
        officer = db.query(User).filter(User.id == payload.assigned_officer_id, User.is_active == True).first()
        if not officer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User #{payload.assigned_officer_id} not found."
            )
        has_membership = any(
            bm.organizational_unit_id == case.current_unit_id and bm.is_active
            for bm in officer.bureau_memberships
        ) or officer.default_role == UserRoleEnum.SUPER_ADMIN
        if not has_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Officer {officer.full_name} does not have an active membership in unit #{case.current_unit_id}."
            )
        case.assigned_officer_id = officer.id
        assigned_officer = officer
    elif payload.assigned_officer_id == 0:
        case.assigned_officer_id = None

    case.last_action_at = datetime.now(timezone.utc)

    # Log ASSIGNMENT action
    officer_name = assigned_officer.full_name if assigned_officer else "Unassigned"
    assignment_action = CaseAction(
        case_id=case.id,
        action_type=AICTECaseActionTypeEnum.ASSIGNMENT,
        action_title="Case Assignment Updated",
        action_description=f"Assigned Officer: {officer_name}. Unit: {case.current_unit.code if case.current_unit else new_unit_id}.",
        previous_status=case.status.value,
        new_status=case.status.value,
        unit_id=case.current_unit_id,
        performed_by_user_id=current_user.id,
        action_at=datetime.now(timezone.utc),
        remarks=payload.reason or "Assignment updated by supervisor."
    )
    db.add(assignment_action)
    db.commit()
    db.refresh(case)

    # Dispatch assignment alert
    if assigned_officer:
        from app.services.aicte_alert_service import AICTEAlertService
        AICTEAlertService.notify_case_assignment(
            db=db,
            case=case,
            assigned_officer_id=assigned_officer.id,
            actor=current_user
        )

    return _map_case_to_response(case)


# ---------------------------------------------------------------------------
# 6. Procedural Case Actions & Status Transition
# ---------------------------------------------------------------------------
@router.post("/cases/{case_id}/actions", response_model=CaseActionResponse, status_code=status.HTTP_201_CREATED)
def append_case_action(
    case_id: int,
    payload: CaseActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Append an official procedural step to an AICTE case docket:
    - Verifies user has access to the responsible Bureau.
    - If status change requested, validates lifecycle transition.
    - Commits action and case status atomically.
    """
    case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AICTE Case #{case_id} not found."
        )

    if not check_bureau_access(current_user, case.current_unit_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized membership in the handling Bureau."
        )

    prev_status = case.status
    new_status = payload.new_status

    if new_status and new_status != prev_status:
        _validate_lifecycle_transition(prev_status, new_status)
        case.status = new_status
        if new_status == AICTECaseStatusEnum.DISPOSED:
            case.disposed_at = datetime.now(timezone.utc)
        elif new_status == AICTECaseStatusEnum.REOPENED:
            case.disposed_at = None

    if payload.next_action_required:
        case.next_action_required = payload.next_action_required.strip()
    if payload.next_action_due_at:
        case.next_action_due_at = payload.next_action_due_at

    case.last_action_at = datetime.now(timezone.utc)

    action = CaseAction(
        case_id=case.id,
        action_type=payload.action_type,
        action_title=payload.action_title.strip(),
        action_description=payload.action_description.strip() if payload.action_description else None,
        previous_status=prev_status.value if new_status else None,
        new_status=new_status.value if new_status else None,
        unit_id=case.current_unit_id,
        performed_by_user_id=current_user.id,
        action_at=datetime.now(timezone.utc),
        remarks=payload.remarks.strip() if payload.remarks else None,
        supporting_document_ref=payload.supporting_document_ref.strip() if payload.supporting_document_ref else None,
        next_action_required=payload.next_action_required.strip() if payload.next_action_required else None,
        next_action_due_at=payload.next_action_due_at,
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    # Trigger escalation alert if escalated
    if (new_status == AICTECaseStatusEnum.ESCALATED) or (payload.action_type == AICTECaseActionTypeEnum.ESCALATION):
        from app.services.aicte_alert_service import AICTEAlertService
        recipients = set(AICTEAlertService.get_unit_member_ids(db, case.current_unit_id))
        if case.assigned_officer_id:
            recipients.add(case.assigned_officer_id)
        for uid in recipients:
            AICTEAlertService.send_alert(
                db=db,
                recipient_id=uid,
                category="CASE_ESCALATED",
                severity="CRITICAL",
                title=f"Case Escalated: {case.case_reference}",
                message=f"Case {case.case_reference} has been escalated: {payload.action_title}.",
                link=f"/aicte/cases/{case.id}",
                reference_id=f"ESCALATION_{case.id}_{action.id}",
                requires_acknowledgement=True
            )

    return _map_action_to_response(action)


# ---------------------------------------------------------------------------
# 7. Chronological Action History
# ---------------------------------------------------------------------------
@router.get("/cases/{case_id}/history", response_model=List[CaseActionResponse])
def get_case_history(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve the full chronological procedural action log for a case."""
    case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AICTE Case #{case_id} not found."
        )

    if not check_bureau_access(current_user, case.current_unit_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this Bureau case history."
        )

    actions = db.query(CaseAction).filter(CaseAction.case_id == case_id).order_by(CaseAction.action_at.asc()).all()
    return [_map_action_to_response(a) for a in actions]


# ---------------------------------------------------------------------------
# 8. Campus Grievance to AICTE Referral
# ---------------------------------------------------------------------------
@router.post("/cases/refer-grievance", response_model=AICTECaseResponse, status_code=status.HTTP_201_CREATED)
def refer_campus_grievance_to_aicte(
    payload: AICTECaseReferGrievance,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Controlled referral of an existing campus grievance into the AICTE case system:
    - Verifies caller has permission to refer (SuperAdmin, RegulatoryAdmin, or Officer/Head of institution).
    - Prevents duplicate referral of the same grievance.
    - Validates destination organizational unit.
    - Creates AICTECase with source_type=CAMPUS_REFERRAL and source_grievance_id.
    - Preserves source grievance status and notes intact.
    - Atomically logs INTAKE action.
    """
    # 1. Fetch Source Grievance
    grievance = db.query(Grievance).filter(Grievance.id == payload.source_grievance_id).first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campus grievance #{payload.source_grievance_id} does not exist."
        )

    # 2. Prevent duplicate referral
    existing_referral = db.query(AICTECase).filter(AICTECase.source_grievance_id == grievance.id).first()
    if existing_referral:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grievance #{grievance.reference_number} has already been referred to AICTE as case {existing_referral.case_reference}."
        )

    # 3. Check caller authorization to refer
    is_super = current_user.default_role == UserRoleEnum.SUPER_ADMIN
    is_regulatory = current_user.default_role == UserRoleEnum.REGULATORY_ADMIN
    is_inst_admin = any(
        m.institution_id == grievance.institution_id and m.is_active and m.role in (UserRoleEnum.COLLEGE_OFFICER, UserRoleEnum.INSTITUTION_HEAD)
        for m in current_user.memberships
    )
    is_bureau_member = len(get_user_bureau_unit_ids(current_user, db)) > 0

    if not (is_super or is_regulatory or is_inst_admin or is_bureau_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to refer this grievance to AICTE."
        )

    # 4. Validate Destination Unit
    unit = db.query(OrganizationalUnit).filter(OrganizationalUnit.id == payload.destination_unit_id, OrganizationalUnit.is_active == True).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination organizational unit #{payload.destination_unit_id} not found or inactive."
        )

    institution = grievance.institution
    case_ref = _generate_unique_case_reference(db)
    priority_val = payload.priority or grievance.priority

    # 5. Create AICTE Case (Bridged)
    new_case = AICTECase(
        case_reference=case_ref,
        institution_id=grievance.institution_id,
        source_grievance_id=grievance.id,
        source_type=AICTECaseSourceTypeEnum.CAMPUS_REFERRAL,
        official_reference_number=payload.official_reference_number,
        received_at=datetime.now(timezone.utc),
        complainant_type=payload.complainant_type,
        complainant_name=grievance.student.full_name if grievance.student else None,
        complainant_email=grievance.student.email if grievance.student else None,
        category=grievance.category.name if grievance.category else "Student Grievance",
        subject=f"Referred Grievance #{grievance.reference_number}: {grievance.title}",
        description=f"Referral Reason: {payload.referral_reason}\n\nOriginal Grievance Summary:\n{grievance.description}",
        status=AICTECaseStatusEnum.RECEIVED,
        current_unit_id=unit.id,
        region=institution.region if institution else None,
        priority=priority_val,
        last_action_at=datetime.now(timezone.utc),
        created_by_user_id=current_user.id,
    )
    db.add(new_case)
    db.flush()

    # 6. Record Initial INTAKE Action
    referral_action = CaseAction(
        case_id=new_case.id,
        action_type=AICTECaseActionTypeEnum.INTAKE,
        action_title="Campus Grievance Referral Registered",
        action_description=f"Referred from campus grievance #{grievance.reference_number}. Reason: {payload.referral_reason}",
        previous_status=None,
        new_status=new_case.status.value,
        unit_id=unit.id,
        performed_by_user_id=current_user.id,
        action_at=datetime.now(timezone.utc),
        remarks=f"Referred by {current_user.full_name} ({current_user.default_role.value}).",
    )
    db.add(referral_action)

    # 7. Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="GRIEVANCE_REFERRED_TO_AICTE",
        entity_type="AICTE_CASE",
        entity_id=str(new_case.id),
        details=json.dumps({
            "case_reference": new_case.case_reference,
            "source_grievance_id": grievance.id,
            "source_grievance_ref": grievance.reference_number,
            "destination_unit_code": unit.code,
            "referral_reason": payload.referral_reason
        })
    ))

    db.commit()
    db.refresh(new_case)

    # Notify receiving Bureau members of campus grievance referral
    from app.services.aicte_alert_service import AICTEAlertService
    unit_members = AICTEAlertService.get_unit_member_ids(db, unit.id)
    for uid in unit_members:
        AICTEAlertService.send_alert(
            db=db,
            recipient_id=uid,
            category="CASE_STATUS",
            severity="INFO",
            title=f"New Case Referred: {new_case.case_reference}",
            message=f"A campus grievance has been referred to {unit.code} as AICTE Case {new_case.case_reference}.",
            link=f"/aicte/cases/{new_case.id}",
            reference_id=f"REFER_{new_case.id}",
            requires_acknowledgement=False
        )

    return _map_case_to_response(new_case)


# ---------------------------------------------------------------------------
# 9. Consolidated Institution Profile & Cross-Bureau History
# ---------------------------------------------------------------------------
@router.get("/institutions/{institution_id}/consolidated-history", response_model=InstitutionConsolidatedHistoryResponse)
def get_institution_consolidated_history(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Consolidated single-pane institutional profile:
    - Official AICTE Permanent ID, Region, and Aliases.
    - Aggregated case counts across all AICTE Bureaus/Cells.
    - Cross-bureau status and workload distribution.
    - Recent chronological case roster.
    """
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution #{institution_id} not found."
        )

    # User must have Bureau access, Super Admin, Regulatory Admin, or be affiliated with this institution
    is_super = current_user.default_role == UserRoleEnum.SUPER_ADMIN
    is_regulatory = current_user.default_role == UserRoleEnum.REGULATORY_ADMIN
    is_affiliated = any(
        m.institution_id == institution_id and m.is_active
        for m in current_user.memberships
    )
    is_bureau = len(get_user_bureau_unit_ids(current_user, db)) > 0

    if not (is_super or is_regulatory or is_affiliated or is_bureau):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this institution's consolidated regulatory profile."
        )

    # Aliases
    aliases = [a.alias_name for a in institution.aliases if a.is_active]

    # Query all cases for this institution
    cases_query = db.query(AICTECase).filter(AICTECase.institution_id == institution_id)
    all_cases = cases_query.all()

    total_cases = len(all_cases)
    active_cases = sum(1 for c in all_cases if c.status not in (AICTECaseStatusEnum.DISPOSED, AICTECaseStatusEnum.CLOSED))
    disposed_cases = sum(1 for c in all_cases if c.status in (AICTECaseStatusEnum.DISPOSED, AICTECaseStatusEnum.CLOSED))

    # Aggregates by status
    status_counts = {}
    for c in all_cases:
        s_val = c.status.value
        status_counts[s_val] = status_counts.get(s_val, 0) + 1

    # Aggregates by Bureau unit
    unit_counts = {}
    for c in all_cases:
        u_code = c.current_unit.code if c.current_unit else f"Unit-{c.current_unit_id}"
        unit_counts[u_code] = unit_counts.get(u_code, 0) + 1

    # Recent cases (top 15)
    recent_cases = cases_query.order_by(desc(AICTECase.last_action_at)).limit(15).all()

    return InstitutionConsolidatedHistoryResponse(
        institution_id=institution.id,
        name=institution.name,
        code=institution.code,
        aicte_permanent_id=institution.aicte_permanent_id,
        is_aicte_verified=institution.is_aicte_verified,
        region=institution.region,
        aliases=aliases,
        total_cases=total_cases,
        active_cases=active_cases,
        disposed_cases=disposed_cases,
        status_counts=status_counts,
        unit_counts=unit_counts,
        recent_cases=[_map_case_to_response(c) for c in recent_cases]
    )
