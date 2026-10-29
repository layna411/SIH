from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import GrievanceStatusEnum, GrievancePriorityEnum, EscalationLevelEnum

class GrievanceCreate(BaseModel):
    institution_id: int
    category_id: int
    subcategory: Optional[str] = None
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=20)
    priority: Optional[GrievancePriorityEnum] = GrievancePriorityEnum.NORMAL
    is_confidential: bool = False
    preferred_contact: str = "portal"

class GrievanceStatusUpdate(BaseModel):
    to_status: GrievanceStatusEnum
    reason: str = Field(..., min_length=5, description="Mandatory reason for workflow status transition")
    resolution_summary: Optional[str] = None

class GrievanceAssignRequest(BaseModel):
    assigned_to_user_id: int
    notes: Optional[str] = None

class GrievanceReopenRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Detailed reason for requesting case reopening")

class GrievanceEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=10, description="Mandatory justification for case escalation")
    level: Optional[EscalationLevelEnum] = EscalationLevelEnum.LEVEL_2_INSTITUTION_HEAD

class GrievanceAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_to_user_id: int
    assigned_to_name: str
    assigned_by_user_id: int
    assigned_by_name: str
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: bool

class BatchEscalationResponse(BaseModel):
    escalated_count: int
    escalated_reference_numbers: List[str]
    processed_at: datetime

class GrievanceStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: Optional[GrievanceStatusEnum] = None
    to_status: GrievanceStatusEnum
    changed_by_name: str
    reason: str
    created_at: datetime

class GrievanceMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    sender_name: str
    sender_role: str
    message: str
    is_student_visible: bool
    created_at: datetime

class GrievanceInternalNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    author_name: str
    note: str
    created_at: datetime

class GrievanceAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_size_bytes: int
    content_type: str
    is_internal_only: bool
    created_at: datetime

class GrievanceFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    satisfies_resolution: bool
    comments: Optional[str] = None
    created_at: datetime

class GrievanceSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    institution_id: int
    institution_name: str
    category_id: int
    category_name: str
    subcategory: Optional[str] = None
    title: str
    status: GrievanceStatusEnum
    priority: GrievancePriorityEnum
    is_confidential: bool
    assigned_officer_id: Optional[int] = None
    assigned_officer_name: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class GrievanceDetailResponse(GrievanceSummaryResponse):
    model_config = ConfigDict(from_attributes=True)

    description: str
    preferred_contact: str
    student_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    student_id_number: Optional[str] = None
    resolution_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # AI Assist Data
    ai_suggested_category_id: Optional[int] = None
    ai_suggested_category_name: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_suggested_priority: Optional[GrievancePriorityEnum] = None
    ai_explanation: Optional[str] = None
    ai_duplicate_suspected: bool = False
    ai_duplicate_ref: Optional[str] = None
    
    status_history: List[GrievanceStatusHistoryResponse] = []
    messages: List[GrievanceMessageResponse] = []
    internal_notes: List[GrievanceInternalNoteResponse] = []
    attachments: List[GrievanceAttachmentResponse] = []
    feedback: Optional[GrievanceFeedbackResponse] = None

class GrievancePublicTrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference_number: str
    institution_name: str
    category_name: str
    title: str
    status: GrievanceStatusEnum
    priority: GrievancePriorityEnum
    created_at: datetime
    updated_at: datetime
    resolution_summary: Optional[str] = None
    status_history: List[GrievanceStatusHistoryResponse] = []
