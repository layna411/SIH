from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_

from app.database.connection import get_db
from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum, EscalationLevelEnum
from app.models.grievance import Grievance, GrievanceStatusHistory
from app.models.category import GrievanceCategory
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.user import User
from app.models.assignment import GrievanceAssignment
from app.models.escalation import GrievanceEscalation
from app.models.communication import GrievanceMessage, GrievanceInternalNote
from app.models.attachment import GrievanceAttachment
from app.models.feedback import GrievanceFeedback
from app.core.permissions import (
    get_current_user,
    check_institution_access,
    check_grievance_access,
    get_user_institution_ids,
    require_roles
)
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceStatusUpdate,
    GrievanceAssignRequest,
    GrievanceReopenRequest,
    GrievanceEscalateRequest,
    GrievanceAssignmentResponse,
    BatchEscalationResponse,
    GrievanceSummaryResponse,
    GrievanceDetailResponse,
    GrievanceStatusHistoryResponse,
    GrievanceMessageResponse,
    GrievanceInternalNoteResponse,
    GrievanceAttachmentResponse,
    GrievanceFeedbackResponse,
    GrievancePublicTrackResponse
)
from app.services.grievance_service import grievance_service, ALLOWED_TRANSITIONS
from app.services.escalation_service import escalation_service

router = APIRouter(prefix="/grievances", tags=["Grievances"])

def build_summary(g: Grievance) -> GrievanceSummaryResponse:
    return GrievanceSummaryResponse(
        id=g.id,
        reference_number=g.reference_number,
        institution_id=g.institution_id,
        institution_name=g.institution.name if g.institution else "Unknown",
        category_id=g.category_id,
        category_name=g.category.name if g.category else "Uncategorized",
        subcategory=g.subcategory,
        title=g.title,
        status=g.status,
        priority=g.priority,
        is_confidential=g.is_confidential,
        assigned_officer_id=g.assigned_officer_id,
        assigned_officer_name=g.assigned_officer.full_name if g.assigned_officer else None,
        due_date=g.due_date,
        created_at=g.created_at,
        updated_at=g.updated_at
    )

@router.post("", response_model=GrievanceDetailResponse, status_code=status.HTTP_201_CREATED)
def submit_grievance(
    req: GrievanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a new student grievance.
    - Validates institutional affiliation
    - Assigns unique public reference number
    - Safely suggests categories and priority via AI without blocking on AI failure
    """
    new_grievance = grievance_service.create_grievance(req, current_user, db)
    return get_grievance(new_grievance.id, current_user, db)

@router.get("", response_model=List[GrievanceSummaryResponse])
def list_grievances(
    status: Optional[GrievanceStatusEnum] = None,
    category_id: Optional[int] = None,
    priority: Optional[GrievancePriorityEnum] = None,
    institution_id: Optional[int] = None,
    assigned_officer_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List grievances with strict role-based multi-tenant boundary checks:
    - STUDENT: only their own grievances
    - COLLEGE_OFFICER / INSTITUTION_HEAD: only their authorized institution(s)
    - REGULATORY_ADMIN: only institutions within assigned jurisdiction states
    - SUPER_ADMIN: platform-wide access
    """
    query = db.query(Grievance)

    if current_user.default_role == UserRoleEnum.STUDENT:
        query = query.filter(Grievance.student_id == current_user.id)
    elif current_user.default_role in (UserRoleEnum.COLLEGE_OFFICER, UserRoleEnum.INSTITUTION_HEAD):
        user_institutions = get_user_institution_ids(current_user, db)
        query = query.filter(Grievance.institution_id.in_(user_institutions))
    elif current_user.default_role == UserRoleEnum.REGULATORY_ADMIN:
        jurisdictions = db.query(RegulatoryJurisdiction).filter(
            RegulatoryJurisdiction.user_id == current_user.id,
            RegulatoryJurisdiction.is_active == True
        ).all()
        assigned_states = [j.state.strip().lower() for j in jurisdictions if j.state]
        assigned_inst_ids = [j.institution_id for j in jurisdictions if j.institution_id]
        
        institutions = db.query(Institution).all()
        allowed_inst_ids = set(assigned_inst_ids)
        for inst in institutions:
            if inst.state and inst.state.strip().lower() in assigned_states:
                allowed_inst_ids.add(inst.id)
        query = query.filter(Grievance.institution_id.in_(list(allowed_inst_ids)))

    # Filters
    if status:
        query = query.filter(Grievance.status == status)
    if category_id:
        query = query.filter(Grievance.category_id == category_id)
    if priority:
        query = query.filter(Grievance.priority == priority)
    if assigned_officer_id:
        query = query.filter(Grievance.assigned_officer_id == assigned_officer_id)
    if from_date:
        query = query.filter(Grievance.created_at >= from_date)
    if to_date:
        query = query.filter(Grievance.created_at <= to_date)
    if institution_id:
        if check_institution_access(current_user, institution_id, db):
            query = query.filter(Grievance.institution_id == institution_id)
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to requested institution.")
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Grievance.title.ilike(search_pattern),
                Grievance.reference_number.ilike(search_pattern),
                Grievance.description.ilike(search_pattern)
            )
        )

    grievances = query.order_by(Grievance.created_at.desc()).offset(offset).limit(limit).all()
    return [build_summary(g) for g in grievances]

@router.get("/track/{reference_number}", response_model=GrievancePublicTrackResponse)
def track_grievance_public(reference_number: str, db: Session = Depends(get_db)):
    """
    Public tracking by reference number without authentication.
    Returns status, category, institution, and workflow timeline while shielding personal student details.
    """
    g = db.query(Grievance).filter(Grievance.reference_number == reference_number.strip().upper()).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found with the provided reference number.")

    history_list = []
    for h in g.status_history:
        history_list.append(GrievanceStatusHistoryResponse(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by_name=h.changed_by.full_name if h.changed_by else "System",
            reason=h.reason,
            created_at=h.created_at
        ))

    return GrievancePublicTrackResponse(
        reference_number=g.reference_number,
        institution_name=g.institution.name if g.institution else "Institution",
        category_name=g.category.name if g.category else "General",
        title=g.title,
        status=g.status,
        priority=g.priority,
        created_at=g.created_at,
        updated_at=g.updated_at,
        resolution_summary=g.resolution_summary,
        status_history=history_list
    )

@router.post("/escalations/process-overdue", response_model=BatchEscalationResponse)
def process_overdue_escalations(
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD)),
    db: Session = Depends(get_db)
):
    """
    Callable administrative service to process and auto-escalate overdue grievances.
    Restricted to Super Administrators and Institution Heads.
    """
    escalated_refs = escalation_service.process_overdue_escalations(db, actor=current_user)
    return BatchEscalationResponse(
        escalated_count=len(escalated_refs),
        escalated_reference_numbers=escalated_refs,
        processed_at=datetime.now(timezone.utc)
    )

@router.get("/{id}", response_model=GrievanceDetailResponse)
def get_grievance(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed grievance case information.
    Ensures confidentiality: strictly hides internal notes and internal attachments from students!
    """
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: unauthorized to view this grievance.")

    is_student = current_user.default_role == UserRoleEnum.STUDENT

    # Format status history
    history_list = []
    for h in grievance.status_history:
        history_list.append(GrievanceStatusHistoryResponse(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by_name=h.changed_by.full_name if h.changed_by else "System",
            reason=h.reason,
            created_at=h.created_at
        ))

    # Format messages
    message_list = []
    for m in grievance.messages:
        if is_student and not m.is_student_visible:
            continue
        message_list.append(GrievanceMessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            sender_name=m.sender.full_name if m.sender else "User",
            sender_role=m.sender.default_role.value if m.sender else "MEMBER",
            message=m.message,
            is_student_visible=m.is_student_visible,
            created_at=m.created_at
        ))

    # Format internal notes (ONLY FOR OFFICERS / HEADS / SUPER ADMIN)
    internal_note_list = []
    if not is_student:
        for n in grievance.internal_notes:
            internal_note_list.append(GrievanceInternalNoteResponse(
                id=n.id,
                author_id=n.author_id,
                author_name=n.author.full_name if n.author else "Officer",
                note=n.note,
                created_at=n.created_at
            ))

    # Format attachments
    attachment_list = []
    for a in grievance.attachments:
        if is_student and a.is_internal_only:
            continue
        attachment_list.append(GrievanceAttachmentResponse(
            id=a.id,
            file_name=a.file_name,
            file_size_bytes=a.file_size_bytes,
            content_type=a.content_type,
            is_internal_only=a.is_internal_only,
            created_at=a.created_at
        ))

    # Format feedback
    feedback_resp = None
    if grievance.feedback:
        feedback_resp = GrievanceFeedbackResponse(
            id=grievance.feedback.id,
            rating=grievance.feedback.rating,
            satisfies_resolution=grievance.feedback.satisfies_resolution,
            comments=grievance.feedback.comments,
            created_at=grievance.feedback.created_at
        )

    # Mask student name if marked confidential and viewer is not super admin or grievance student
    display_student_name = grievance.student.full_name if grievance.student else None
    display_student_email = grievance.student.email if grievance.student else None
    display_student_id_num = grievance.student.student_id_number if grievance.student else None

    if grievance.is_confidential and current_user.default_role not in (UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD):
        if current_user.id != grievance.student_id:
            display_student_name = "Confidential Student"
            display_student_email = "[Protected]"
            display_student_id_num = "[Protected]"

    return GrievanceDetailResponse(
        id=grievance.id,
        reference_number=grievance.reference_number,
        institution_id=grievance.institution_id,
        institution_name=grievance.institution.name if grievance.institution else "Unknown",
        category_id=grievance.category_id,
        category_name=grievance.category.name if grievance.category else "Uncategorized",
        subcategory=grievance.subcategory,
        title=grievance.title,
        description=grievance.description,
        status=grievance.status,
        priority=grievance.priority,
        is_confidential=grievance.is_confidential,
        preferred_contact=grievance.preferred_contact,
        student_id=grievance.student_id,
        student_name=display_student_name,
        student_email=display_student_email,
        student_id_number=display_student_id_num,
        assigned_officer_name=grievance.assigned_officer.full_name if grievance.assigned_officer else None,
        due_date=grievance.due_date,
        resolution_summary=grievance.resolution_summary,
        resolved_at=grievance.resolved_at,
        closed_at=grievance.closed_at,
        ai_suggested_category_id=grievance.ai_suggested_category_id,
        ai_suggested_category_name=grievance.ai_suggested_category.name if grievance.ai_suggested_category else None,
        ai_confidence=grievance.ai_confidence,
        ai_suggested_priority=grievance.ai_suggested_priority,
        ai_explanation=grievance.ai_explanation,
        ai_duplicate_suspected=grievance.ai_duplicate_suspected,
        ai_duplicate_ref=grievance.ai_duplicate_ref,
        created_at=grievance.created_at,
        updated_at=grievance.updated_at,
        status_history=history_list,
        messages=message_list,
        internal_notes=internal_note_list,
        attachments=attachment_list,
        feedback=feedback_resp
    )

@router.get("/{id}/timeline", response_model=List[GrievanceStatusHistoryResponse])
def get_grievance_timeline(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View permitted status history timeline for a grievance case."""
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    history = db.query(GrievanceStatusHistory).filter(
        GrievanceStatusHistory.grievance_id == grievance.id
    ).order_by(GrievanceStatusHistory.id.desc()).all()

    return [
        GrievanceStatusHistoryResponse(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by_name=h.changed_by.full_name if h.changed_by else "System",
            reason=h.reason,
            created_at=h.created_at
        )
        for h in history
    ]

@router.put("/{id}/status", response_model=GrievanceDetailResponse)
def update_grievance_status(
    id: int,
    req: GrievanceStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform a valid workflow status transition with mandatory reason.
    Guarantees atomic status history and role verification.
    """
    grievance_service.update_status(id, req, current_user, db)
    return get_grievance(id, current_user, db)

@router.post("/{id}/assign", response_model=GrievanceDetailResponse)
def assign_grievance(
    id: int,
    req: GrievanceAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign or reassign case to an authorized institutional officer with audit history."""
    grievance_service.assign_officer(id, req, current_user, db)
    return get_grievance(id, current_user, db)

@router.post("/{id}/claim", response_model=GrievanceDetailResponse)
def claim_grievance(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Authorized institutional officer claims an open grievance for themselves."""
    grievance_service.claim_grievance(id, current_user, db)
    return get_grievance(id, current_user, db)

@router.get("/{id}/assignments", response_model=List[GrievanceAssignmentResponse])
def get_assignment_history(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View assignment and reassignment audit history (Officers/Heads/SuperAdmin only)."""
    if current_user.default_role == UserRoleEnum.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students cannot view internal assignment history.")

    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db, require_officer_edit=True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return [
        GrievanceAssignmentResponse(
            id=a.id,
            assigned_to_user_id=a.assigned_to_user_id,
            assigned_to_name=a.assigned_to.full_name if a.assigned_to else "Officer",
            assigned_by_user_id=a.assigned_by_user_id,
            assigned_by_name=a.assigned_by.full_name if a.assigned_by else "Staff",
            assigned_at=a.assigned_at,
            unassigned_at=a.unassigned_at,
            notes=a.notes,
            is_active=a.is_active
        )
        for a in grievance.assignments
    ]

@router.post("/{id}/reopen-request", response_model=GrievanceDetailResponse)
def request_reopening(
    id: int,
    req: GrievanceReopenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request case reopening for a resolved or closed grievance.
    Permitted only when resolution is deemed unsatisfactory.
    """
    grievance_service.reopen_grievance(id, req.reason, current_user, db)
    return get_grievance(id, current_user, db)

@router.post("/{id}/escalate", response_model=GrievanceDetailResponse)
def escalate_grievance(
    id: int,
    reason: Optional[str] = Query(None, min_length=10),
    level: EscalationLevelEnum = EscalationLevelEnum.LEVEL_2_INSTITUTION_HEAD,
    body: Optional[GrievanceEscalateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Escalate a grievance due to delay, inaction, or unsatisfactory handling.
    Accepts reason and level either via query params or request body.
    """
    effective_reason = body.reason if (body and body.reason) else reason
    effective_level = body.level if (body and body.level) else level

    if not effective_reason or len(effective_reason.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A detailed escalation reason (at least 10 characters) is required."
        )

    escalation_service.escalate_grievance(
        grievance_id=id,
        reason=effective_reason.strip(),
        level=effective_level,
        actor=current_user,
        db=db
    )
    return get_grievance(id, current_user, db)
