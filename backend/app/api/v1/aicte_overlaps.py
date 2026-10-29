import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, select

from app.database.connection import get_db
from app.core.permissions import (
    get_current_active_user,
    get_user_bureau_unit_ids,
    check_bureau_access,
)
from app.models.enums import (
    UserRoleEnum,
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTEDetectionMethodEnum,
    AICTECaseLinkTypeEnum,
)
from app.models.user import User
from app.models.aicte_case import AICTECase
from app.models.aicte_overlap import AICTECaseOverlap, AICTECaseLink
from app.models.audit import AuditLog
from app.services.aicte_overlap_service import AICTEOverlapService
from app.schemas.aicte_overlap import (
    OverlapReviewRequest,
    ManualLinkCreateRequest,
    LinkUpdateRequest,
    AICTECaseOverlapResponse,
    AICTECaseOverlapListResponse,
    AICTECaseLinkResponse,
    OverlapHistoryItem,
)

router = APIRouter(prefix="/aicte/overlaps", tags=["AICTE Cross-Bureau Overlaps & Case Linking"])

def _format_overlap_response(overlap: AICTECaseOverlap, user: User, db: Session) -> AICTECaseOverlapResponse:
    """Format AICTECaseOverlap entity with access-safe masked case summaries."""
    try:
        reasons_dict = json.loads(overlap.match_reasons) if isinstance(overlap.match_reasons, str) else overlap.match_reasons
    except Exception:
        reasons_dict = {"raw": overlap.match_reasons}

    case_low_summary = None
    case_high_summary = None

    if overlap.case_low:
        case_low_summary = AICTEOverlapService.mask_case_summary(overlap.case_low, user, db)
    if overlap.case_high:
        case_high_summary = AICTEOverlapService.mask_case_summary(overlap.case_high, user, db)

    # Check for active link
    active_link = db.query(AICTECaseLink).filter(
        AICTECaseLink.case_id_low == overlap.case_id_low,
        AICTECaseLink.case_id_high == overlap.case_id_high,
        AICTECaseLink.is_active == True
    ).first()

    reviewer_name = None
    if overlap.reviewed_by_user:
        reviewer_name = overlap.reviewed_by_user.full_name

    return AICTECaseOverlapResponse(
        id=overlap.id,
        case_id_low=overlap.case_id_low,
        case_id_high=overlap.case_id_high,
        overlap_type=overlap.overlap_type,
        match_score=overlap.match_score,
        match_reasons=reasons_dict,
        detection_method=overlap.detection_method,
        review_status=overlap.review_status,
        detected_at=overlap.detected_at,
        reviewed_at=overlap.reviewed_at,
        reviewed_by_user_id=overlap.reviewed_by_user_id,
        reviewed_by_name=reviewer_name,
        review_notes=overlap.review_notes,
        case_low=case_low_summary,
        case_high=case_high_summary,
        active_link_type=active_link.link_type.value if active_link else None,
        created_at=overlap.created_at,
        updated_at=overlap.updated_at,
    )


# ---------------------------------------------------------------------------
# 1. Run Bounded Overlap Detection for a Case
# ---------------------------------------------------------------------------
@router.post("/detect/{case_id}", response_model=List[AICTECaseOverlapResponse])
def detect_case_overlaps(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger bounded overlap detection for an AICTE case:
    - Scans eligible cases concerning the same institution / verified PID.
    - Evaluates multiple independent explainable matching signals.
    - Updates match reasons without erasing previous human review decisions.
    - User must hold membership in the handling Bureau or be SuperAdmin.
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
            detail="Access forbidden: you do not possess membership in the responsible Bureau."
        )

    overlaps = AICTEOverlapService.detect_overlaps_for_case(case_id, db, current_user)
    return [_format_overlap_response(o, current_user, db) for o in overlaps]


# ---------------------------------------------------------------------------
# 2. List Overlap Candidates (Queue with Filters & Pagination)
# ---------------------------------------------------------------------------
@router.get("", response_model=AICTECaseOverlapListResponse)
def list_overlap_candidates(
    review_status: Optional[AICTEOverlapReviewStatusEnum] = None,
    overlap_type: Optional[AICTEOverlapTypeEnum] = None,
    unit_id: Optional[int] = None,
    institution_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List AICTE case overlap candidates:
    - SuperAdmin sees candidates nationwide across all Bureaus.
    - Bureau members see candidates where at least one case belongs to their authorized units.
    - Unauthorized users (students, non-bureau college officers) are denied.
    """
    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    if not authorized_unit_ids and current_user.default_role != UserRoleEnum.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess active AICTE Bureau membership."
        )

    query = db.query(AICTECaseOverlap)

    # Unit boundary scoping: User must belong to either case_low's unit or case_high's unit
    if current_user.default_role != UserRoleEnum.SUPER_ADMIN:
        allowed_case_ids_select = select(AICTECase.id).filter(AICTECase.current_unit_id.in_(authorized_unit_ids))
        query = query.filter(
            or_(
                AICTECaseOverlap.case_id_low.in_(allowed_case_ids_select),
                AICTECaseOverlap.case_id_high.in_(allowed_case_ids_select)
            )
        )

    if review_status:
        query = query.filter(AICTECaseOverlap.review_status == review_status)

    if overlap_type:
        query = query.filter(AICTECaseOverlap.overlap_type == overlap_type)

    if unit_id:
        if current_user.default_role != UserRoleEnum.SUPER_ADMIN and unit_id not in authorized_unit_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: requested unit is outside your authorized jurisdiction."
            )
        unit_case_ids_select = select(AICTECase.id).filter(AICTECase.current_unit_id == unit_id)
        query = query.filter(
            or_(
                AICTECaseOverlap.case_id_low.in_(unit_case_ids_select),
                AICTECaseOverlap.case_id_high.in_(unit_case_ids_select)
            )
        )

    if institution_id:
        inst_case_ids_select = select(AICTECase.id).filter(AICTECase.institution_id == institution_id)
        query = query.filter(
            or_(
                AICTECaseOverlap.case_id_low.in_(inst_case_ids_select),
                AICTECaseOverlap.case_id_high.in_(inst_case_ids_select)
            )
        )

    total = query.count()
    overlaps = query.order_by(desc(AICTECaseOverlap.detected_at)).offset((page - 1) * page_size).limit(page_size).all()

    return AICTECaseOverlapListResponse(
        items=[_format_overlap_response(o, current_user, db) for o in overlaps],
        total=total,
        page=page,
        page_size=page_size
    )


# ---------------------------------------------------------------------------
# 3. Retrieve Overlap Detail with Shielded Case Summaries
# ---------------------------------------------------------------------------
@router.get("/{overlap_id}", response_model=AICTECaseOverlapResponse)
def get_overlap_detail(
    overlap_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve candidate overlap record with explainable matching signals:
    - Sensitive case details for foreign bureaus are masked unless authorized.
    """
    overlap = db.query(AICTECaseOverlap).filter(AICTECaseOverlap.id == overlap_id).first()
    if not overlap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Overlap record #{overlap_id} not found."
        )

    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    has_low_access = overlap.case_low and overlap.case_low.current_unit_id in authorized_unit_ids
    has_high_access = overlap.case_high and overlap.case_high.current_unit_id in authorized_unit_ids

    if current_user.default_role != UserRoleEnum.SUPER_ADMIN and not (has_low_access or has_high_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized membership in either handling Bureau."
        )

    return _format_overlap_response(overlap, current_user, db)


# ---------------------------------------------------------------------------
# 4. Human Review Decision Workflow
# ---------------------------------------------------------------------------
@router.post("/{overlap_id}/review", response_model=AICTECaseOverlapResponse)
def review_overlap_candidate(
    overlap_id: int,
    payload: OverlapReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Commit human review verdict on an overlap candidate:
    - Action: CONFIRM_DUPLICATE, CONFIRM_RELATED, REJECT, or DEFERRED.
    - Requires non-empty review justification notes.
    - If CONFIRMED_DUPLICATE / CONFIRMED_RELATED: creates an administrative link in aicte_case_links.
    - CRITICAL RULE: NEVER merges, closes, or alters official case statuses.
    - If REJECTED: deactivates any existing link; both cases remain completely independent.
    - Preserves audit trail atomically.
    """
    overlap = db.query(AICTECaseOverlap).filter(AICTECaseOverlap.id == overlap_id).with_for_update().first()
    if not overlap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Overlap candidate #{overlap_id} not found."
        )

    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    has_low_access = overlap.case_low and overlap.case_low.current_unit_id in authorized_unit_ids
    has_high_access = overlap.case_high and overlap.case_high.current_unit_id in authorized_unit_ids

    if current_user.default_role != UserRoleEnum.SUPER_ADMIN and not (has_low_access or has_high_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: review requires active membership in at least one of the involved Bureaus."
        )

    prev_status = overlap.review_status
    new_status = payload.action
    review_notes = payload.review_notes.strip()

    # Update candidate review fields
    overlap.review_status = new_status
    overlap.reviewed_at = datetime.now(timezone.utc)
    overlap.reviewed_by_user_id = current_user.id
    overlap.review_notes = review_notes
    overlap.updated_at = datetime.now(timezone.utc)

    # Administrative case link handling
    if new_status in (AICTEOverlapReviewStatusEnum.CONFIRMED_DUPLICATE, AICTEOverlapReviewStatusEnum.CONFIRMED_RELATED):
        target_link_type = (
            AICTECaseLinkTypeEnum.DUPLICATE_OF 
            if new_status == AICTEOverlapReviewStatusEnum.CONFIRMED_DUPLICATE 
            else AICTECaseLinkTypeEnum.RELATED_TO
        )

        existing_link = db.query(AICTECaseLink).filter(
            AICTECaseLink.case_id_low == overlap.case_id_low,
            AICTECaseLink.case_id_high == overlap.case_id_high,
            AICTECaseLink.link_type == target_link_type
        ).first()

        if existing_link:
            existing_link.is_active = True
            existing_link.notes = review_notes
            existing_link.source_overlap_id = overlap.id
            existing_link.updated_at = datetime.now(timezone.utc)
        else:
            new_link = AICTECaseLink(
                case_id_low=overlap.case_id_low,
                case_id_high=overlap.case_id_high,
                link_type=target_link_type,
                source_overlap_id=overlap.id,
                created_by_user_id=current_user.id,
                notes=review_notes,
                is_active=True
            )
            db.add(new_link)

    elif new_status == AICTEOverlapReviewStatusEnum.REJECTED:
        # Deactivate any active links between this pair
        active_links = db.query(AICTECaseLink).filter(
            AICTECaseLink.case_id_low == overlap.case_id_low,
            AICTECaseLink.case_id_high == overlap.case_id_high,
            AICTECaseLink.is_active == True
        ).all()
        for lnk in active_links:
            lnk.is_active = False
            lnk.updated_at = datetime.now(timezone.utc)

    # Atomic audit logging
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="AICTE_OVERLAP_REVIEWED",
        entity_type="AICTE_OVERLAP",
        entity_id=str(overlap.id),
        details=json.dumps({
            "previous_status": prev_status.value if hasattr(prev_status, 'value') else prev_status,
            "new_status": new_status.value if hasattr(new_status, 'value') else new_status,
            "review_notes": review_notes,
            "case_id_low": overlap.case_id_low,
            "case_id_high": overlap.case_id_high
        })
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(overlap)

    # Notify involved bureaus of review decision
    from app.services.aicte_alert_service import AICTEAlertService
    recipients = set(AICTEAlertService.get_unit_member_ids(db, overlap.case_low.current_unit_id))
    recipients.update(AICTEAlertService.get_unit_member_ids(db, overlap.case_high.current_unit_id))
    for uid in recipients:
        AICTEAlertService.send_alert(
            db=db,
            recipient_id=uid,
            category="OVERLAP_DECISION",
            severity="INFO",
            title=f"Overlap Reviewed: {overlap.case_low.case_reference} & {overlap.case_high.case_reference}",
            message=f"Overlap review concluded ({new_status.value}) by {current_user.full_name}.",
            link=f"/aicte/overlaps/{overlap.id}",
            reference_id=f"OVERLAP_REVIEW_{overlap.id}_{new_status.value}",
            requires_acknowledgement=False
        )

    return _format_overlap_response(overlap, current_user, db)


# ---------------------------------------------------------------------------
# 5. Overlap Review History
# ---------------------------------------------------------------------------
@router.get("/{overlap_id}/history", response_model=List[OverlapHistoryItem])
def get_overlap_history(
    overlap_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve chronological audit trail of human review verdicts and detections."""
    overlap = db.query(AICTECaseOverlap).filter(AICTECaseOverlap.id == overlap_id).first()
    if not overlap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Overlap record #{overlap_id} not found."
        )

    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "AICTE_OVERLAP",
        AuditLog.entity_id == str(overlap_id)
    ).order_by(AuditLog.created_at.asc()).all()

    history: List[OverlapHistoryItem] = []
    for log in logs:
        try:
            details_obj = json.loads(log.details) if log.details else {}
        except Exception:
            details_obj = {"raw": log.details}

        history.append(OverlapHistoryItem(
            id=log.id,
            action=log.action,
            actor_name=log.user.full_name if log.user else "System Process",
            timestamp=log.created_at,
            details=details_obj
        ))

    return history


# ---------------------------------------------------------------------------
# 6. List Case Relationships (Confirmed Links on Case Docket)
# ---------------------------------------------------------------------------
@router.get("/cases/{case_id}/links", response_model=List[AICTECaseLinkResponse])
def get_case_links(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List confirmed administrative links (DUPLICATE_OF, RELATED_TO) for an AICTE case:
    - Returned cases retain independent case references and statuses.
    """
    case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AICTE Case #{case_id} not found."
        )

    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    if current_user.default_role != UserRoleEnum.SUPER_ADMIN and case.current_unit_id not in authorized_unit_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized membership in the handling Bureau."
        )

    links = db.query(AICTECaseLink).filter(
        or_(AICTECaseLink.case_id_low == case_id, AICTECaseLink.case_id_high == case_id),
        AICTECaseLink.is_active == True
    ).order_by(AICTECaseLink.created_at.desc()).all()

    results: List[AICTECaseLinkResponse] = []
    for lnk in links:
        other_id = lnk.case_id_high if lnk.case_id_low == case_id else lnk.case_id_low
        other_case = db.query(AICTECase).filter(AICTECase.id == other_id).first()
        if not other_case:
            continue

        results.append(AICTECaseLinkResponse(
            id=lnk.id,
            case_id_low=lnk.case_id_low,
            case_id_high=lnk.case_id_high,
            linked_case_id=other_case.id,
            linked_case_reference=other_case.case_reference,
            linked_case_subject=other_case.subject,
            linked_case_category=other_case.category,
            linked_case_unit_code=other_case.current_unit.code if other_case.current_unit else None,
            linked_case_status=other_case.status.value if hasattr(other_case.status, 'value') else other_case.status,
            link_type=lnk.link_type,
            source_overlap_id=lnk.source_overlap_id,
            created_by_user_id=lnk.created_by_user_id,
            created_by_name=lnk.created_by_user.full_name if lnk.created_by_user else None,
            notes=lnk.notes,
            is_active=lnk.is_active,
            created_at=lnk.created_at,
        ))

    return results


# ---------------------------------------------------------------------------
# 7. Create Manual Case Relationship Link
# ---------------------------------------------------------------------------
@router.post("/cases/{case_id}/links", response_model=AICTECaseLinkResponse, status_code=status.HTTP_201_CREATED)
def create_manual_case_link(
    case_id: int,
    payload: ManualLinkCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually link two related AICTE cases:
    - Enforces canonical pair ordering (case_id_low < case_id_high).
    - Prevents self-linking.
    - Preserves independent official dockets and statuses.
    """
    if case_id == payload.target_case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot link a case to itself."
        )

    case_a = db.query(AICTECase).filter(AICTECase.id == case_id).first()
    case_b = db.query(AICTECase).filter(AICTECase.id == payload.target_case_id).first()

    if not case_a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case #{case_id} not found.")
    if not case_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target Case #{payload.target_case_id} not found.")

    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    if current_user.default_role != UserRoleEnum.SUPER_ADMIN and case_a.current_unit_id not in authorized_unit_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized membership in the handling Bureau."
        )

    low_id = min(case_id, payload.target_case_id)
    high_id = max(case_id, payload.target_case_id)

    # Check for existing link
    existing_link = db.query(AICTECaseLink).filter(
        AICTECaseLink.case_id_low == low_id,
        AICTECaseLink.case_id_high == high_id,
        AICTECaseLink.link_type == payload.link_type
    ).first()

    if existing_link:
        existing_link.is_active = True
        if payload.notes:
            existing_link.notes = payload.notes.strip()
        existing_link.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing_link)
        link_record = existing_link
    else:
        new_link = AICTECaseLink(
            case_id_low=low_id,
            case_id_high=high_id,
            link_type=payload.link_type,
            created_by_user_id=current_user.id,
            notes=payload.notes.strip() if payload.notes else None,
            is_active=True
        )
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        link_record = new_link

    AuditLog(
        user_id=current_user.id,
        action="AICTE_CASE_LINK_CREATED",
        entity_type="AICTE_CASE_LINK",
        entity_id=str(link_record.id),
        details=json.dumps({
            "case_id_low": low_id,
            "case_id_high": high_id,
            "link_type": payload.link_type.value
        })
    )
    db.commit()

    other_case = case_b if case_id == low_id else case_a
    return AICTECaseLinkResponse(
        id=link_record.id,
        case_id_low=link_record.case_id_low,
        case_id_high=link_record.case_id_high,
        linked_case_id=other_case.id,
        linked_case_reference=other_case.case_reference,
        linked_case_subject=other_case.subject,
        linked_case_category=other_case.category,
        linked_case_unit_code=other_case.current_unit.code if other_case.current_unit else None,
        linked_case_status=other_case.status.value if hasattr(other_case.status, 'value') else other_case.status,
        link_type=link_record.link_type,
        source_overlap_id=link_record.source_overlap_id,
        created_by_user_id=link_record.created_by_user_id,
        created_by_name=current_user.full_name,
        notes=link_record.notes,
        is_active=link_record.is_active,
        created_at=link_record.created_at,
    )


# ---------------------------------------------------------------------------
# 8. Update or Deactivate Case Relationship Link
# ---------------------------------------------------------------------------
@router.patch("/links/{link_id}", response_model=AICTECaseLinkResponse)
def update_case_link(
    link_id: int,
    payload: LinkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate or update notes on an administrative case link."""
    link_record = db.query(AICTECaseLink).filter(AICTECaseLink.id == link_id).first()
    if not link_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case link #{link_id} not found."
        )

    case_low = db.query(AICTECase).filter(AICTECase.id == link_record.case_id_low).first()
    case_high = db.query(AICTECase).filter(AICTECase.id == link_record.case_id_high).first()

    authorized_unit_ids = get_user_bureau_unit_ids(current_user, db)
    has_low = case_low and case_low.current_unit_id in authorized_unit_ids
    has_high = case_high and case_high.current_unit_id in authorized_unit_ids

    if current_user.default_role != UserRoleEnum.SUPER_ADMIN and not (has_low or has_high):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized membership in either handling Bureau."
        )

    if payload.is_active is not None:
        link_record.is_active = payload.is_active
    if payload.notes is not None:
        link_record.notes = payload.notes.strip() or None

    link_record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(link_record)

    AuditLog(
        user_id=current_user.id,
        action="AICTE_CASE_LINK_UPDATED",
        entity_type="AICTE_CASE_LINK",
        entity_id=str(link_record.id),
        details=json.dumps({
            "is_active": link_record.is_active,
            "notes": link_record.notes
        })
    )
    db.commit()

    other_case = case_high if case_low else case_high
    return AICTECaseLinkResponse(
        id=link_record.id,
        case_id_low=link_record.case_id_low,
        case_id_high=link_record.case_id_high,
        linked_case_id=other_case.id,
        linked_case_reference=other_case.case_reference,
        linked_case_subject=other_case.subject,
        linked_case_category=other_case.category,
        linked_case_unit_code=other_case.current_unit.code if other_case.current_unit else None,
        linked_case_status=other_case.status.value if hasattr(other_case.status, 'value') else other_case.status,
        link_type=link_record.link_type,
        source_overlap_id=link_record.source_overlap_id,
        created_by_user_id=link_record.created_by_user_id,
        created_by_name=link_record.created_by_user.full_name if link_record.created_by_user else None,
        notes=link_record.notes,
        is_active=link_record.is_active,
        created_at=link_record.created_at,
    )
