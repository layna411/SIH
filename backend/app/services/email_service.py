import smtplib
import secrets
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.email_verification import EmailVerificationToken
from app.services.audit_service import log_audit

logger = logging.getLogger("eduresolve.email")

class EmailService:
    @staticmethod
    def generate_verification_token(db: Session, user: User) -> Tuple[str, EmailVerificationToken]:
        """
        Generate a cryptographically secure single-use email verification token.
        Only the SHA-256 hash is persisted in the database.
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

        # Invalidate any existing unused tokens for this user
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False
        ).update({"is_used": True, "used_at": now})

        token_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False,
            created_at=now
        )
        db.add(token_record)
        db.commit()
        db.refresh(token_record)

        return raw_token, token_record

    @staticmethod
    def can_resend_verification(db: Session, user: User) -> Tuple[bool, int]:
        """
        Check if user has waited the required cooldown period before requesting another token.
        Returns (can_resend, remaining_seconds).
        """
        latest = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id
        ).order_by(EmailVerificationToken.created_at.desc()).first()

        if not latest:
            return True, 0

        now = datetime.now(timezone.utc)
        elapsed = (now - latest.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        cooldown = settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS

        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            return False, remaining

        return True, 0

    @classmethod
    def send_verification_email(cls, user: User, raw_token: str, db: Optional[Session] = None) -> bool:
        """
        Dispatch account email verification.
        If SMTP is configured, uses outbound SMTP with STARTTLS.
        If SMTP is unconfigured (development/test), logs to console backend safely.
        """
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
        subject = f"Verify Your {settings.APP_NAME} Account"
        
        body_text = (
            f"Hello {user.full_name},\n\n"
            f"Thank you for registering on {settings.APP_NAME}.\n"
            f"Please verify your email address by visiting the following link:\n\n"
            f"{verification_link}\n\n"
            f"This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.\n"
            f"If you did not create this account, please disregard this email."
        )

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: sans-serif; color: #334155; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;">
                <h2 style="color: #1e293b; margin-top: 0;">Welcome to {settings.APP_NAME}</h2>
                <p>Hello <strong>{user.full_name}</strong>,</p>
                <p>Thank you for registering. Please click the button below to verify your email address:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">Verify Email Address</a>
                </p>
                <p style="font-size: 12px; color: #64748b;">Or copy and paste this link into your browser:<br>
                    <a href="{verification_link}" style="color: #2563eb; word-break: break-all;">{verification_link}</a>
                </p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                <p style="font-size: 11px; color: #94a3b8; margin-bottom: 0;">This single-use link expires in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours. If you did not register, please ignore this email.</p>
            </div>
        </body>
        </html>
        """

        if not settings.SMTP_HOST:
            # Development / local test logging backend
            logger.info(
                f"[DEV EMAIL BACKEND] Verification email dispatched to '{user.email}'. "
                f"Verification link: {verification_link}"
            )
            return True

        # Production SMTP Delivery
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = user.email

            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email verification successfully delivered via SMTP to '{user.email}'")
            return True
        except Exception as e:
            logger.warning(f"SMTP delivery failed to '{user.email}': {e}. System will remain functional.")
            return False

    @staticmethod
    def verify_email_token(db: Session, raw_token: str) -> Tuple[bool, str, Optional[User]]:
        """
        Verify raw email verification token against database SHA-256 hash.
        Marks token used and updates user email verification status.
        """
        token_clean = raw_token.strip()
        token_hash = hashlib.sha256(token_clean.encode("utf-8")).hexdigest()

        token_record = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token_hash == token_hash
        ).first()

        if not token_record:
            return False, "Invalid or unrecognized verification token.", None

        if token_record.is_used:
            return False, "This verification link has already been used.", None

        now = datetime.now(timezone.utc)
        if token_record.expires_at.replace(tzinfo=timezone.utc) < now:
            return False, "This verification link has expired. Please request a new one.", None

        # Activate email verification
        token_record.is_used = True
        token_record.used_at = now

        user = db.query(User).filter(User.id == token_record.user_id).first()
        if user:
            user.is_email_verified = True
            db.commit()
            db.refresh(user)

            log_audit(
                db=db,
                action="VERIFY_EMAIL",
                entity_type="USER",
                user_id=user.id,
                entity_id=str(user.id),
                details=f"Email {user.email} successfully verified via token."
            )
            return True, "Email verified successfully.", user

        db.commit()
        return False, "Associated user account could not be found.", None

email_service = EmailService()
