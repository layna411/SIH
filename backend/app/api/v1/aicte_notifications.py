from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.permissions import get_current_active_user, require_roles
from app.models.enums import UserRoleEnum
from app.models.user import User
from app.schemas.aicte_alert import (
    AICTENotificationResponse,
    AICTENotificationListResponse,
    AICTEAlertSummaryResponse,
    AICTEOverdueAlertListResponse,
    AICTEAlertConfigurationResponse,
    AICTEAlertConfigurationUpdateRequest,
)
from app.services.aicte_alert_service import AICTEAlertService

router = APIRouter(prefix="/aicte", tags=["AICTE Notifications & Alert Center"])

# ---------------------------------------------------------------------------
# 1. Centralized Notifications List & Filtering
# ---------------------------------------------------------------------------
@router.get("/notifications", response_model=AICTENotificationListResponse)
def get_aicte_notifications(
    category: Optional[str] = Query(None, description="Filter by category (e.g. SLA_OVERDUE, TRANSFER_PENDING, OVERLAP_PENDING)"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, WARNING, INFO)"),
    is_read: Optional[bool] = Query(None, description="Filter by read state"),
    is_acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement state"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve paginated in-app notifications and alerts strictly scoped to current user:
    - Never displays notifications belonging to other officers.
    - Server-side filtering by category, severity, read state, and acknowledgement.
    """
    return AICTEAlertService.get_user_notifications(
        db=db,
        current_user=current_user,
        category=category,
        severity=severity,
        is_read=is_read,
        is_acknowledged=is_acknowledged,
        page=page,
        page_size=page_size
    )

# ---------------------------------------------------------------------------
# 2. Unread & Unacknowledged Count Badge
# ---------------------------------------------------------------------------
@router.get("/notifications/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Return count of unread and unacknowledged notifications for caller."""
    summary = AICTEAlertService.get_alerts_summary(db, current_user)
    return {
        "unread_count": summary.total_unread,
        "unacknowledged_count": summary.total_unacknowledged,
        "critical_count": summary.critical_count
    }

# ---------------------------------------------------------------------------
# 3. Notification Detail
# ---------------------------------------------------------------------------
@router.get("/notifications/{notification_id}", response_model=AICTENotificationResponse)
def get_notification_detail(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve detailed metadata of a specific notification with recipient ownership enforcement."""
    return AICTEAlertService.get_notification_detail(db, notification_id, current_user)

# ---------------------------------------------------------------------------
# 4. Mark Read Lifecycle
# ---------------------------------------------------------------------------
@router.post("/notifications/{notification_id}/read", response_model=AICTENotificationResponse)
@router.put("/notifications/{notification_id}/read", response_model=AICTENotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark an individual notification as read.
    Guaranteed invariant: Never mutates or resolves the underlying case or alert condition.
    """
    return AICTEAlertService.mark_read(db, notification_id, current_user)

# ---------------------------------------------------------------------------
# 5. Mark All Read
# ---------------------------------------------------------------------------
@router.post("/notifications/read-all")
@router.put("/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all eligible unread notifications for current user as read."""
    return AICTEAlertService.mark_all_read(db, current_user)

# ---------------------------------------------------------------------------
# 6. Formal Alert Acknowledgement
# ---------------------------------------------------------------------------
@router.post("/notifications/{notification_id}/acknowledge", response_model=AICTENotificationResponse)
def acknowledge_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Formally acknowledge review of a critical operational alert:
    - Distinct from reading: records immutable timestamp of acknowledgement.
    - Requires caller recipient ownership.
    - Guaranteed invariant: Does NOT alter case procedural status or close the case.
    """
    return AICTEAlertService.acknowledge_notification(db, notification_id, current_user)

# ---------------------------------------------------------------------------
# 7. Alerts Summary & Operational Queues
# ---------------------------------------------------------------------------
@router.get("/alerts/summary", response_model=AICTEAlertSummaryResponse)
def get_alerts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve aggregated alert and operational counters:
    - Unread, unacknowledged, and critical alert counts.
    - Live breakdown by category (SLA, transfers, overlaps, assignments).
    - Scoped strictly to caller's authorized Bureau memberships and jurisdiction.
    """
    return AICTEAlertService.get_alerts_summary(db, current_user)

# ---------------------------------------------------------------------------
# 8. Live Overdue Cases Queue
# ---------------------------------------------------------------------------
@router.get("/alerts/overdue", response_model=AICTEOverdueAlertListResponse)
def get_overdue_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve live queue of active cases with overdue deadlines scoped to caller jurisdiction:
    - Categorizes NEXT_ACTION, EXPECTED_DISPOSAL, or BOTH.
    - Calculates exact days overdue from live database timestamps.
    """
    return AICTEAlertService.get_overdue_alerts(db, current_user, page=page, page_size=page_size)

# ---------------------------------------------------------------------------
# 9. Alert Configuration Management
# ---------------------------------------------------------------------------
@router.get("/alerts/configuration", response_model=AICTEAlertConfigurationResponse)
def get_alert_configuration(
    current_user: User = Depends(get_current_active_user)
):
    """Read permitted operational alert configuration thresholds."""
    return AICTEAlertService.get_configuration()

@router.patch("/alerts/configuration", response_model=AICTEAlertConfigurationResponse)
def update_alert_configuration(
    payload: AICTEAlertConfigurationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN, UserRoleEnum.REGULATORY_ADMIN))
):
    """
    Update permitted alert thresholds:
    - Restricted to SuperAdmin and RegulatoryAdmin.
    - Atomically recorded in system audit log.
    """
    return AICTEAlertService.update_configuration(db, payload, current_user)
