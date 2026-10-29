from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import EscalationLevelEnum

class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    satisfies_resolution: bool = True
    comments: Optional[str] = None

class EscalationCreate(BaseModel):
    escalation_level: EscalationLevelEnum
    reason: str = Field(..., min_length=10)

class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grievance_id: int
    escalated_by_id: int
    escalated_by_name: str
    escalation_level: EscalationLevelEnum
    reason: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    link: Optional[str] = None
    notification_type: str
    is_read: bool
    created_at: datetime
