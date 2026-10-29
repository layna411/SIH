from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class GrievanceAttachment(Base):
    __tablename__ = "grievance_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False) # Original file name
    stored_file_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True) # UUID-based safe server name
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_internal_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="attachments")
    uploader: Mapped["User"] = relationship("User")

from app.models.grievance import Grievance
from app.models.user import User
