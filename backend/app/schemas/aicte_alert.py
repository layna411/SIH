from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AICTENotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    link: Optional[str] = None
    notification_type: str
    severity: str = "INFO"
    category: Optional[str] = None
    reference_id: Optional[str] = None
    is_read: bool = False
    requires_acknowledgement: bool = False
    is_acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

class AICTENotificationListResponse(BaseModel):
    items: List[AICTENotificationResponse]
    total: int
    unread_count: int
    unacknowledged_count: int
    page: int
    page_size: int

class AICTEAlertSummaryResponse(BaseModel):
    total_unread: int
    total_unacknowledged: int
    critical_count: int
    warning_count: int
    info_count: int
    by_category: Dict[str, int]
    active_overdue_cases_count: int
    pending_transfers_count: int
    pending_overlaps_count: int
    failed_deliveries_count: int

class AICTEOverdueAlertItem(BaseModel):
    case_id: int
    case_reference: str
    subject: str
    institution_id: int
    institution_name: str
    current_unit_id: int
    current_unit_code: str
    current_unit_name: str
    assigned_officer_id: Optional[int] = None
    assigned_officer_name: Optional[str] = None
    status: str
    priority: str
    next_action_required: Optional[str] = None
    next_action_due_at: Optional[datetime] = None
    expected_disposal_at: Optional[datetime] = None
    overdue_type: str  # "NEXT_ACTION", "EXPECTED_DISPOSAL", "BOTH", "MISSING_DEADLINE"
    overdue_days: int

class AICTEOverdueAlertListResponse(BaseModel):
    items: List[AICTEOverdueAlertItem]
    total: int
    page: int
    page_size: int

class AICTEAlertConfigurationResponse(BaseModel):
    warning_window_hours: int
    dedup_window_hours: int
    transfer_pending_hours: int
    poll_interval_seconds: int
    scheduler_enabled: bool

class AICTEAlertConfigurationUpdateRequest(BaseModel):
    warning_window_hours: Optional[int] = Field(None, ge=1, le=168, description="Warning threshold hours before deadline")
    dedup_window_hours: Optional[int] = Field(None, ge=1, le=72, description="Deduplication window hours")
    transfer_pending_hours: Optional[int] = Field(None, ge=12, le=336, description="Hours before pending transfer flags warning")
