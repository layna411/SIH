import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationOutbox
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger("eduresolve.notification")

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    link: Optional[str] = None,
    notification_type: str = "INFO",
    email_notify: bool = True,
    severity: str = "INFO",
    category: Optional[str] = None,
    reference_id: Optional[str] = None,
    requires_acknowledgement: bool = False
) -> Notification:
    """
    Create in-app notification with atomic transactional outbox entry.
    Ensures that notifications are reliably stored even if outbound email is delayed or fails.
    Supports alert categories, severity tiers, reference correlation, and acknowledgement requirements.
    """
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        link=link,
        notification_type=notification_type,
        severity=severity,
        category=category,
        reference_id=reference_id,
        requires_acknowledgement=requires_acknowledgement,
        is_acknowledged=False,
        acknowledged_at=None
    )
    db.add(notif)
    db.flush()

    # Create transactional outbox entry if email notifications are enabled
    if email_notify and settings.NOTIFICATION_EMAIL_ENABLED:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.email:
            outbox_entry = NotificationOutbox(
                notification_id=notif.id,
                user_id=user.id,
                channel="EMAIL",
                recipient_email=user.email,
                subject=f"[{settings.APP_NAME}] {title}",
                body=f"Hello {user.full_name},\n\n{message}\n\nView details: {settings.FRONTEND_URL}{link or ''}",
                status="PENDING",
                attempts=0,
                created_at=datetime.now(timezone.utc)
            )
            db.add(outbox_entry)

    db.commit()
    db.refresh(notif)
    return notif

def dispatch_pending_outbox(db: Session, max_batch: int = 25) -> int:
    """
    Process pending outbound email notifications from the transactional outbox table.
    Enforces retry limits, prevents duplicate deliveries, and records attempt metadata.
    """
    pending = db.query(NotificationOutbox).filter(
        NotificationOutbox.status == "PENDING",
        NotificationOutbox.attempts < settings.NOTIFICATION_OUTBOX_MAX_RETRIES
    ).order_by(NotificationOutbox.created_at.asc()).limit(max_batch).all()

    if not pending:
        return 0

    dispatched = 0
    now = datetime.now(timezone.utc)

    for entry in pending:
        entry.attempts += 1
        entry.last_attempt_at = now

        if not settings.SMTP_HOST:
            # Development fallback logging
            logger.info(
                f"[DEV OUTBOX DISPATCH] Email to {entry.recipient_email} | Subject: {entry.subject}"
            )
            entry.status = "SENT"
            entry.sent_at = now
            dispatched += 1
            continue

        # SMTP dispatch
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = entry.subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = entry.recipient_email
            msg.attach(MIMEText(entry.body, "plain", "utf-8"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            entry.status = "SENT"
            entry.sent_at = now
            dispatched += 1
        except Exception as e:
            error_str = str(e)
            entry.error_message = error_str
            if entry.attempts >= settings.NOTIFICATION_OUTBOX_MAX_RETRIES:
                entry.status = "FAILED"
            logger.warning(
                f"Failed outbox delivery #{entry.id} to {entry.recipient_email} (Attempt {entry.attempts}): {error_str}"
            )

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit outbox dispatch updates: {e}", exc_info=True)

    return dispatched
