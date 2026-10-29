import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    AICTECaseActionTypeEnum,
    AICTETransferStatusEnum,
)
from app.models.user import User
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.models.aicte_case import AICTECase, CaseAction
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.audit import AuditLog
from app.models.notification import Notification, NotificationOutbox
from app.core.permissions import check_bureau_access, get_user_bureau_unit_ids
from app.schemas.aicte_transfer import (
    TransferInitiateRequest,
    TransferAcceptRequest,
    TransferRejectRequest,
    TransferCancelRequest,
    AICTECaseTransferResponse,
    AICTECaseTransferListResponse,
)

class AICTETransferService:
    @staticmethod
    def map_transfer_to_response(transfer: AICTECaseTransfer) -> AICTECaseTransferResponse:
        case = transfer.case
        inst = case.institution if case else None
        return AICTECaseTransferResponse(
            id=transfer.id,
            case_id=transfer.case_id,
            case_reference=case.case_reference if case else f"#{transfer.case_id}",
            case_subject=case.subject if case else "N/A",
            institution_id=case.institution_id if case else 0,
            institution_name=inst.name if inst else "Unknown Institution",
            institution_aicte_pid=inst.aicte_permanent_id if inst else None,
            from_unit_id=transfer.from_unit_id,
            from_unit_code=transfer.from_unit.code if transfer.from_unit else "N/A",
            from_unit_name=transfer.from_unit.name if transfer.from_unit else "N/A",
            to_unit_id=transfer.to_unit_id,
            to_unit_code=transfer.to_unit.code if transfer.to_unit else "N/A",
            to_unit_name=transfer.to_unit.name if transfer.to_unit else "N/A",
            initiated_by_user_id=transfer.initiated_by_user_id,
            initiated_by_name=transfer.initiated_by_user.full_name if transfer.initiated_by_user else "Authorized Officer",
            proposed_assignee_id=transfer.proposed_assignee_id,
            proposed_assignee_name=transfer.proposed_assignee.full_name if transfer.proposed_assignee else None,
            transfer_reason=transfer.transfer_reason,
            handover_summary=transfer.handover_summary,
            prior_case_status=transfer.prior_case_status,
            transfer_status=transfer.transfer_status,
            initiated_at=transfer.initiated_at,
            responded_at=transfer.responded_at,
            responded_by_user_id=transfer.responded_by_user_id,
            responded_by_name=transfer.responded_by_user.full_name if transfer.responded_by_user else None,
            response_notes=transfer.response_notes,
            accepted_assignee_id=transfer.accepted_assignee_id,
            accepted_assignee_name=transfer.accepted_assignee.full_name if transfer.accepted_assignee else None,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
        )

    @classmethod
    def initiate_transfer(
        cls,
        db: Session,
        case_id: int,
        payload: TransferInitiateRequest,
        current_user: User
    ) -> AICTECaseTransferResponse:
        """
        Initiate a formal inter-Bureau case transfer proposal:
        - Validates originating unit authorization.
        - Validates destination unit exists, is active, and differs from originating unit.
        - Checks for conflicting active pending transfers.
        - Moves case to TRANSFER_PENDING without modifying current_unit_id or current assignee.
        - Records immutable CaseAction and AuditLog.
        """
        # Lock case row for concurrency safety
        case = db.query(AICTECase).filter(AICTECase.id == case_id).with_for_update().first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AICTE Case #{case_id} not found."
            )

        # 1. Authorization: Originating unit
        if not check_bureau_access(current_user, case.current_unit_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you do not possess authorized membership in the originating Bureau."
            )

        # 2. Case lifecycle check
        if case.status in (AICTECaseStatusEnum.CLOSED, AICTECaseStatusEnum.DISPOSED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transfer a case with status '{case.status.value}'. Reopen the case first."
            )

        # 3. Check for conflicting pending transfer
        existing_pending = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.case_id == case.id,
            AICTECaseTransfer.transfer_status == AICTETransferStatusEnum.PENDING_ACCEPTANCE
        ).first()
        if existing_pending:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Case #{case.case_reference} already has a pending transfer proposal (Transfer #{existing_pending.id})."
            )

        # 4. Destination validation
        if payload.to_unit_id == case.current_unit_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination unit cannot be identical to the current handling unit."
            )

        destination_unit = db.query(OrganizationalUnit).filter(
            OrganizationalUnit.id == payload.to_unit_id,
            OrganizationalUnit.is_active == True
        ).first()
        if not destination_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target organizational unit #{payload.to_unit_id} not found or inactive."
            )

        # 5. Proposed assignee validation (if provided)
        if payload.proposed_assignee_id:
            proposed_user = db.query(User).filter(
                User.id == payload.proposed_assignee_id,
                User.is_active == True
            ).first()
            if not proposed_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Proposed officer #{payload.proposed_assignee_id} not found or inactive."
                )
            has_dest_membership = any(
                bm.organizational_unit_id == payload.to_unit_id and bm.is_active
                for bm in proposed_user.bureau_memberships
            ) or proposed_user.default_role == UserRoleEnum.SUPER_ADMIN
            if not has_dest_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Proposed officer '{proposed_user.full_name}' does not have an active membership in destination unit '{destination_unit.code}'."
                )

        now = datetime.now(timezone.utc)
        prior_status = case.status.value

        # 6. Create transfer record
        transfer = AICTECaseTransfer(
            case_id=case.id,
            from_unit_id=case.current_unit_id,
            to_unit_id=destination_unit.id,
            initiated_by_user_id=current_user.id,
            proposed_assignee_id=payload.proposed_assignee_id,
            transfer_reason=payload.transfer_reason.strip(),
            handover_summary=payload.handover_summary.strip() if payload.handover_summary else None,
            prior_case_status=prior_status,
            transfer_status=AICTETransferStatusEnum.PENDING_ACCEPTANCE,
            initiated_at=now,
        )
        db.add(transfer)
        db.flush()

        # 7. Update Case status to TRANSFER_PENDING (keep current_unit_id and assigned_officer_id intact)
        case.status = AICTECaseStatusEnum.TRANSFER_PENDING
        case.last_action_at = now

        # 8. Record CaseAction
        from_unit = case.current_unit
        action = CaseAction(
            case_id=case.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_INITIATED,
            action_title="Inter-Bureau Transfer Initiated",
            action_description=f"Transfer proposed from {from_unit.code} to {destination_unit.code}. Reason: {payload.transfer_reason[:200]}",
            previous_status=prior_status,
            new_status=AICTECaseStatusEnum.TRANSFER_PENDING.value,
            unit_id=case.current_unit_id,
            performed_by_user_id=current_user.id,
            action_at=now,
            remarks=payload.transfer_reason.strip(),
        )
        db.add(action)

        # 9. Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="AICTE_TRANSFER_INITIATED",
            entity_type="AICTE_CASE_TRANSFER",
            entity_id=str(transfer.id),
            details=json.dumps({
                "case_id": case.id,
                "case_reference": case.case_reference,
                "from_unit_id": case.current_unit_id,
                "to_unit_id": destination_unit.id,
                "transfer_reason": payload.transfer_reason[:200],
            })
        ))

        # 10. Outbox Notification to receiving unit officials
        cls._notify_unit_members(
            db=db,
            unit_id=destination_unit.id,
            title=f"Incoming Case Transfer: {case.case_reference}",
            message=f"An inter-bureau transfer proposal for case {case.case_reference} has been submitted to {destination_unit.code} by {from_unit.code}.",
            link=f"/aicte/transfers/{transfer.id}",
            category="TRANSFER_PENDING",
            severity="WARNING",
            reference_id=f"TRANSFER_PROP_{transfer.id}",
            requires_acknowledgement=True
        )

        db.commit()
        db.refresh(transfer)
        return cls.map_transfer_to_response(transfer)

    @classmethod
    def accept_transfer(
        cls,
        db: Session,
        transfer_id: int,
        payload: TransferAcceptRequest,
        current_user: User
    ) -> AICTECaseTransferResponse:
        """
        Accept an incoming inter-Bureau transfer:
        - Locks transfer and case rows atomically.
        - Validates caller authorization in receiving unit.
        - Handover of current_unit_id to to_unit_id.
        - Reassigns officer if accepted_assignee_id is provided.
        - Updates case status to TRANSFERRED / UNDER_PROCESS.
        """
        transfer = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.id == transfer_id
        ).with_for_update().first()
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transfer #{transfer_id} not found."
            )

        if transfer.transfer_status != AICTETransferStatusEnum.PENDING_ACCEPTANCE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transfer #{transfer_id} cannot be accepted; current state is '{transfer.transfer_status.value}'."
            )

        # Authorization: Must belong to destination unit (or SUPER_ADMIN)
        if not check_bureau_access(current_user, transfer.to_unit_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you do not hold authorized membership in the receiving Bureau."
            )

        case = db.query(AICTECase).filter(AICTECase.id == transfer.case_id).with_for_update().first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case #{transfer.case_id} associated with transfer not found."
            )

        # Validate accepted assignee if given
        accepted_officer_id = payload.accepted_assignee_id or transfer.proposed_assignee_id
        if accepted_officer_id:
            assignee = db.query(User).filter(User.id == accepted_officer_id, User.is_active == True).first()
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee #{accepted_officer_id} not found."
                )
            has_membership = any(
                bm.organizational_unit_id == transfer.to_unit_id and bm.is_active
                for bm in assignee.bureau_memberships
            ) or assignee.default_role == UserRoleEnum.SUPER_ADMIN
            if not has_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Assignee '{assignee.full_name}' is not an active member of receiving unit #{transfer.to_unit_id}."
                )
            case.assigned_officer_id = assignee.id
        else:
            case.assigned_officer_id = None

        now = datetime.now(timezone.utc)
        prev_status = case.status.value

        # Update Transfer Record
        transfer.transfer_status = AICTETransferStatusEnum.ACCEPTED
        transfer.responded_at = now
        transfer.responded_by_user_id = current_user.id
        transfer.response_notes = payload.response_notes.strip() if payload.response_notes else None
        transfer.accepted_assignee_id = case.assigned_officer_id

        # Update Case Responsibility
        case.current_unit_id = transfer.to_unit_id
        case.status = AICTECaseStatusEnum.TRANSFERRED
        case.last_action_at = now

        # Record CaseAction
        action = CaseAction(
            case_id=case.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_ACCEPTED,
            action_title="Inter-Bureau Transfer Formally Accepted",
            action_description=f"Responsibility transferred to {transfer.to_unit.code}. Accepted by {current_user.full_name}.",
            previous_status=prev_status,
            new_status=AICTECaseStatusEnum.TRANSFERRED.value,
            unit_id=transfer.to_unit_id,
            performed_by_user_id=current_user.id,
            action_at=now,
            remarks=payload.response_notes or "Case transfer accepted by receiving Bureau.",
        )
        db.add(action)

        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="AICTE_TRANSFER_ACCEPTED",
            entity_type="AICTE_CASE_TRANSFER",
            entity_id=str(transfer.id),
            details=json.dumps({
                "case_id": case.id,
                "case_reference": case.case_reference,
                "from_unit_id": transfer.from_unit_id,
                "to_unit_id": transfer.to_unit_id,
                "assigned_officer_id": case.assigned_officer_id,
            })
        ))

        # Notify Originating Unit
        cls._notify_unit_members(
            db=db,
            unit_id=transfer.from_unit_id,
            title=f"Transfer Accepted: {case.case_reference}",
            message=f"Case {case.case_reference} transfer to {transfer.to_unit.code} was accepted by {current_user.full_name}.",
            link=f"/aicte/cases/{case.id}",
            category="TRANSFER_DECISION",
            severity="INFO",
            reference_id=f"TRANSFER_ACCEPTED_{transfer.id}",
            requires_acknowledgement=False
        )

        db.commit()
        db.refresh(transfer)
        return cls.map_transfer_to_response(transfer)

    @classmethod
    def reject_transfer(
        cls,
        db: Session,
        transfer_id: int,
        payload: TransferRejectRequest,
        current_user: User
    ) -> AICTECaseTransferResponse:
        """
        Reject an incoming inter-Bureau transfer:
        - Validates caller authorization in receiving unit.
        - Keeps handling unit and assigned officer intact in originating unit.
        - Restores case to its prior_case_status.
        - Records rejection reason and audit history.
        """
        transfer = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.id == transfer_id
        ).with_for_update().first()
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transfer #{transfer_id} not found."
            )

        if transfer.transfer_status != AICTETransferStatusEnum.PENDING_ACCEPTANCE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transfer #{transfer_id} cannot be rejected; current state is '{transfer.transfer_status.value}'."
            )

        # Authorization: Must belong to destination unit (or SUPER_ADMIN)
        if not check_bureau_access(current_user, transfer.to_unit_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you do not hold authorized membership in the receiving Bureau."
            )

        case = db.query(AICTECase).filter(AICTECase.id == transfer.case_id).with_for_update().first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case #{transfer.case_id} associated with transfer not found."
            )

        now = datetime.now(timezone.utc)
        prev_status = case.status.value

        # Update Transfer Record
        transfer.transfer_status = AICTETransferStatusEnum.REJECTED
        transfer.responded_at = now
        transfer.responded_by_user_id = current_user.id
        transfer.response_notes = payload.rejection_reason.strip()

        # Restore Case to prior status, leaving unit and officer untouched
        try:
            restored_status = AICTECaseStatusEnum(transfer.prior_case_status)
        except ValueError:
            restored_status = AICTECaseStatusEnum.UNDER_PROCESS
        case.status = restored_status
        case.last_action_at = now

        # Record CaseAction
        action = CaseAction(
            case_id=case.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_REJECTED,
            action_title="Inter-Bureau Transfer Declined",
            action_description=f"Transfer to {transfer.to_unit.code} was declined by {current_user.full_name}. Reason: {payload.rejection_reason.strip()}",
            previous_status=prev_status,
            new_status=case.status.value,
            unit_id=transfer.from_unit_id,
            performed_by_user_id=current_user.id,
            action_at=now,
            remarks=payload.rejection_reason.strip(),
        )
        db.add(action)

        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="AICTE_TRANSFER_REJECTED",
            entity_type="AICTE_CASE_TRANSFER",
            entity_id=str(transfer.id),
            details=json.dumps({
                "case_id": case.id,
                "case_reference": case.case_reference,
                "from_unit_id": transfer.from_unit_id,
                "to_unit_id": transfer.to_unit_id,
                "rejection_reason": payload.rejection_reason.strip(),
                "restored_status": restored_status.value
            })
        ))

        # Notify Originating Unit
        cls._notify_unit_members(
            db=db,
            unit_id=transfer.from_unit_id,
            title=f"Transfer Declined: {case.case_reference}",
            message=f"Transfer proposal for {case.case_reference} to {transfer.to_unit.code} was declined. Rejection reason: {payload.rejection_reason.strip()}",
            link=f"/aicte/cases/{case.id}",
            category="TRANSFER_DECISION",
            severity="WARNING",
            reference_id=f"TRANSFER_REJECTED_{transfer.id}",
            requires_acknowledgement=False
        )

        db.commit()
        db.refresh(transfer)
        return cls.map_transfer_to_response(transfer)

    @classmethod
    def cancel_transfer(
        cls,
        db: Session,
        transfer_id: int,
        payload: TransferCancelRequest,
        current_user: User
    ) -> AICTECaseTransferResponse:
        """
        Withdraw a pending transfer proposal:
        - Only initiator, originating bureau officer, or SUPER_ADMIN may cancel.
        - Can only be cancelled before acceptance/rejection.
        - Restores case to its prior_case_status.
        """
        transfer = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.id == transfer_id
        ).with_for_update().first()
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transfer #{transfer_id} not found."
            )

        if transfer.transfer_status != AICTETransferStatusEnum.PENDING_ACCEPTANCE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot withdraw transfer #{transfer_id}; current state is '{transfer.transfer_status.value}'."
            )

        # Authorization: Initiator, or member of originating unit, or SUPER_ADMIN
        is_initiator = transfer.initiated_by_user_id == current_user.id
        has_origin_access = check_bureau_access(current_user, transfer.from_unit_id, db)
        if not (is_initiator or has_origin_access or current_user.default_role == UserRoleEnum.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: only the transfer initiator or originating Bureau officials can withdraw this proposal."
            )

        case = db.query(AICTECase).filter(AICTECase.id == transfer.case_id).with_for_update().first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case #{transfer.case_id} associated with transfer not found."
            )

        now = datetime.now(timezone.utc)
        prev_status = case.status.value

        # Update Transfer
        transfer.transfer_status = AICTETransferStatusEnum.CANCELLED
        transfer.responded_at = now
        transfer.responded_by_user_id = current_user.id
        transfer.response_notes = payload.cancellation_reason.strip()

        # Restore Case
        try:
            restored_status = AICTECaseStatusEnum(transfer.prior_case_status)
        except ValueError:
            restored_status = AICTECaseStatusEnum.UNDER_PROCESS
        case.status = restored_status
        case.last_action_at = now

        # Case Action
        action = CaseAction(
            case_id=case.id,
            action_type=AICTECaseActionTypeEnum.TRANSFER_CANCELLED,
            action_title="Inter-Bureau Transfer Withdrawn",
            action_description=f"Transfer proposal to {transfer.to_unit.code} was withdrawn by {current_user.full_name}. Reason: {payload.cancellation_reason.strip()}",
            previous_status=prev_status,
            new_status=case.status.value,
            unit_id=transfer.from_unit_id,
            performed_by_user_id=current_user.id,
            action_at=now,
            remarks=payload.cancellation_reason.strip(),
        )
        db.add(action)

        # Audit Log
        db.add(AuditLog(
            user_id=current_user.id,
            action="AICTE_TRANSFER_CANCELLED",
            entity_type="AICTE_CASE_TRANSFER",
            entity_id=str(transfer.id),
            details=json.dumps({
                "case_id": case.id,
                "case_reference": case.case_reference,
                "cancellation_reason": payload.cancellation_reason.strip(),
                "restored_status": restored_status.value
            })
        ))

        # Notify Receiving Unit of cancellation
        cls._notify_unit_members(
            db=db,
            unit_id=transfer.to_unit_id,
            title=f"Transfer Cancelled: {case.case_reference}",
            message=f"Transfer proposal for case {case.case_reference} to {transfer.to_unit.code} was withdrawn by {current_user.full_name}.",
            link=f"/aicte/cases/{case.id}",
            category="TRANSFER_DECISION",
            severity="INFO",
            reference_id=f"TRANSFER_CANCELLED_{transfer.id}",
            requires_acknowledgement=False
        )

        db.commit()
        db.refresh(transfer)
        return cls.map_transfer_to_response(transfer)

    @classmethod
    def get_case_transfers(
        cls,
        db: Session,
        case_id: int,
        current_user: User
    ) -> List[AICTECaseTransferResponse]:
        """Retrieve authorized transfer history for a case."""
        case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case #{case_id} not found."
            )

        # Verify access: Must have access to case.current_unit_id or SUPER_ADMIN or be party to a transfer
        user_units = get_user_bureau_unit_ids(current_user, db)
        is_admin = current_user.default_role == UserRoleEnum.SUPER_ADMIN
        if not is_admin and case.current_unit_id not in user_units:
            # Check if user belongs to from_unit or to_unit of any transfer of this case
            involved_units = db.query(AICTECaseTransfer.from_unit_id, AICTECaseTransfer.to_unit_id).filter(
                AICTECaseTransfer.case_id == case.id
            ).all()
            all_involved = set()
            for f_id, t_id in involved_units:
                all_involved.add(f_id)
                all_involved.add(t_id)
            if not any(uid in user_units for uid in all_involved):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden to case transfer records."
                )

        transfers = db.query(AICTECaseTransfer).filter(
            AICTECaseTransfer.case_id == case_id
        ).order_by(desc(AICTECaseTransfer.initiated_at)).all()
        return [cls.map_transfer_to_response(t) for t in transfers]

    @classmethod
    def get_incoming_transfers(
        cls,
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[AICTETransferStatusEnum] = None
    ) -> AICTECaseTransferListResponse:
        """List incoming transfer proposals targeted at the user's authorized organizational units."""
        user_units = get_user_bureau_unit_ids(current_user, db)
        if not user_units and current_user.default_role != UserRoleEnum.SUPER_ADMIN:
            return AICTECaseTransferListResponse(items=[], total=0, page=page, page_size=page_size)

        query = db.query(AICTECaseTransfer)
        if current_user.default_role != UserRoleEnum.SUPER_ADMIN:
            query = query.filter(AICTECaseTransfer.to_unit_id.in_(user_units))

        if status_filter:
            query = query.filter(AICTECaseTransfer.transfer_status == status_filter)

        total = query.count()
        transfers = query.order_by(desc(AICTECaseTransfer.initiated_at)).offset((page - 1) * page_size).limit(page_size).all()
        items = [cls.map_transfer_to_response(t) for t in transfers]
        return AICTECaseTransferListResponse(items=items, total=total, page=page, page_size=page_size)

    @classmethod
    def get_outgoing_transfers(
        cls,
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[AICTETransferStatusEnum] = None
    ) -> AICTECaseTransferListResponse:
        """List outgoing transfer proposals initiated from the user's authorized organizational units."""
        user_units = get_user_bureau_unit_ids(current_user, db)
        if not user_units and current_user.default_role != UserRoleEnum.SUPER_ADMIN:
            return AICTECaseTransferListResponse(items=[], total=0, page=page, page_size=page_size)

        query = db.query(AICTECaseTransfer)
        if current_user.default_role != UserRoleEnum.SUPER_ADMIN:
            query = query.filter(AICTECaseTransfer.from_unit_id.in_(user_units))

        if status_filter:
            query = query.filter(AICTECaseTransfer.transfer_status == status_filter)

        total = query.count()
        transfers = query.order_by(desc(AICTECaseTransfer.initiated_at)).offset((page - 1) * page_size).limit(page_size).all()
        items = [cls.map_transfer_to_response(t) for t in transfers]
        return AICTECaseTransferListResponse(items=items, total=total, page=page, page_size=page_size)

    @classmethod
    def get_transfer_detail(
        cls,
        db: Session,
        transfer_id: int,
        current_user: User
    ) -> AICTECaseTransferResponse:
        """Retrieve authorized detail of an individual transfer record."""
        transfer = db.query(AICTECaseTransfer).filter(AICTECaseTransfer.id == transfer_id).first()
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transfer #{transfer_id} not found."
            )

        user_units = get_user_bureau_unit_ids(current_user, db)
        is_admin = current_user.default_role == UserRoleEnum.SUPER_ADMIN
        has_access = is_admin or (transfer.from_unit_id in user_units) or (transfer.to_unit_id in user_units)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you are not authorized to view this transfer."
            )

        return cls.map_transfer_to_response(transfer)

    @staticmethod
    def _notify_unit_members(
        db: Session,
        unit_id: int,
        title: str,
        message: str,
        link: str,
        category: str = "TRANSFER_PENDING",
        severity: str = "WARNING",
        reference_id: Optional[str] = None,
        requires_acknowledgement: bool = False
    ):
        """Enqueue outbox notifications to all active members of an organizational unit using AICTEAlertService."""
        from app.services.aicte_alert_service import AICTEAlertService
        memberships = db.query(BureauMembership).filter(
            BureauMembership.organizational_unit_id == unit_id,
            BureauMembership.is_active == True
        ).all()
        for m in memberships:
            if m.user and m.user.is_active:
                AICTEAlertService.send_alert(
                    db=db,
                    recipient_id=m.user_id,
                    category=category,
                    severity=severity,
                    title=title,
                    message=message,
                    link=link,
                    reference_id=reference_id,
                    requires_acknowledgement=requires_acknowledgement,
                    email_notify=True
                )
