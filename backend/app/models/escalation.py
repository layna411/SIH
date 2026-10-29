from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Enum, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.models.enums import EscalationLevelEnum

class GrievanceEscalation(Base):
    __tablename__ = "grievance_escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    escalated_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    escalation_level: Mapped[EscalationLevelEnum] = mapped_column(Enum(EscalationLevelEnum), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, REVIEWED, RESOLVED
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_handling_scope: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    new_handling_scope: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="escalations")
    escalated_by: Mapped[Optional["User"]] = relationship("User")

from app.models.grievance import Grievance
from app.models.user import User
