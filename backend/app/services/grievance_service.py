import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_

from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum
from app.models.grievance import Grievance, GrievanceStatusHistory
from app.models.category import GrievanceCategory
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.assignment import GrievanceAssignment
from app.models.user import User
from app.core.permissions import (
    check_institution_access,
    check_grievance_access,
    get_user_institution_ids
)
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceStatusUpdate,
    GrievanceAssignRequest
)
from app.utils.reference import generate_reference_number
from app.services.ai_service import ai_service
from app.services.notification_service import create_notification
from app.services.audit_service import log_audit

logger = logging.getLogger("eduresolve.grievance")

ALLOWED_TRANSITIONS = {
    GrievanceStatusEnum.SUBMITTED: [
        GrievanceStatusEnum.UNDER_REVIEW,
        GrievanceStatusEnum.ASSIGNED,
        GrievanceStatusEnum.NEEDS_INFORMATION,
        GrievanceStatusEnum.REJECTED
    ],
    GrievanceStatusEnum.UNDER_REVIEW: [
        GrievanceStatusEnum.ASSIGNED,
        GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
        GrievanceStatusEnum.NEEDS_INFORMATION,
        GrievanceStatusEnum.REJECTED
    ],
    GrievanceStatusEnum.NEEDS_INFORMATION: [
        GrievanceStatusEnum.UNDER_REVIEW,
        GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS
    ],
    GrievanceStatusEnum.ASSIGNED: [
        GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
        GrievanceStatusEnum.UNDER_REVIEW,
        GrievanceStatusEnum.NEEDS_INFORMATION,
        GrievanceStatusEnum.RESOLUTION_PROPOSED
    ],
    GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS: [
        GrievanceStatusEnum.NEEDS_INFORMATION,
        GrievanceStatusEnum.RESOLUTION_PROPOSED,
        GrievanceStatusEnum.ASSIGNED,
        GrievanceStatusEnum.ESCALATED
    ],
    GrievanceStatusEnum.RESOLUTION_PROPOSED: [
        GrievanceStatusEnum.RESOLVED,
        GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
        GrievanceStatusEnum.REOPENED,
        GrievanceStatusEnum.REJECTED
    ],
    GrievanceStatusEnum.RESOLVED: [
        GrievanceStatusEnum.CLOSED,
        GrievanceStatusEnum.REOPENED
    ],
    GrievanceStatusEnum.CLOSED: [
        GrievanceStatusEnum.REOPENED
    ],
    GrievanceStatusEnum.REOPENED: [
        GrievanceStatusEnum.UNDER_REVIEW,
        GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
        GrievanceStatusEnum.ESCALATED
    ],
    GrievanceStatusEnum.ESCALATED: [
        GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
        GrievanceStatusEnum.RESOLUTION_PROPOSED,
        GrievanceStatusEnum.RESOLVED
    ],
    GrievanceStatusEnum.REJECTED: [
        GrievanceStatusEnum.REOPENED
    ]
}

class GrievanceService:
    @staticmethod
    def validate_student_institution(current_user: User, requested_institution_id: int, db: Session) -> Institution:
        """
        Derive or validate student institutional affiliation.
        Never trust unverified client-supplied institution IDs.
        """
        # If user is a student and has active institutional memberships, verify affiliation
        if current_user.default_role == UserRoleEnum.STUDENT:
            user_inst_ids = get_user_institution_ids(current_user, db)
            if user_inst_ids and requested_institution_id not in user_inst_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized: You can only submit grievances to institutions you are actively registered with."
                )

        institution = db.query(Institution).filter(
            Institution.id == requested_institution_id,
            Institution.is_active == True
        ).first()

        if not institution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected institution does not exist or is currently inactive."
            )

        return institution

    @staticmethod
    def create_grievance(req: GrievanceCreate, current_user: User, db: Session) -> Grievance:
        """
        Create a new student grievance with:
        - Strict institutional verification
        - Non-guessable public reference number
        - Safe fallback AI suggestions (AI errors never break submission)
        - Atomic status history recording
        """
        # 1. Validate institution
        institution = GrievanceService.validate_student_institution(current_user, req.institution_id, db)

        # 2. Validate category
        category = db.query(GrievanceCategory).filter(
            GrievanceCategory.id == req.category_id,
            GrievanceCategory.is_active == True
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected grievance category not found or inactive."
            )

        # 3. Generate non-guessable reference number (e.g. GRV-YYYY-XXXXXX)
        current_year = datetime.now(timezone.utc).year
        ref_num = ""
        while not ref_num:
            candidate = f"GRV-{current_year}-{secrets.token_hex(4).upper()}"
            exists = db.query(Grievance).filter(Grievance.reference_number == candidate).first()
            if not exists:
                ref_num = candidate

        # 4. Graceful AI integration (Failure of AI must NOT prevent submission)
        ai_cat = None
        ai_p = None
        ai_cat_id = None
        ai_conf = None
        ai_prio = None
        ai_explanation = None
        ai_dup_suspected = False
        ai_dup_ref = None
        suggested_officer_id = None

        try:
            ai_cat = ai_service.recommend_category(req.title, req.description, db)
            if ai_cat and ai_cat.category_id:
                cat_exists = db.query(GrievanceCategory.id).filter(GrievanceCategory.id == ai_cat.category_id).first()
                if cat_exists:
                    ai_cat_id = ai_cat.category_id
                ai_conf = ai_cat.confidence
                ai_explanation = ai_cat.explanation

            ai_p = ai_service.recommend_priority(req.title, req.description)
            if ai_p:
                ai_prio = ai_p.priority
                ai_explanation = f"{ai_explanation or ''} | Priority suggestion: {ai_p.explanation}"

            ai_dup = ai_service.detect_duplicates(req.title, req.description, req.institution_id, db)
            if ai_dup:
                ai_dup_suspected = ai_dup.is_duplicate_suspected
                ai_dup_ref = ai_dup.matches[0].reference_number if ai_dup.matches else None

            ai_route = ai_service.recommend_routing(req.category_id, req.institution_id, db)
            if ai_route:
                suggested_officer_id = ai_route.suggested_officer_id
        except Exception as e:
            logger.warning(f"AI assist service failed during grievance submission (proceeding safely): {e}")

        # Authoritative priority: client-specified or AI suggestion or NORMAL
        effective_priority = req.priority or ai_prio or GrievancePriorityEnum.NORMAL

        sla_days = category.default_sla_days or 7
        due_date = datetime.now(timezone.utc) + timedelta(days=sla_days)

        try:
            new_grievance = Grievance(
                reference_number=ref_num,
                student_id=current_user.id,
                institution_id=req.institution_id,
                category_id=req.category_id,
                subcategory=req.subcategory,
                title=req.title.strip(),
                description=req.description.strip(),
                status=GrievanceStatusEnum.SUBMITTED,
                priority=effective_priority,
                is_confidential=req.is_confidential,
                preferred_contact=req.preferred_contact,
                ai_suggested_category_id=ai_cat_id,
                ai_confidence=ai_conf,
                ai_suggested_priority=ai_prio,
                ai_explanation=ai_explanation,
                ai_duplicate_suspected=ai_dup_suspected,
                ai_duplicate_ref=ai_dup_ref,
                assigned_officer_id=suggested_officer_id,
                due_date=due_date
            )
            db.add(new_grievance)
            db.flush() # obtain new_grievance.id

            # Initial status history record
            history = GrievanceStatusHistory(
                grievance_id=new_grievance.id,
                from_status=None,
                to_status=GrievanceStatusEnum.SUBMITTED,
                changed_by_user_id=current_user.id,
                reason="Grievance submitted by student."
            )
            db.add(history)
            db.commit()
            db.refresh(new_grievance)

            # Persist AI recommendations separately in audit table
            if ai_cat or ai_p:
                ai_service.persist_recommendations(new_grievance.id, ai_cat, ai_p, db)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during grievance submission: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transaction failed while submitting grievance."
            )

        # Notify student
        create_notification(
            db=db,
            user_id=current_user.id,
            title="Grievance Submitted Successfully",
            message=f"Your grievance '{new_grievance.title}' has been registered with Reference ID #{new_grievance.reference_number}.",
            link=f"/grievances/{new_grievance.id}",
            notification_type="SUCCESS"
        )

        log_audit(
            db=db,
            action="SUBMIT_GRIEVANCE",
            entity_type="GRIEVANCE",
            user_id=current_user.id,
            entity_id=str(new_grievance.id),
            details=f"Ref: {new_grievance.reference_number}, Inst: {new_grievance.institution_id}"
        )

        return new_grievance

    @staticmethod
    def update_status(
        grievance_id: int,
        req: GrievanceStatusUpdate,
        current_user: User,
        db: Session
    ) -> Grievance:
        """
        Validate and execute a formal workflow status transition.
        Guarantees atomic status history and role verification.
        """
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

        # Permission checks
        if current_user.default_role == UserRoleEnum.STUDENT:
            if grievance.student_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
            # Students can only close or request reopen of a resolved case; they can never directly resolve, reject, or assign
            if req.to_status not in (GrievanceStatusEnum.CLOSED, GrievanceStatusEnum.REOPENED):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students can only close or request reopening of a resolved case."
                )
            if grievance.status not in (GrievanceStatusEnum.RESOLVED, GrievanceStatusEnum.CLOSED):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Action only permitted on resolved or closed cases."
                )
        else:
            # Officer / Head / Regulatory Admin / Super Admin
            if not check_grievance_access(current_user, grievance, db, require_officer_edit=True):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to modify this grievance.")

        # Check allowed workflow transition
        current_status = grievance.status
        allowed_next = ALLOWED_TRANSITIONS.get(current_status, [])

        if current_user.default_role != UserRoleEnum.SUPER_ADMIN and req.to_status not in allowed_next:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transition from {current_status.value} to {req.to_status.value}. Allowed: {[s.value for s in allowed_next]}"
            )

        now = datetime.now(timezone.utc)
        try:
            grievance.status = req.to_status
            if req.resolution_summary:
                grievance.resolution_summary = req.resolution_summary.strip()

            if req.to_status == GrievanceStatusEnum.RESOLVED:
                grievance.resolved_at = now
            elif req.to_status == GrievanceStatusEnum.CLOSED:
                grievance.closed_at = now
            elif req.to_status == GrievanceStatusEnum.REOPENED:
                grievance.closed_at = None

            history = GrievanceStatusHistory(
                grievance_id=grievance.id,
                from_status=current_status,
                to_status=req.to_status,
                changed_by_user_id=current_user.id,
                reason=req.reason.strip()
            )
            db.add(history)
            db.commit()
            db.refresh(grievance)
        except Exception as e:
            db.rollback()
            logger.error(f"Status update transaction failed for grievance #{grievance_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transaction failed while updating status."
            )

        # Notify student
        create_notification(
            db=db,
            user_id=grievance.student_id,
            title=f"Grievance Status: {req.to_status.value}",
            message=f"Case #{grievance.reference_number} changed to {req.to_status.value}. Reason: {req.reason}",
            link=f"/grievances/{grievance.id}",
            notification_type="INFO"
        )

        log_audit(
            db=db,
            action="UPDATE_GRIEVANCE_STATUS",
            entity_type="GRIEVANCE",
            user_id=current_user.id,
            entity_id=str(grievance.id),
            details=f"From {current_status.value} to {req.to_status.value}"
        )

        return grievance

    @staticmethod
    def assign_officer(
        grievance_id: int,
        req: GrievanceAssignRequest,
        current_user: User,
        db: Session
    ) -> Grievance:
        """
        Assign an officer to a grievance:
        - Verifies target officer has active authorized membership in the institution
        - Deactivates previous active assignments and records unassigned_at
        - Creates GrievanceAssignment audit record
        - Transitions status to ASSIGNED if currently SUBMITTED or UNDER_REVIEW
        """
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

        if not check_grievance_access(current_user, grievance, db, require_officer_edit=True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to assign this grievance.")

        # Verify target officer exists
        target_officer = db.query(User).filter(User.id == req.assigned_to_user_id).first()
        if not target_officer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target officer not found.")

        # Verify target officer belongs to the grievance's institution
        if not check_institution_access(target_officer, grievance.institution_id, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign case to an officer who does not belong to this institution."
            )

        now = datetime.now(timezone.utc)
        prev_status = grievance.status

        try:
            # Deactivate prior assignments with unassignment timestamp
            prior_assignments = db.query(GrievanceAssignment).filter(
                GrievanceAssignment.grievance_id == grievance.id,
                GrievanceAssignment.is_active == True
            ).all()
            for pa in prior_assignments:
                pa.is_active = False
                pa.unassigned_at = now

            # Create new active assignment
            assignment = GrievanceAssignment(
                grievance_id=grievance.id,
                assigned_to_user_id=target_officer.id,
                assigned_by_user_id=current_user.id,
                assigned_at=now,
                notes=req.notes,
                is_active=True
            )
            db.add(assignment)

            grievance.assigned_officer_id = target_officer.id
            if grievance.status in (GrievanceStatusEnum.SUBMITTED, GrievanceStatusEnum.UNDER_REVIEW):
                grievance.status = GrievanceStatusEnum.ASSIGNED

            # History entry
            history = GrievanceStatusHistory(
                grievance_id=grievance.id,
                from_status=prev_status,
                to_status=grievance.status,
                changed_by_user_id=current_user.id,
                reason=f"Assigned to officer {target_officer.full_name}. Notes: {req.notes or 'None'}"
            )
            db.add(history)
            db.commit()
            db.refresh(grievance)
        except Exception as e:
            db.rollback()
            logger.error(f"Assignment transaction failed for grievance #{grievance_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transaction failed while assigning officer."
            )

        # Notify assigned officer
        create_notification(
            db=db,
            user_id=target_officer.id,
            title="New Grievance Assigned",
            message=f"Case #{grievance.reference_number} ('{grievance.title}') has been assigned to you.",
            link=f"/grievances/{grievance.id}",
            notification_type="WARNING"
        )

        log_audit(
            db=db,
            action="ASSIGN_GRIEVANCE",
            entity_type="GRIEVANCE",
            user_id=current_user.id,
            entity_id=str(grievance.id),
            details=f"Assigned to {target_officer.full_name} (ID: {target_officer.id})"
        )

        return grievance

    @staticmethod
    def claim_grievance(grievance_id: int, current_user: User, db: Session) -> Grievance:
        """Authorized institutional officer claims an open case for themselves."""
        req = GrievanceAssignRequest(
            assigned_to_user_id=current_user.id,
            notes="Claimed by officer."
        )
        return GrievanceService.assign_officer(grievance_id, req, current_user, db)

    @staticmethod
    def reopen_grievance(grievance_id: int, reason: str, current_user: User, db: Session) -> Grievance:
        """
        Request reopening of a resolved or closed grievance.
        Permitted only when resolution is deemed unsatisfactory.
        """
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

        # Must be student owner or authorized staff
        if current_user.default_role == UserRoleEnum.STUDENT:
            if grievance.student_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        else:
            if not check_grievance_access(current_user, grievance, db):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        if grievance.status not in (GrievanceStatusEnum.RESOLVED, GrievanceStatusEnum.CLOSED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reopen a grievance currently in '{grievance.status.value}' status. Only RESOLVED or CLOSED cases can be reopened."
            )

        req = GrievanceStatusUpdate(
            to_status=GrievanceStatusEnum.REOPENED,
            reason=reason.strip()
        )
        return GrievanceService.update_status(grievance_id, req, current_user, db)

grievance_service = GrievanceService()
