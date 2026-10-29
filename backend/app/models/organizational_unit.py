from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class OrganizationalUnit(Base):
    __tablename__ = "organizational_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False) # e.g. RB, PGRC, AB, RO_NORTH
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(50), default="BUREAU", nullable=False) # BUREAU, CELL, REGIONAL_OFFICE, OTHER
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizational_units.id", ondelete="SET NULL"), nullable=True, index=True)
    region_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g. NORTH, WEST, SOUTH, CENTRAL, EAST
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    parent_unit: Mapped[Optional["OrganizationalUnit"]] = relationship("OrganizationalUnit", remote_side=[id], back_populates="child_units")
    child_units: Mapped[List["OrganizationalUnit"]] = relationship("OrganizationalUnit", back_populates="parent_unit")
    memberships: Mapped[List["BureauMembership"]] = relationship("BureauMembership", back_populates="organizational_unit", cascade="all, delete-orphan")
    cases = relationship("AICTECase", back_populates="current_unit")

from app.models.bureau_membership import BureauMembership
