from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class BureauMembership(Base):
    __tablename__ = "bureau_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organizational_unit_id", name="uq_user_bureau_membership"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organizational_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizational_units.id", ondelete="CASCADE"), nullable=False, index=True)
    membership_role: Mapped[str] = mapped_column(String(50), default="BUREAU_OFFICER", nullable=False) # BUREAU_OFFICER, BUREAU_HEAD, REGIONAL_OFFICER, MEMBER
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="bureau_memberships")
    organizational_unit: Mapped["OrganizationalUnit"] = relationship("OrganizationalUnit", back_populates="memberships")
    assigned_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by_user_id])

from app.models.user import User
from app.models.organizational_unit import OrganizationalUnit
