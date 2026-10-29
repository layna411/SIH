from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Enum, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from app.database.base import Base
from app.models.enums import UserRoleEnum

class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False) # e.g. INST001 / AISHE code
    institution_code = synonym("code")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    institution_type: Mapped[Optional[str]] = mapped_column(String(50), default="COLLEGE", nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    official_email = synonym("contact_email")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="VERIFIED", nullable=False) # PENDING, VERIFIED, REJECTED
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    aicte_permanent_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    is_aicte_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    memberships: Mapped[List["InstitutionMembership"]] = relationship("InstitutionMembership", back_populates="institution", cascade="all, delete-orphan")
    grievances: Mapped[List["Grievance"]] = relationship("Grievance", back_populates="institution")
    aliases: Mapped[List["InstitutionAlias"]] = relationship("InstitutionAlias", back_populates="institution", cascade="all, delete-orphan")
    aicte_cases = relationship("AICTECase", back_populates="institution", cascade="all, delete-orphan")

class InstitutionAlias(Base):
    __tablename__ = "institution_aliases"
    __table_args__ = (
        UniqueConstraint("institution_id", "normalized_alias", name="uq_institution_normalized_alias"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    alias_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), default="MANUAL", nullable=False) # MANUAL, ACRONYM, FORMER_NAME, STATE_PORTAL
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    institution: Mapped["Institution"] = relationship("Institution", back_populates="aliases")
    created_by: Mapped[Optional["User"]] = relationship("User")

class InstitutionMembership(Base):
    __tablename__ = "institution_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "institution_id", name="uq_user_institution_membership"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True, index=True)
    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    institution: Mapped["Institution"] = relationship("Institution", back_populates="memberships")
    role_obj: Mapped[Optional["Role"]] = relationship("Role", back_populates="memberships")

class RegulatoryJurisdiction(Base):
    __tablename__ = "regulatory_jurisdictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jurisdiction_type: Mapped[str] = mapped_column(String(50), default="STATE", nullable=False) # STATE, REGION, INSTITUTION
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    institution_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    jurisdiction_code: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="regulatory_jurisdictions")
    institution: Mapped[Optional["Institution"]] = relationship("Institution")

from app.models.user import User
from app.models.role import Role
from app.models.grievance import Grievance

