import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum, EscalationLevelEnum
from app.models.grievance import Grievance, GrievanceStatusHistory
from app.models.escalation import GrievanceEscalation
from app.models.user import User
from app.core.permissions import check_grievance_access
from app.services.notification_service import create_notification
from app.services.audit_service import log_audit

logger = logging.getLogger("eduresolve.escalation")

class EscalationService:
    @staticmethod
    def escalate_grievance(
        grievance_id: int,
        reason: str,
        level: EscalationLevelEnum,
        actor: User,
        db: Session
    ) -> Grievance:
        """
        Manually escalate a grievance due to procedural delays or supervisory requirement.
        """
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

        # Ensure actor has access to this grievance
        if not check_grievance_access(actor, grievance, db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: unauthorized to escalate this grievance.")

        # Cannot escalate already resolved, closed, or rejected cases
        if grievance.status in (GrievanceStatusEnum.RESOLVED, GrievanceStatusEnum.CLOSED, GrievanceStatusEnum.REJECTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot escalate a case that is already {grievance.status.value}."
            )

        previous_status = grievance.status
        prev_scope = "COLLEGE_OFFICER"
        new_scope = "INSTITUTION_HEAD" if level == EscalationLevelEnum.LEVEL_2_INSTITUTION_HEAD else "REGULATORY_ADMIN"

        try:
            escalation = GrievanceEscalation(
                grievance_id=grievance.id,
                escalated_by_id=actor.id,
                escalation_level=level,
                reason=reason.strip(),
                status="PENDING",
                previous_handling_scope=prev_scope,
                new_handling_scope=new_scope
            )
            db.add(escalation)

            grievance.status = GrievanceStatusEnum.ESCALATED
            grievance.priority = GrievancePriorityEnum.URGENT

            history = GrievanceStatusHistory(
                grievance_id=grievance.id,
                from_status=previous_status,
                to_status=GrievanceStatusEnum.ESCALATED,
                changed_by_user_id=actor.id,
                reason=f"Escalation ({level.value}): {reason.strip()}"
            )
            db.add(history)
            db.commit()
            db.refresh(grievance)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record escalation for grievance #{grievance.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transaction failed while recording escalation."
            )

        # Notify student
        create_notification(
            db=db,
            user_id=grievance.student_id,
            title=f"Grievance Escalated to {level.value}",
            message=f"Case #{grievance.reference_number} has been escalated for senior supervisory review. Reason: {reason.strip()}",
            link=f"/grievances/{grievance.id}",
            notification_type="WARNING"
        )

        log_audit(
            db=db,
            action="ESCALATE_GRIEVANCE",
            entity_type="GRIEVANCE",
            user_id=actor.id,
            entity_id=str(grievance.id),
            details=f"Escalated to {level.value}. Reason: {reason.strip()}"
        )

        return grievance

    @staticmethod
    def process_overdue_escalations(db: Session, actor: Optional[User] = None) -> List[str]:
        """
        Scan active grievances that have exceeded their SLA due date and auto-escalate them.
        Escalation indicates supervisory review is required due to elapsed time, not proven misconduct.
        """
        now = datetime.now(timezone.utc)
        active_statuses = [
            GrievanceStatusEnum.SUBMITTED,
            GrievanceStatusEnum.UNDER_REVIEW,
            GrievanceStatusEnum.ASSIGNED,
            GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
            GrievanceStatusEnum.NEEDS_INFORMATION
        ]

        overdue_grievances = db.query(Grievance).filter(
            Grievance.due_date < now,
            Grievance.status.in_(active_statuses)
        ).all()

        escalated_refs = []
        for g in overdue_grievances:
            prev_status = g.status
            g.status = GrievanceStatusEnum.ESCALATED
            g.priority = GrievancePriorityEnum.URGENT

            escalation = GrievanceEscalation(
                grievance_id=g.id,
                escalated_by_id=actor.id if actor else None,
                escalation_level=EscalationLevelEnum.LEVEL_2_INSTITUTION_HEAD,
                reason="Automated escalation: Case resolution overdue past configured SLA deadline.",
                status="PENDING",
                previous_handling_scope="COLLEGE_OFFICER",
                new_handling_scope="INSTITUTION_HEAD"
            )
            db.add(escalation)

            history = GrievanceStatusHistory(
                grievance_id=g.id,
                from_status=prev_status,
                to_status=GrievanceStatusEnum.ESCALATED,
                changed_by_user_id=actor.id if actor else g.student_id,
                reason="Automated SLA escalation: Resolution due date exceeded."
            )
            db.add(history)
            escalated_refs.append(g.reference_number)

            create_notification(
                db=db,
                user_id=g.student_id,
                title="Case Escalated (SLA Overdue)",
                message=f"Case #{g.reference_number} has been automatically escalated to senior management due to SLA timeline expiry.",
                link=f"/grievances/{g.id}",
                notification_type="WARNING"
            )

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit batch overdue escalations: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process overdue escalations.")

        return escalated_refs

    @staticmethod
    def process_sla_warnings(db: Session) -> List[str]:
        """
        Scan active grievances whose SLA deadline is approaching within the configured warning window.
        Dispatches advisory warnings to the assigned officer and student before escalation.
        """
        now = datetime.now(timezone.utc)
        warning_window = now + timedelta(hours=settings.SLA_WARNING_HOURS)
        active_statuses = [
            GrievanceStatusEnum.SUBMITTED,
            GrievanceStatusEnum.UNDER_REVIEW,
            GrievanceStatusEnum.ASSIGNED,
            GrievanceStatusEnum.INVESTIGATION_IN_PROGRESS,
            GrievanceStatusEnum.NEEDS_INFORMATION
        ]

        approaching_grievances = db.query(Grievance).filter(
            Grievance.due_date > now,
            Grievance.due_date <= warning_window,
            Grievance.sla_warning_sent == False,
            Grievance.status.in_(active_statuses)
        ).all()

        warned_refs = []
        for g in approaching_grievances:
            g.sla_warning_sent = True
            warned_refs.append(g.reference_number)

            # Calculate remaining hours
            hours_left = max(1, int((g.due_date.replace(tzinfo=timezone.utc) - now).total_seconds() // 3600))

            # Notify assigned officer if present
            if g.assigned_officer_id:
                create_notification(
                    db=db,
                    user_id=g.assigned_officer_id,
                    title="SLA Deadline Warning",
                    message=f"Case #{g.reference_number} is approaching statutory deadline in ~{hours_left} hours.",
                    link=f"/grievances/{g.id}",
                    notification_type="WARNING"
                )

            # Notify student
            create_notification(
                db=db,
                user_id=g.student_id,
                title="SLA Progress Notice",
                message=f"Case #{g.reference_number} is actively monitored. SLA target expires in ~{hours_left} hours.",
                link=f"/grievances/{g.id}",
                notification_type="INFO"
            )

        if warned_refs:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to commit SLA warning flags: {e}", exc_info=True)

        return warned_refs

escalation_service = EscalationService()
