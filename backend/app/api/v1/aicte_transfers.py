from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.permissions import get_current_active_user
from app.models.user import User
from app.models.enums import AICTETransferStatusEnum
from app.schemas.aicte_transfer import (
    TransferInitiateRequest,
    TransferAcceptRequest,
    TransferRejectRequest,
    TransferCancelRequest,
    AICTECaseTransferResponse,
    AICTECaseTransferListResponse,
)
from app.services.aicte_transfer_service import AICTETransferService

router = APIRouter(prefix="/aicte", tags=["AICTE Case Transfers"])

@router.post("/cases/{case_id}/transfers", response_model=AICTECaseTransferResponse, status_code=status.HTTP_201_CREATED)
def initiate_case_transfer(
    case_id: int,
    payload: TransferInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiate a formal inter-Bureau case transfer proposal:
    - Originating unit members or Super Admin only.
    - Destination unit must be active and distinct.
    - Moves case to TRANSFER_PENDING without changing handling unit.
    """
    return AICTETransferService.initiate_transfer(
        db=db,
        case_id=case_id,
        payload=payload,
        current_user=current_user
    )

@router.get("/cases/{case_id}/transfers", response_model=List[AICTECaseTransferResponse])
def get_case_transfers(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve full chronological transfer history for an AICTE case."""
    return AICTETransferService.get_case_transfers(
        db=db,
        case_id=case_id,
        current_user=current_user
    )

@router.get("/transfers/incoming", response_model=AICTECaseTransferListResponse)
def list_incoming_transfers(
    status_filter: Optional[AICTETransferStatusEnum] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List incoming transfer proposals targeted at the user's authorized Bureau units."""
    return AICTETransferService.get_incoming_transfers(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter
    )

@router.get("/transfers/outgoing", response_model=AICTECaseTransferListResponse)
def list_outgoing_transfers(
    status_filter: Optional[AICTETransferStatusEnum] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List outgoing transfer proposals originating from the user's authorized Bureau units."""
    return AICTETransferService.get_outgoing_transfers(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter
    )

@router.get("/transfers/{transfer_id}", response_model=AICTECaseTransferResponse)
def get_transfer_detail(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve authorized details of an individual transfer record."""
    return AICTETransferService.get_transfer_detail(
        db=db,
        transfer_id=transfer_id,
        current_user=current_user
    )

@router.post("/transfers/{transfer_id}/accept", response_model=AICTECaseTransferResponse)
def accept_transfer(
    transfer_id: int,
    payload: TransferAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Accept an incoming case transfer:
    - Receiving Bureau officials or Super Admin only.
    - Atomically updates case handling unit and marks transfer ACCEPTED.
    """
    return AICTETransferService.accept_transfer(
        db=db,
        transfer_id=transfer_id,
        payload=payload,
        current_user=current_user
    )

@router.post("/transfers/{transfer_id}/reject", response_model=AICTECaseTransferResponse)
def reject_transfer(
    transfer_id: int,
    payload: TransferRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Decline an incoming case transfer:
    - Receiving Bureau officials or Super Admin only.
    - Rejection reason is mandatory.
    - Preserves originating handling unit and restores prior case status.
    """
    return AICTETransferService.reject_transfer(
        db=db,
        transfer_id=transfer_id,
        payload=payload,
        current_user=current_user
    )

@router.post("/transfers/{transfer_id}/cancel", response_model=AICTECaseTransferResponse)
def cancel_transfer(
    transfer_id: int,
    payload: TransferCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Withdraw a pending transfer proposal:
    - Initiator, originating Bureau officials, or Super Admin only.
    - Can only be cancelled while still in PENDING_ACCEPTANCE state.
    """
    return AICTETransferService.cancel_transfer(
        db=db,
        transfer_id=transfer_id,
        payload=payload,
        current_user=current_user
    )
