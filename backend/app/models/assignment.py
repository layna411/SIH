from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class GrievanceAssignment(Base):
    __tablename__ = "grievance_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="assignments")
    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_grievances")
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_user_id])

from app.models.grievance import Grievance
from app.models.user import User
