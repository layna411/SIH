from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Enum, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.models.enums import UserRoleEnum

class UserInvitation(Base):
    __tablename__ = "user_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), nullable=False)
    institution_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    staff_id_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    jurisdiction_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    jurisdiction_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    jurisdiction_notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Secure token storage: SHA-256 hash of random urlsafe token
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    
    invited_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False) # PENDING, ACCEPTED, EXPIRED, REVOKED
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    institution: Mapped[Optional["Institution"]] = relationship("Institution")
    invited_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invited_by_user_id])

from app.models.institution import Institution
from app.models.user import User
