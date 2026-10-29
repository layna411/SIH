from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class GrievanceMessage(Base):
    __tablename__ = "grievance_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_student_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="messages")
    sender: Mapped["User"] = relationship("User")

class GrievanceInternalNote(Base):
    __tablename__ = "grievance_internal_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="internal_notes")
    author: Mapped["User"] = relationship("User")

from app.models.grievance import Grievance
from app.models.user import User
