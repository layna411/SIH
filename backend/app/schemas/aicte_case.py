from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import (
    AICTECaseStatusEnum,
    AICTECaseSourceTypeEnum,
    AICTEComplainantTypeEnum,
    AICTECaseActionTypeEnum,
    GrievancePriorityEnum,
)

class CaseActionCreate(BaseModel):
    action_type: AICTECaseActionTypeEnum
    action_title: str = Field(..., max_length=255)
    action_description: Optional[str] = None
    new_status: Optional[AICTECaseStatusEnum] = None
    remarks: Optional[str] = None
    supporting_document_ref: Optional[str] = None
    next_action_required: Optional[str] = None
    next_action_due_at: Optional[datetime] = None

class CaseActionResponse(BaseModel):
    id: int
    case_id: int
    action_type: AICTECaseActionTypeEnum
    action_title: str
    action_description: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    unit_id: int
    unit_code: Optional[str] = None
    unit_name: Optional[str] = None
    performed_by_user_id: int
    performed_by_name: Optional[str] = None
    performed_by_email: Optional[str] = None
    action_at: datetime
    remarks: Optional[str] = None
    supporting_document_ref: Optional[str] = None
    next_action_required: Optional[str] = None
    next_action_due_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AICTECaseCreate(BaseModel):
    institution_id: int
    current_unit_id: int
    category: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=255)
    description: str
    complainant_type: AICTEComplainantTypeEnum = AICTEComplainantTypeEnum.STAKEHOLDER
    complainant_name: Optional[str] = None
    complainant_email: Optional[str] = None
    complainant_phone: Optional[str] = None
    official_reference_number: Optional[str] = None
    priority: GrievancePriorityEnum = GrievancePriorityEnum.NORMAL
    region: Optional[str] = None
    assigned_officer_id: Optional[int] = None
    expected_disposal_at: Optional[datetime] = None
    next_action_required: Optional[str] = None
    next_action_due_at: Optional[datetime] = None

class AICTECaseUpdate(BaseModel):
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[GrievancePriorityEnum] = None
    official_reference_number: Optional[str] = None
    region: Optional[str] = None
    expected_disposal_at: Optional[datetime] = None
    next_action_required: Optional[str] = None
    next_action_due_at: Optional[datetime] = None

class AICTECaseAssign(BaseModel):
    current_unit_id: Optional[int] = None
    assigned_officer_id: Optional[int] = None
    reason: Optional[str] = None

class AICTECaseReferGrievance(BaseModel):
    source_grievance_id: int
    destination_unit_id: int
    referral_reason: str = Field(..., min_length=5)
    complainant_type: AICTEComplainantTypeEnum = AICTEComplainantTypeEnum.STUDENT
    priority: Optional[GrievancePriorityEnum] = None
    official_reference_number: Optional[str] = None

class AICTECaseResponse(BaseModel):
    id: int
    case_reference: str
    institution_id: int
    institution_name: Optional[str] = None
    institution_code: Optional[str] = None
    aicte_permanent_id: Optional[str] = None
    source_grievance_id: Optional[int] = None
    source_grievance_reference: Optional[str] = None
    source_type: AICTECaseSourceTypeEnum
    official_reference_number: Optional[str] = None
    received_at: datetime
    complainant_type: AICTEComplainantTypeEnum
    complainant_name: Optional[str] = None
    complainant_email: Optional[str] = None
    complainant_phone: Optional[str] = None
    category: str
    subject: str
    description: str
    status: AICTECaseStatusEnum
    current_unit_id: int
    current_unit_code: Optional[str] = None
    current_unit_name: Optional[str] = None
    assigned_officer_id: Optional[int] = None
    assigned_officer_name: Optional[str] = None
    region: Optional[str] = None
    priority: GrievancePriorityEnum
    last_action_at: datetime
    next_action_required: Optional[str] = None
    next_action_due_at: Optional[datetime] = None
    expected_disposal_at: Optional[datetime] = None
    disposed_at: Optional[datetime] = None
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AICTECaseDetailResponse(AICTECaseResponse):
    actions: List[CaseActionResponse] = []

class AICTECaseListResponse(BaseModel):
    cases: List[AICTECaseResponse]
    total: int
    page: int
    page_size: int

class InstitutionConsolidatedHistoryResponse(BaseModel):
    institution_id: int
    name: str
    code: str
    aicte_permanent_id: Optional[str] = None
    is_aicte_verified: bool = False
    region: Optional[str] = None
    aliases: List[str] = []
    total_cases: int = 0
    active_cases: int = 0
    disposed_cases: int = 0
    status_counts: Dict[str, int] = {}
    unit_counts: Dict[str, int] = {}
    recent_cases: List[AICTECaseResponse] = []
