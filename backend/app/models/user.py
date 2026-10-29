from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from app.database.base import Base
from app.models.enums import UserRoleEnum

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash = synonym("hashed_password")
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), default=UserRoleEnum.STUDENT, nullable=False)
    student_id_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # roll number / enrollment id
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    memberships: Mapped[List["InstitutionMembership"]] = relationship("InstitutionMembership", back_populates="user", cascade="all, delete-orphan")
    regulatory_jurisdictions: Mapped[List["RegulatoryJurisdiction"]] = relationship("RegulatoryJurisdiction", back_populates="user", cascade="all, delete-orphan")
    submitted_grievances: Mapped[List["Grievance"]] = relationship("Grievance", back_populates="student", foreign_keys="Grievance.student_id")
    assigned_grievances: Mapped[List["GrievanceAssignment"]] = relationship("GrievanceAssignment", back_populates="assigned_to", foreign_keys="GrievanceAssignment.assigned_to_user_id")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    invitations_sent: Mapped[List["UserInvitation"]] = relationship("UserInvitation", back_populates="invited_by", foreign_keys="UserInvitation.invited_by_user_id")
    verification_tokens: Mapped[List["EmailVerificationToken"]] = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    bureau_memberships: Mapped[List["BureauMembership"]] = relationship("BureauMembership", back_populates="user", foreign_keys="BureauMembership.user_id", cascade="all, delete-orphan")


from app.models.institution import InstitutionMembership, RegulatoryJurisdiction
from app.models.bureau_membership import BureauMembership
from app.models.grievance import Grievance
from app.models.assignment import GrievanceAssignment
from app.models.notification import Notification
from app.models.invitation import UserInvitation
from app.models.email_verification import EmailVerificationToken
