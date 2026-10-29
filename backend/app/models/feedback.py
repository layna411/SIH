from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class GrievanceFeedback(Base):
    __tablename__ = "grievance_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False) # 1 to 5
    satisfies_resolution: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="feedback")
    student: Mapped["User"] = relationship("User")

from app.models.grievance import Grievance
from app.models.user import User
