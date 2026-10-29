from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.notification import Notification
from app.models.user import User
from app.core.permissions import get_current_user, require_roles
from app.models.enums import UserRoleEnum
from app.schemas.feedback import NotificationResponse
from app.services.notification_service import dispatch_pending_outbox

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Limit for pagination"),
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated in-app notifications for the logged in user with strict recipient ownership.
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return count of unread notifications for recipient."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}

@router.put("/{id}/read", response_model=NotificationResponse)
def mark_read(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark single notification as read with ownership verification."""
    notif = db.query(Notification).filter(
        Notification.id == id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

@router.put("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread notifications for user as read."""
    updated = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read.", "marked_count": updated}

@router.post("/outbox/process")
def process_outbox(
    max_batch: int = Query(25, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRoleEnum.SUPER_ADMIN, UserRoleEnum.INSTITUTION_HEAD])),
    db: Session = Depends(get_db)
):
    """Manual trigger to process pending transactional outbox notifications."""
    dispatched = dispatch_pending_outbox(db, max_batch=max_batch)
    return {"status": "success", "dispatched_count": dispatched}
