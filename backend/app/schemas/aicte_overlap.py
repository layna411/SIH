from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import (
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTEDetectionMethodEnum,
    AICTECaseLinkTypeEnum,
)

class OverlapReviewRequest(BaseModel):
    action: AICTEOverlapReviewStatusEnum
    review_notes: str = Field(..., min_length=3, max_length=2000, description="Justification for review decision.")

class ManualLinkCreateRequest(BaseModel):
    target_case_id: int
    link_type: AICTECaseLinkTypeEnum = AICTECaseLinkTypeEnum.RELATED_TO
    notes: Optional[str] = Field(None, max_length=1000)

class LinkUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

class AICTECaseOverlapResponse(BaseModel):
    id: int
    case_id_low: int
    case_id_high: int
    overlap_type: AICTEOverlapTypeEnum
    match_score: Optional[float] = None
    match_reasons: Dict[str, Any]
    detection_method: AICTEDetectionMethodEnum
    review_status: AICTEOverlapReviewStatusEnum
    detected_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by_user_id: Optional[int] = None
    reviewed_by_name: Optional[str] = None
    review_notes: Optional[str] = None
    case_low: Optional[Dict[str, Any]] = None
    case_high: Optional[Dict[str, Any]] = None
    active_link_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AICTECaseOverlapListResponse(BaseModel):
    items: List[AICTECaseOverlapResponse]
    total: int
    page: int
    page_size: int

class AICTECaseLinkResponse(BaseModel):
    id: int
    case_id_low: int
    case_id_high: int
    linked_case_id: int
    linked_case_reference: str
    linked_case_subject: str
    linked_case_category: str
    linked_case_unit_code: Optional[str] = None
    linked_case_status: str
    link_type: AICTECaseLinkTypeEnum
    source_overlap_id: Optional[int] = None
    created_by_user_id: int
    created_by_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OverlapHistoryItem(BaseModel):
    id: int
    action: str
    actor_name: Optional[str] = None
    timestamp: datetime
    details: Dict[str, Any]
