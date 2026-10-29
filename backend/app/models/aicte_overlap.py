from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, 
    Boolean, 
    DateTime, 
    Enum, 
    Integer, 
    ForeignKey, 
    Text, 
    Float, 
    UniqueConstraint, 
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.models.enums import (
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTEDetectionMethodEnum,
    AICTECaseLinkTypeEnum,
)

class AICTECaseOverlap(Base):
    __tablename__ = "aicte_case_overlaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Canonical ordering: case_id_low < case_id_high
    case_id_low: Mapped[int] = mapped_column(Integer, ForeignKey("aicte_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id_high: Mapped[int] = mapped_column(Integer, ForeignKey("aicte_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    overlap_type: Mapped[AICTEOverlapTypeEnum] = mapped_column(Enum(AICTEOverlapTypeEnum), nullable=False, index=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_reasons: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-serialized matching signals
    detection_method: Mapped[AICTEDetectionMethodEnum] = mapped_column(
        Enum(AICTEDetectionMethodEnum), 
        default=AICTEDetectionMethodEnum.RULE_BASED, 
        nullable=False
    )
    
    review_status: Mapped[AICTEOverlapReviewStatusEnum] = mapped_column(
        Enum(AICTEOverlapReviewStatusEnum), 
        default=AICTEOverlapReviewStatusEnum.PENDING, 
        nullable=False, 
        index=True
    )
    
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id_low", "case_id_high", name="uq_aicte_case_overlap_pair"),
        CheckConstraint("case_id_low < case_id_high", name="chk_aicte_case_overlap_canonical_pair"),
    )

    # Relationships
    case_low = relationship("AICTECase", foreign_keys=[case_id_low])
    case_high = relationship("AICTECase", foreign_keys=[case_id_high])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id])
    links = relationship("AICTECaseLink", back_populates="source_overlap")


class AICTECaseLink(Base):
    __tablename__ = "aicte_case_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Canonical ordering: case_id_low < case_id_high
    case_id_low: Mapped[int] = mapped_column(Integer, ForeignKey("aicte_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id_high: Mapped[int] = mapped_column(Integer, ForeignKey("aicte_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    link_type: Mapped[AICTECaseLinkTypeEnum] = mapped_column(Enum(AICTECaseLinkTypeEnum), nullable=False, index=True)
    source_overlap_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("aicte_case_overlaps.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id_low", "case_id_high", "link_type", name="uq_aicte_case_link_type"),
        CheckConstraint("case_id_low < case_id_high", name="chk_aicte_case_link_canonical_pair"),
    )

    # Relationships
    case_low = relationship("AICTECase", foreign_keys=[case_id_low])
    case_high = relationship("AICTECase", foreign_keys=[case_id_high])
    source_overlap = relationship("AICTECaseOverlap", back_populates="links")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
