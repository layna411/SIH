from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AICTETransferStatusEnum

class TransferInitiateRequest(BaseModel):
    to_unit_id: int = Field(..., description="Target organizational unit ID for the transfer.")
    proposed_assignee_id: Optional[int] = Field(None, description="Optional officer in receiving unit to recommend for assignment.")
    transfer_reason: str = Field(..., min_length=10, max_length=2000, description="Mandatory formal transfer rationale.")
    handover_summary: Optional[str] = Field(None, max_length=2000, description="Executive summary of procedural history and next steps.")

class TransferAcceptRequest(BaseModel):
    response_notes: Optional[str] = Field(None, max_length=1000, description="Administrative acceptance remarks.")
    accepted_assignee_id: Optional[int] = Field(None, description="Optional officer in receiving unit assigned upon acceptance.")

class TransferRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5, max_length=1000, description="Mandatory substantive reason for rejecting case handover.")

class TransferCancelRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=5, max_length=1000, description="Mandatory reason for withdrawing the transfer proposal.")

class AICTECaseTransferResponse(BaseModel):
    id: int
    case_id: int
    case_reference: str
    case_subject: str
    institution_id: int
    institution_name: str
    institution_aicte_pid: Optional[str] = None
    from_unit_id: int
    from_unit_code: str
    from_unit_name: str
    to_unit_id: int
    to_unit_code: str
    to_unit_name: str
    initiated_by_user_id: int
    initiated_by_name: str
    proposed_assignee_id: Optional[int] = None
    proposed_assignee_name: Optional[str] = None
    transfer_reason: str
    handover_summary: Optional[str] = None
    prior_case_status: str
    transfer_status: AICTETransferStatusEnum
    initiated_at: datetime
    responded_at: Optional[datetime] = None
    responded_by_user_id: Optional[int] = None
    responded_by_name: Optional[str] = None
    response_notes: Optional[str] = None
    accepted_assignee_id: Optional[int] = None
    accepted_assignee_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AICTECaseTransferListResponse(BaseModel):
    items: List[AICTECaseTransferResponse]
    total: int
    page: int
    page_size: int
