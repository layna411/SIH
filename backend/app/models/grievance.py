from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.models.enums import GrievanceStatusEnum, GrievancePriorityEnum

class Grievance(Base):
    __tablename__ = "grievances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    reference_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievance_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[GrievanceStatusEnum] = mapped_column(Enum(GrievanceStatusEnum), default=GrievanceStatusEnum.SUBMITTED, nullable=False, index=True)
    priority: Mapped[GrievancePriorityEnum] = mapped_column(Enum(GrievancePriorityEnum), default=GrievancePriorityEnum.NORMAL, nullable=False, index=True)
    
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_contact: Mapped[str] = mapped_column(String(50), default="portal", nullable=False)
    
    # AI Assist fields
    ai_suggested_category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("grievance_categories.id"), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_suggested_priority: Mapped[Optional[GrievancePriorityEnum]] = mapped_column(Enum(GrievancePriorityEnum), nullable=True)
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_duplicate_suspected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_duplicate_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sla_warning_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], back_populates="submitted_grievances")
    institution: Mapped["Institution"] = relationship("Institution", back_populates="grievances")
    category: Mapped["GrievanceCategory"] = relationship("GrievanceCategory", foreign_keys=[category_id], back_populates="grievances")
    ai_suggested_category: Mapped[Optional["GrievanceCategory"]] = relationship("GrievanceCategory", foreign_keys=[ai_suggested_category_id])
    assigned_officer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_officer_id])
    
    assignments: Mapped[list["GrievanceAssignment"]] = relationship("GrievanceAssignment", back_populates="grievance", cascade="all, delete-orphan")
    status_history: Mapped[list["GrievanceStatusHistory"]] = relationship("GrievanceStatusHistory", back_populates="grievance", cascade="all, delete-orphan", order_by="GrievanceStatusHistory.created_at.desc()")
    messages: Mapped[list["GrievanceMessage"]] = relationship("GrievanceMessage", back_populates="grievance", cascade="all, delete-orphan", order_by="GrievanceMessage.created_at.asc()")
    internal_notes: Mapped[list["GrievanceInternalNote"]] = relationship("GrievanceInternalNote", back_populates="grievance", cascade="all, delete-orphan", order_by="GrievanceInternalNote.created_at.desc()")
    attachments: Mapped[list["GrievanceAttachment"]] = relationship("GrievanceAttachment", back_populates="grievance", cascade="all, delete-orphan")
    escalations: Mapped[list["GrievanceEscalation"]] = relationship("GrievanceEscalation", back_populates="grievance", cascade="all, delete-orphan")
    feedback: Mapped[Optional["GrievanceFeedback"]] = relationship("GrievanceFeedback", back_populates="grievance", uselist=False, cascade="all, delete-orphan")
    aicte_case_referrals = relationship("AICTECase", back_populates="source_grievance")

class GrievanceStatusHistory(Base):
    __tablename__ = "grievance_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[Optional[GrievanceStatusEnum]] = mapped_column(Enum(GrievanceStatusEnum), nullable=True)
    to_status: Mapped[GrievanceStatusEnum] = mapped_column(Enum(GrievanceStatusEnum), nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="status_history")
    changed_by: Mapped["User"] = relationship("User")

from app.models.user import User
from app.models.institution import Institution
from app.models.category import GrievanceCategory
from app.models.assignment import GrievanceAssignment
from app.models.communication import GrievanceMessage, GrievanceInternalNote
from app.models.attachment import GrievanceAttachment
from app.models.escalation import GrievanceEscalation
from app.models.feedback import GrievanceFeedback
