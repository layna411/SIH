from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Enum, Integer, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.models.enums import AICTETransferStatusEnum

class AICTECaseTransfer(Base):
    __tablename__ = "aicte_case_transfers"
    __table_args__ = (
        CheckConstraint("from_unit_id != to_unit_id", name="chk_aicte_transfer_diff_units"),
        Index("ix_aicte_transfers_case_status", "case_id", "transfer_status"),
        Index("ix_aicte_transfers_to_unit_status", "to_unit_id", "transfer_status"),
        Index("ix_aicte_transfers_from_unit_status", "from_unit_id", "transfer_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("aicte_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    from_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizational_units.id", ondelete="RESTRICT"), nullable=False, index=True)
    to_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizational_units.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    initiated_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    proposed_assignee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transfer_reason: Mapped[str] = mapped_column(Text, nullable=False)
    handover_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prior_case_status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    transfer_status: Mapped[AICTETransferStatusEnum] = mapped_column(
        Enum(AICTETransferStatusEnum),
        default=AICTETransferStatusEnum.PENDING_ACCEPTANCE,
        nullable=False,
        index=True
    )
    
    initiated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    responded_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    response_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_assignee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    case = relationship("AICTECase", back_populates="transfers")
    from_unit = relationship("OrganizationalUnit", foreign_keys=[from_unit_id])
    to_unit = relationship("OrganizationalUnit", foreign_keys=[to_unit_id])
    initiated_by_user = relationship("User", foreign_keys=[initiated_by_user_id])
    proposed_assignee = relationship("User", foreign_keys=[proposed_assignee_id])
    responded_by_user = relationship("User", foreign_keys=[responded_by_user_id])
    accepted_assignee = relationship("User", foreign_keys=[accepted_assignee_id])
