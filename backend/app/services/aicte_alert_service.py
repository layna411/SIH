import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.core.config import settings
from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTETransferStatusEnum,
    AICTEOverlapReviewStatusEnum,
)
from app.models.user import User
from app.models.bureau_membership import BureauMembership
from app.models.organizational_unit import OrganizationalUnit
from app.models.aicte_case import AICTECase
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.aicte_overlap import AICTECaseOverlap
from app.models.notification import Notification, NotificationOutbox
from app.models.audit import AuditLog
from app.services.notification_service import create_notification
from app.core.permissions import get_user_bureau_unit_ids, check_bureau_access
from app.schemas.aicte_alert import (
    AICTENotificationResponse,
    AICTENotificationListResponse,
    AICTEAlertSummaryResponse,
    AICTEOverdueAlertItem,
    AICTEOverdueAlertListResponse,
    AICTEAlertConfigurationResponse,
    AICTEAlertConfigurationUpdateRequest,
)

logger = logging.getLogger("eduresolve.aicte_alerts")

# In-memory operational overrides for alert thresholds
_ALERT_CONFIG: Dict[str, Any] = {
    "warning_window_hours": settings.AICTE_ALERT_WARNING_HOURS,
    "dedup_window_hours": settings.AICTE_ALERT_DEDUP_HOURS,
    "transfer_pending_hours": settings.AICTE_TRANSFER_PENDING_WARNING_HOURS,
}

class AICTEAlertService:
    @classmethod
    def get_warning_window_hours(cls) -> int:
        return _ALERT_CONFIG.get("warning_window_hours", 48)

    @classmethod
    def get_dedup_window_hours(cls) -> int:
        return _ALERT_CONFIG.get("dedup_window_hours", 24)

    @classmethod
    def get_transfer_pending_hours(cls) -> int:
        return _ALERT_CONFIG.get("transfer_pending_hours", 72)

    @classmethod
    def get_configuration(cls) -> AICTEAlertConfigurationResponse:
        return AICTEAlertConfigurationResponse(
            warning_window_hours=cls.get_warning_window_hours(),
            dedup_window_hours=cls.get_dedup_window_hours(),
            transfer_pending_hours=cls.get_transfer_pending_hours(),
            poll_interval_seconds=settings.SLA_POLL_INTERVAL_SECONDS,
            scheduler_enabled=settings.SLA_SCHEDULER_ENABLED,
        )

    @classmethod
    def update_configuration(
        cls,
        db: Session,
        payload: AICTEAlertConfigurationUpdateRequest,
        current_user: User
    ) -> AICTEAlertConfigurationResponse:
        """Update operational alert thresholds. Restricted to SuperAdmin and RegulatoryAdmin."""
        if current_user.default_role not in (UserRoleEnum.SUPER_ADMIN, UserRoleEnum.REGULATORY_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only AICTE Regulatory Administrators can update alert configuration."
            )

        changes = {}
        if payload.warning_window_hours is not None:
            changes["warning_window_hours"] = {
                "old": _ALERT_CONFIG["warning_window_hours"],
                "new": payload.warning_window_hours
            }
            _ALERT_CONFIG["warning_window_hours"] = payload.warning_window_hours

        if payload.dedup_window_hours is not None:
            changes["dedup_window_hours"] = {
                "old": _ALERT_CONFIG["dedup_window_hours"],
                "new": payload.dedup_window_hours
            }
            _ALERT_CONFIG["dedup_window_hours"] = payload.dedup_window_hours

        if payload.transfer_pending_hours is not None:
            changes["transfer_pending_hours"] = {
                "old": _ALERT_CONFIG["transfer_pending_hours"],
                "new": payload.transfer_pending_hours
            }
            _ALERT_CONFIG["transfer_pending_hours"] = payload.transfer_pending_hours

        # Log audit entry
        db.add(AuditLog(
            user_id=current_user.id,
            action="AICTE_ALERT_CONFIG_UPDATED",
            entity_type="SYSTEM_SETTING",
            entity_id="AICTE_ALERT_CONFIG",
            details=json.dumps(changes)
        ))
        db.commit()

        return cls.get_configuration()

    @classmethod
    def is_duplicate_alert(
        cls,
        db: Session,
        user_id: int,
        category: str,
        reference_id: Optional[str],
        window_hours: Optional[int] = None
    ) -> bool:
        """
        Check if an active notification of the same category and reference_id
        has already been generated for this recipient within the deduplication window.
        """
        if not reference_id:
            return False

        hours = window_hours if window_hours is not None else cls.get_dedup_window_hours()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        existing = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.category == category,
            Notification.reference_id == reference_id,
            Notification.created_at >= cutoff
        ).first()

        return existing is not None

    @classmethod
    def send_alert(
        cls,
        db: Session,
        recipient_id: int,
        category: str,
        severity: str,
        title: str,
        message: str,
        link: Optional[str] = None,
        reference_id: Optional[str] = None,
        requires_acknowledgement: bool = False,
        email_notify: bool = True,
        dedup_window_hours: Optional[int] = None
    ) -> Optional[Notification]:
        """
        Dispatch a single alert notification with deduplication, severity, and outbox integration.
        Returns the created notification or None if deduplicated.
        """
        if cls.is_duplicate_alert(db, recipient_id, category, reference_id, dedup_window_hours):
            return None

        # Verify recipient is active
        recipient = db.query(User).filter(User.id == recipient_id, User.is_active == True).first()
        if not recipient:
            return None

        notif = create_notification(
            db=db,
            user_id=recipient_id,
            title=title,
            message=message,
            link=link,
            notification_type=category,
            email_notify=email_notify,
            severity=severity,
            category=category,
            reference_id=reference_id,
            requires_acknowledgement=requires_acknowledgement
        )
        return notif

    @classmethod
    def get_unit_member_ids(cls, db: Session, unit_id: int) -> List[int]:
        """Return user IDs of all active members of an organizational unit."""
        memberships = db.query(BureauMembership).filter(
            BureauMembership.organizational_unit_id == unit_id,
            BureauMembership.is_active == True
        ).all()
        user_ids = []
        for m in memberships:
            if m.user and m.user.is_active:
                user_ids.append(m.user_id)
        return list(set(user_ids))

    @classmethod
    def get_regulatory_admin_ids(cls, db: Session) -> List[int]:
        """Return user IDs of active SuperAdmins and RegulatoryAdmins."""
        users = db.query(User).filter(
            User.default_role.in_([UserRoleEnum.SUPER_ADMIN, UserRoleEnum.REGULATORY_ADMIN]),
            User.is_active == True
        ).all()
        return [u.id for u in users]

    # -------------------------------------------------------------------------
    # Event-Driven Alert Generators
    # -------------------------------------------------------------------------

    @classmethod
    def notify_case_assignment(
        cls,
        db: Session,
        case: AICTECase,
        assigned_officer_id: int,
        actor: Optional[User] = None
    ) -> Optional[Notification]:
        """Notify an officer when assigned to an AICTE case. Narrative shielded."""
        title = f"Case Assigned: {case.case_reference}"
        message = (
            f"You have been assigned as the handling officer for AICTE Case {case.case_reference} "
            f"concerning {case.institution.name if case.institution else 'Institution'}. "
            f"Category: {case.category}."
        )
        return cls.send_alert(
            db=db,
            recipient_id=assigned_officer_id,
            category="CASE_ASSIGNMENT",
            severity="INFO",
            title=title,
            message=message,
            link=f"/aicte/cases/{case.id}",
            reference_id=f"ASSIGN_{case.id}_{assigned_officer_id}",
            requires_acknowledgement=False
        )

    @classmethod
    def notify_transfer_proposal(
        cls,
        db: Session,
        transfer: AICTECaseTransfer
    ) -> int:
        """Notify authorized receiving Bureau members of an incoming transfer proposal."""
        case = transfer.case
        case_ref = case.case_reference if case else f"#{transfer.case_id}"
        to_unit_code = transfer.to_unit.code if transfer.to_unit else "Unit"
        from_unit_code = transfer.from_unit.code if transfer.from_unit else "Unit"

        title = f"Incoming Transfer: {case_ref}"
        message = (
            f"AICTE Case {case_ref} has been proposed for transfer from {from_unit_code} to {to_unit_code}. "
            f"Review and formal acceptance is required."
        )
        link = f"/aicte/transfers/{transfer.id}"
        ref_id = f"TRANSFER_PROP_{transfer.id}"

        recipients = cls.get_unit_member_ids(db, transfer.to_unit_id)
        if transfer.proposed_assignee_id and transfer.proposed_assignee_id not in recipients:
            recipients.append(transfer.proposed_assignee_id)

        sent_count = 0
        for uid in recipients:
            res = cls.send_alert(
                db=db,
                recipient_id=uid,
                category="TRANSFER_PENDING",
                severity="WARNING",
                title=title,
                message=message,
                link=link,
                reference_id=ref_id,
                requires_acknowledgement=True
            )
            if res:
                sent_count += 1
        return sent_count

    @classmethod
    def notify_transfer_decision(
        cls,
        db: Session,
        transfer: AICTECaseTransfer,
        decision: str,  # "ACCEPTED", "REJECTED", "CANCELLED"
        actor: Optional[User] = None
    ) -> int:
        """Notify originating Bureau members when a transfer is accepted, rejected, or cancelled."""
        case = transfer.case
        case_ref = case.case_reference if case else f"#{transfer.case_id}"
        to_unit_code = transfer.to_unit.code if transfer.to_unit else "Unit"
        from_unit_code = transfer.from_unit.code if transfer.from_unit else "Unit"

        severity = "WARNING" if decision == "REJECTED" else "INFO"
        title = f"Transfer {decision.capitalize()}: {case_ref}"
        if decision == "ACCEPTED":
            message = f"Case {case_ref} transfer to {to_unit_code} was formally accepted."
        elif decision == "REJECTED":
            reason = f" Reason: {transfer.response_notes}" if transfer.response_notes else ""
            message = f"Case {case_ref} transfer to {to_unit_code} was declined.{reason}"
        else:
            message = f"Case {case_ref} transfer proposal to {to_unit_code} was cancelled."

        link = f"/aicte/cases/{case.id}" if case else "/aicte/transfers"
        ref_id = f"TRANSFER_{decision}_{transfer.id}"

        recipients = cls.get_unit_member_ids(db, transfer.from_unit_id)
        if transfer.initiated_by_user_id not in recipients:
            recipients.append(transfer.initiated_by_user_id)

        sent_count = 0
        for uid in recipients:
            res = cls.send_alert(
                db=db,
                recipient_id=uid,
                category="TRANSFER_DECISION",
                severity=severity,
                title=title,
                message=message,
                link=link,
                reference_id=ref_id,
                requires_acknowledgement=False
            )
            if res:
                sent_count += 1
        return sent_count

    @classmethod
    def notify_overlap_detected(
        cls,
        db: Session,
        overlap: AICTECaseOverlap
    ) -> int:
        """Notify members of both involved Bureaus when an overlap candidate is flagged. Narrative shielded."""
        case_low = db.query(AICTECase).filter(AICTECase.id == overlap.case_id_low).first()
        case_high = db.query(AICTECase).filter(AICTECase.id == overlap.case_id_high).first()
        if not case_low or not case_high:
            return 0

        title = f"Potential Case Overlap: {case_low.case_reference} & {case_high.case_reference}"
        message = (
            f"Multi-signal overlap candidate ({overlap.overlap_type.value}) detected between "
            f"Case {case_low.case_reference} and Case {case_high.case_reference}. "
            f"Supervisory review required."
        )
        link = f"/aicte/overlaps/{overlap.id}"
        ref_id = f"OVERLAP_DETECT_{overlap.id}"

        recipients = set(cls.get_unit_member_ids(db, case_low.current_unit_id))
        recipients.update(cls.get_unit_member_ids(db, case_high.current_unit_id))

        sent_count = 0
        for uid in recipients:
            res = cls.send_alert(
                db=db,
                recipient_id=uid,
                category="OVERLAP_PENDING",
                severity="WARNING",
                title=title,
                message=message,
                link=link,
                reference_id=ref_id,
                requires_acknowledgement=False
            )
            if res:
                sent_count += 1
        return sent_count

    # -------------------------------------------------------------------------
    # Scheduled SLA and Deadline Alert Evaluation
    # -------------------------------------------------------------------------

    @classmethod
    def scan_and_generate_sla_alerts(cls, db: Session) -> Dict[str, Any]:
        """
        Periodically evaluate active AICTE cases for deadline breaches and warnings.
        Runs safely within the existing SLA scheduler cycle.
        Guarantees:
        - Bounded query, deduplication prevents alert floods.
        - Does NOT mutate any case status or legal disposition.
        """
        now = datetime.now(timezone.utc)
        warning_window_hours = cls.get_warning_window_hours()
        transfer_pending_hours = cls.get_transfer_pending_hours()
        warning_threshold = now + timedelta(hours=warning_window_hours)

        terminal_statuses = [
            AICTECaseStatusEnum.DISPOSED,
            AICTECaseStatusEnum.CLOSED,
            AICTECaseStatusEnum.TRANSFERRED,
        ]

        # Fetch active cases (bounded to 250 per run to prevent runaway scans)
        active_cases = db.query(AICTECase).filter(
            ~AICTECase.status.in_(terminal_statuses)
        ).limit(250).all()

        results = {
            "overdue_next_actions": 0,
            "approaching_next_actions": 0,
            "overdue_expected_disposals": 0,
            "approaching_expected_disposals": 0,
            "missing_deadlines": 0,
            "pending_transfers_flagged": 0,
            "failed_outbox_flagged": 0,
        }

        for case in active_cases:
            assigned_officer_id = case.assigned_officer_id
            unit_member_ids = cls.get_unit_member_ids(db, case.current_unit_id)
            recipients = set(unit_member_ids)
            if assigned_officer_id:
                recipients.add(assigned_officer_id)

            # 1. Overdue Next Action
            if case.next_action_due_at and case.next_action_due_at.replace(tzinfo=timezone.utc if case.next_action_due_at.tzinfo is None else case.next_action_due_at.tzinfo) < now:
                date_key = case.next_action_due_at.strftime('%Y%m%d')
                ref_id = f"SLA_NEXT_OVERDUE_{case.id}_{date_key}"
                title = f"OVERDUE Next Action: {case.case_reference}"
                msg = (
                    f"AICTE Case {case.case_reference} has an overdue next action deadline "
                    f"({case.next_action_due_at.strftime('%Y-%m-%d')}). Immediate operational review required."
                )
                for uid in recipients:
                    if cls.send_alert(
                        db=db,
                        recipient_id=uid,
                        category="SLA_OVERDUE",
                        severity="CRITICAL",
                        title=title,
                        message=msg,
                        link=f"/aicte/cases/{case.id}",
                        reference_id=ref_id,
                        requires_acknowledgement=True
                    ):
                        results["overdue_next_actions"] += 1

            # 2. Approaching Next Action Deadline
            elif case.next_action_due_at:
                due_aware = case.next_action_due_at.replace(tzinfo=timezone.utc if case.next_action_due_at.tzinfo is None else case.next_action_due_at.tzinfo)
                if now <= due_aware <= warning_threshold:
                    date_key = case.next_action_due_at.strftime('%Y%m%d')
                    ref_id = f"SLA_NEXT_WARN_{case.id}_{date_key}"
                    hours_left = max(1, int((due_aware - now).total_seconds() // 3600))
                    title = f"Upcoming Deadline: {case.case_reference}"
                    msg = (
                        f"AICTE Case {case.case_reference} next action is due in ~{hours_left} hours "
                        f"({case.next_action_due_at.strftime('%Y-%m-%d')})."
                    )
                    for uid in recipients:
                        if cls.send_alert(
                            db=db,
                            recipient_id=uid,
                            category="SLA_WARNING",
                            severity="WARNING",
                            title=title,
                            message=msg,
                            link=f"/aicte/cases/{case.id}",
                            reference_id=ref_id,
                            requires_acknowledgement=False
                        ):
                            results["approaching_next_actions"] += 1

            # 3. Overdue Expected Disposal Date
            if case.expected_disposal_at and case.expected_disposal_at.replace(tzinfo=timezone.utc if case.expected_disposal_at.tzinfo is None else case.expected_disposal_at.tzinfo) < now:
                date_key = case.expected_disposal_at.strftime('%Y%m%d')
                ref_id = f"SLA_DISPOSAL_OVERDUE_{case.id}_{date_key}"
                title = f"OVERDUE Disposal Date: {case.case_reference}"
                msg = (
                    f"AICTE Case {case.case_reference} has passed its expected disposal target date "
                    f"({case.expected_disposal_at.strftime('%Y-%m-%d')}). Supervisory attention required."
                )
                for uid in recipients:
                    if cls.send_alert(
                        db=db,
                        recipient_id=uid,
                        category="SLA_OVERDUE",
                        severity="CRITICAL",
                        title=title,
                        message=msg,
                        link=f"/aicte/cases/{case.id}",
                        reference_id=ref_id,
                        requires_acknowledgement=True
                    ):
                        results["overdue_expected_disposals"] += 1

            # 4. Approaching Expected Disposal Date
            elif case.expected_disposal_at:
                disp_aware = case.expected_disposal_at.replace(tzinfo=timezone.utc if case.expected_disposal_at.tzinfo is None else case.expected_disposal_at.tzinfo)
                if now <= disp_aware <= warning_threshold:
                    date_key = case.expected_disposal_at.strftime('%Y%m%d')
                    ref_id = f"SLA_DISPOSAL_WARN_{case.id}_{date_key}"
                    hours_left = max(1, int((disp_aware - now).total_seconds() // 3600))
                    title = f"Disposal Target Approaching: {case.case_reference}"
                    msg = (
                        f"AICTE Case {case.case_reference} expected disposal date target in ~{hours_left} hours "
                        f"({case.expected_disposal_at.strftime('%Y-%m-%d')})."
                    )
                    for uid in recipients:
                        if cls.send_alert(
                            db=db,
                            recipient_id=uid,
                            category="SLA_WARNING",
                            severity="WARNING",
                            title=title,
                            message=msg,
                            link=f"/aicte/cases/{case.id}",
                            reference_id=ref_id,
                            requires_acknowledgement=False
                        ):
                            results["approaching_expected_disposals"] += 1

            # 5. Missing Deadline Compliance Alert
            # Active cases in substantive review that lack next action due dates are non-compliant
            if not case.next_action_due_at and case.status in (AICTECaseStatusEnum.UNDER_PROCESS, AICTECaseStatusEnum.PENDING_REVIEW):
                ref_id = f"SLA_MISSING_DEADLINE_{case.id}"
                title = f"Missing Deadline Configuration: {case.case_reference}"
                msg = (
                    f"AICTE Case {case.case_reference} is active under process but lacks a configured "
                    f"next action deadline. Policy requires scheduling next procedural milestones."
                )
                for uid in recipients:
                    if cls.send_alert(
                        db=db,
                        recipient_id=uid,
                        category="SLA_WARNING",
                        severity="WARNING",
                        title=title,
                        message=msg,
                        link=f"/aicte/cases/{case.id}",
                        reference_id=ref_id,
                        requires_acknowledgement=False
                    ):
                        results["missing_deadlines"] += 1

        # 6. Flag Transfers Pending Beyond Operational Threshold
        delayed_transfer_cutoff = now - timedelta(hours=transfer_pending_hours)
        delayed_transfers = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.transfer_status == AICTETransferStatusEnum.PENDING_ACCEPTANCE,
            AICTECaseTransfer.initiated_at <= delayed_transfer_cutoff
        ).limit(50).all()

        for transfer in delayed_transfers:
            case_ref = transfer.case.case_reference if transfer.case else f"#{transfer.case_id}"
            to_code = transfer.to_unit.code if transfer.to_unit else "Unit"
            ref_id = f"TRANSFER_DELAY_{transfer.id}"
            title = f"URGENT: Delayed Transfer Awaiting Acceptance: {case_ref}"
            msg = (
                f"Transfer proposal for Case {case_ref} to {to_code} has been pending acceptance "
                f"for over {transfer_pending_hours} hours. Immediate Bureau decision required."
            )
            to_members = cls.get_unit_member_ids(db, transfer.to_unit_id)
            for uid in to_members:
                if cls.send_alert(
                    db=db,
                    recipient_id=uid,
                    category="TRANSFER_PENDING",
                    severity="CRITICAL",
                    title=title,
                    message=msg,
                    link=f"/aicte/transfers/{transfer.id}",
                    reference_id=ref_id,
                    requires_acknowledgement=True
                ):
                    results["pending_transfers_flagged"] += 1

        # 7. Failed Outbox Deliveries Needing Admin Attention
        failed_outbox_entries = db.query(NotificationOutbox).filter(
            NotificationOutbox.status == "FAILED"
        ).order_by(desc(NotificationOutbox.created_at)).limit(20).all()

        admin_ids = cls.get_regulatory_admin_ids(db)
        for outbox_entry in failed_outbox_entries:
            ref_id = f"FAILED_OUTBOX_{outbox_entry.id}"
            title = f"Operational Alert: Failed Notification Delivery #{outbox_entry.id}"
            msg = (
                f"Outbox email delivery to {outbox_entry.recipient_email} failed after "
                f"{outbox_entry.attempts} attempts. Error: {str(outbox_entry.error_message)[:120]}."
            )
            for admin_id in admin_ids:
                if cls.send_alert(
                    db=db,
                    recipient_id=admin_id,
                    category="FAILED_DELIVERY",
                    severity="CRITICAL",
                    title=title,
                    message=msg,
                    link="/aicte/notifications",
                    reference_id=ref_id,
                    requires_acknowledgement=True
                ):
                    results["failed_outbox_flagged"] += 1

        return results

    # -------------------------------------------------------------------------
    # Notification & Alert Center APIs
    # -------------------------------------------------------------------------

    @classmethod
    def get_user_notifications(
        cls,
        db: Session,
        current_user: User,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        is_read: Optional[bool] = None,
        is_acknowledged: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> AICTENotificationListResponse:
        """Retrieve paginated notifications strictly scoped to current_user."""
        query = db.query(Notification).filter(Notification.user_id == current_user.id)

        if category:
            query = query.filter(Notification.category == category)
        if severity:
            query = query.filter(Notification.severity == severity)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        if is_acknowledged is not None:
            query = query.filter(Notification.is_acknowledged == is_acknowledged)

        total = query.count()
        unread_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        unacknowledged_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.requires_acknowledgement == True,
            Notification.is_acknowledged == False
        ).count()

        items = query.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return AICTENotificationListResponse(
            items=[AICTENotificationResponse.model_validate(n) for n in items],
            total=total,
            unread_count=unread_count,
            unacknowledged_count=unacknowledged_count,
            page=page,
            page_size=page_size
        )

    @classmethod
    def get_notification_detail(
        cls,
        db: Session,
        notification_id: int,
        current_user: User
    ) -> AICTENotificationResponse:
        """Retrieve a single notification ensuring recipient ownership."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification #{notification_id} not found."
            )
        return AICTENotificationResponse.model_validate(notif)

    @classmethod
    def mark_read(
        cls,
        db: Session,
        notification_id: int,
        current_user: User
    ) -> AICTENotificationResponse:
        """Mark notification as read. Preserves case status intact."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification #{notification_id} not found."
            )
        notif.is_read = True
        db.commit()
        db.refresh(notif)
        return AICTENotificationResponse.model_validate(notif)

    @classmethod
    def acknowledge_notification(
        cls,
        db: Session,
        notification_id: int,
        current_user: User
    ) -> AICTENotificationResponse:
        """
        Formally acknowledge an alert notification.
        Distinct from reading: records timestamp of acknowledgement.
        Invariant: Never modifies or resolves the underlying case condition.
        """
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification #{notification_id} not found."
            )
        now = datetime.now(timezone.utc)
        notif.is_acknowledged = True
        notif.acknowledged_at = now
        notif.is_read = True
        db.commit()
        db.refresh(notif)
        return AICTENotificationResponse.model_validate(notif)

    @classmethod
    def mark_all_read(
        cls,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """Mark all unread notifications for current user as read."""
        updated = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()
        return {"message": "All notifications marked as read.", "updated_count": updated}

    @classmethod
    def get_alerts_summary(
        cls,
        db: Session,
        current_user: User
    ) -> AICTEAlertSummaryResponse:
        """
        Compute live summary of alerts for the user:
        - Unread & unacknowledged notification counts
        - Severity breakdown
        - Counts by category
        - Actionable operational queue counts based on user's authorized jurisdiction
        """
        user_units = get_user_bureau_unit_ids(current_user, db)
        is_admin = current_user.default_role in (UserRoleEnum.SUPER_ADMIN, UserRoleEnum.REGULATORY_ADMIN)

        # 1. User Notifications aggregation
        user_notifs = db.query(Notification).filter(Notification.user_id == current_user.id).all()
        total_unread = sum(1 for n in user_notifs if not n.is_read)
        total_unacknowledged = sum(1 for n in user_notifs if n.requires_acknowledgement and not n.is_acknowledged)
        critical_count = sum(1 for n in user_notifs if n.severity == "CRITICAL" and not n.is_read)
        warning_count = sum(1 for n in user_notifs if n.severity == "WARNING" and not n.is_read)
        info_count = sum(1 for n in user_notifs if n.severity == "INFO" and not n.is_read)

        by_category: Dict[str, int] = {}
        for n in user_notifs:
            cat = n.category or "OTHER"
            by_category[cat] = by_category.get(cat, 0) + 1

        # 2. Operational Queue Counts (scoped to user's authorized units)
        now = datetime.now(timezone.utc)
        terminal_statuses = [AICTECaseStatusEnum.DISPOSED, AICTECaseStatusEnum.CLOSED]

        case_query = db.query(AICTECase).filter(~AICTECase.status.in_(terminal_statuses))
        if not is_admin and user_units:
            case_query = case_query.filter(AICTECase.current_unit_id.in_(user_units))
        elif not is_admin and not user_units:
            case_query = case_query.filter(AICTECase.id == -1)

        active_overdue_cases_count = case_query.filter(
            or_(
                AICTECase.next_action_due_at < now,
                AICTECase.expected_disposal_at < now
            )
        ).count()

        # Pending Transfers for user's destination units
        transfer_query = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.transfer_status == AICTETransferStatusEnum.PENDING_ACCEPTANCE
        )
        if not is_admin and user_units:
            transfer_query = transfer_query.filter(AICTECaseTransfer.to_unit_id.in_(user_units))
        elif not is_admin and not user_units:
            transfer_query = transfer_query.filter(AICTECaseTransfer.id == -1)
        pending_transfers_count = transfer_query.count()

        # Pending Overlaps involving user's bureaus
        overlap_query = db.query(AICTECaseOverlap).filter(
            AICTECaseOverlap.review_status == AICTEOverlapReviewStatusEnum.PENDING
        )
        if not is_admin and user_units:
            overlap_query = overlap_query.join(
                AICTECase,
                or_(
                    AICTECase.id == AICTECaseOverlap.case_id_low,
                    AICTECase.id == AICTECaseOverlap.case_id_high
                )
            ).filter(AICTECase.current_unit_id.in_(user_units))
        elif not is_admin and not user_units:
            overlap_query = overlap_query.filter(AICTECaseOverlap.id == -1)
        pending_overlaps_count = overlap_query.distinct().count()

        # Failed Deliveries (visible only to admins)
        failed_deliveries_count = 0
        if is_admin:
            failed_deliveries_count = db.query(NotificationOutbox).filter(
                NotificationOutbox.status == "FAILED"
            ).count()

        return AICTEAlertSummaryResponse(
            total_unread=total_unread,
            total_unacknowledged=total_unacknowledged,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            by_category=by_category,
            active_overdue_cases_count=active_overdue_cases_count,
            pending_transfers_count=pending_transfers_count,
            pending_overlaps_count=pending_overlaps_count,
            failed_deliveries_count=failed_deliveries_count
        )

    @classmethod
    def get_overdue_alerts(
        cls,
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20
    ) -> AICTEOverdueAlertListResponse:
        """
        Retrieve live list of active cases with overdue deadlines scoped to caller jurisdiction.
        Distinguishes next action overdue, disposal overdue, both, or missing deadlines.
        """
        user_units = get_user_bureau_unit_ids(current_user, db)
        is_admin = current_user.default_role in (UserRoleEnum.SUPER_ADMIN, UserRoleEnum.REGULATORY_ADMIN)

        now = datetime.now(timezone.utc)
        terminal_statuses = [AICTECaseStatusEnum.DISPOSED, AICTECaseStatusEnum.CLOSED]

        query = db.query(AICTECase).filter(~AICTECase.status.in_(terminal_statuses))
        if not is_admin and user_units:
            query = query.filter(AICTECase.current_unit_id.in_(user_units))
        elif not is_admin and not user_units:
            return AICTEOverdueAlertListResponse(items=[], total=0, page=page, page_size=page_size)

        # Overdue condition: next_action_due_at < now OR expected_disposal_at < now
        query = query.filter(
            or_(
                AICTECase.next_action_due_at < now,
                AICTECase.expected_disposal_at < now
            )
        )

        total = query.count()
        cases = query.order_by(
            AICTECase.next_action_due_at.asc(),
            AICTECase.expected_disposal_at.asc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for c in cases:
            inst = c.institution
            unit = c.current_unit
            officer = c.assigned_officer

            is_next_overdue = c.next_action_due_at and c.next_action_due_at.replace(tzinfo=timezone.utc if c.next_action_due_at.tzinfo is None else c.next_action_due_at.tzinfo) < now
            is_disp_overdue = c.expected_disposal_at and c.expected_disposal_at.replace(tzinfo=timezone.utc if c.expected_disposal_at.tzinfo is None else c.expected_disposal_at.tzinfo) < now

            if is_next_overdue and is_disp_overdue:
                overdue_type = "BOTH"
                oldest_date = min(c.next_action_due_at, c.expected_disposal_at)
            elif is_next_overdue:
                overdue_type = "NEXT_ACTION"
                oldest_date = c.next_action_due_at
            else:
                overdue_type = "EXPECTED_DISPOSAL"
                oldest_date = c.expected_disposal_at

            oldest_aware = oldest_date.replace(tzinfo=timezone.utc if oldest_date.tzinfo is None else oldest_date.tzinfo)
            overdue_days = max(1, int((now - oldest_aware).total_seconds() // 86400))

            items.append(AICTEOverdueAlertItem(
                case_id=c.id,
                case_reference=c.case_reference,
                subject=c.subject,
                institution_id=c.institution_id,
                institution_name=inst.name if inst else "Unknown Institution",
                current_unit_id=c.current_unit_id,
                current_unit_code=unit.code if unit else "N/A",
                current_unit_name=unit.name if unit else "N/A",
                assigned_officer_id=c.assigned_officer_id,
                assigned_officer_name=officer.full_name if officer else None,
                status=c.status.value if hasattr(c.status, 'value') else str(c.status),
                priority=c.priority.value if hasattr(c.priority, 'value') else str(c.priority),
                next_action_required=c.next_action_required,
                next_action_due_at=c.next_action_due_at,
                expected_disposal_at=c.expected_disposal_at,
                overdue_type=overdue_type,
                overdue_days=overdue_days
            ))

        return AICTEOverdueAlertListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
