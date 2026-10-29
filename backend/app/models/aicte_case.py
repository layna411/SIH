from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Enum, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.models.enums import (
    AICTECaseStatusEnum,
    AICTECaseSourceTypeEnum,
    AICTEComplainantTypeEnum,
    AICTECaseActionTypeEnum,
    GrievancePriorityEnum,
)

class AICTECase(Base):
    __tablename__ = "aicte_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    case_reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    source_grievance_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type: Mapped[AICTECaseSourceTypeEnum] = mapped_column(Enum(AICTECaseSourceTypeEnum), default=AICTECaseSourceTypeEnum.DIRECT, nullable=False, index=True)
    official_reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    received_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    complainant_type: Mapped[AICTEComplainantTypeEnum] = mapped_column(Enum(AICTEComplainantTypeEnum), default=AICTEComplainantTypeEnum.STAKEHOLDER, nullable=False)
    complainant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    complainant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    complainant_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[AICTECaseStatusEnum] = mapped_column(Enum(AICTECaseStatusEnum), default=AICTECaseStatusEnum.RECEIVED, nullable=False, index=True)
    current_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizational_units.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    priority: Mapped[GrievancePriorityEnum] = mapped_column(Enum(GrievancePriorityEnum), default=GrievancePriorityEnum.NORMAL, nullable=False, index=True)
    
    last_action_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    next_action_required: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_action_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_disposal_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disposed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    institution = relationship("Institution", back_populates="aicte_cases")
    source_grievance = relationship("Grievance", back_populates="aicte_case_referrals")
    current_unit = relationship("OrganizationalUnit", back_populates="cases")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    actions = relationship("CaseAction", back_populates="case", cascade="all, delete-orphan", order_by="CaseAction.action_at.asc()")
    transfers = relationship("AICTECaseTransfer", back_populates="case", cascade="all, delete-orphan", order_by="AICTECaseTransfer.initiated_at.desc()")


class CaseAction(Base):
    __tablename__ = "case_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("aicte_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type: Mapped[AICTECaseActionTypeEnum] = mapped_column(Enum(AICTECaseActionTypeEnum), nullable=False, index=True)
    action_title: Mapped[str] = mapped_column(String(255), nullable=False)
    action_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizational_units.id", ondelete="RESTRICT"), nullable=False, index=True)
    performed_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    action_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_document_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_action_required: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_action_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    case = relationship("AICTECase", back_populates="actions")
    unit = relationship("OrganizationalUnit")
    performed_by_user = relationship("User", foreign_keys=[performed_by_user_id])
