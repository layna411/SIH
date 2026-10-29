from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.enums import UserRoleEnum

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: "UserResponse"

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name")
    phone_number: Optional[str] = Field(None, max_length=30)
    institution_id: Optional[int] = None
    student_id_number: Optional[str] = Field(None, max_length=50)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full name must contain at least 2 characters.")
        return clean

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=30)
    student_id_number: Optional[str] = Field(None, max_length=50)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if len(clean) < 2:
                raise ValueError("Full name must contain at least 2 characters.")
            return clean
        return v

class InstitutionMembershipSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution_id: int
    institution_name: str
    institution_code: str
    role_id: Optional[int] = None
    role: UserRoleEnum
    department: Optional[str] = None
    designation: Optional[str] = None
    is_active: bool = True

class JurisdictionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    jurisdiction_type: str = "STATE"
    state: str
    region: Optional[str] = None
    institution_id: Optional[int] = None
    jurisdiction_code: str
    notes: Optional[str] = None
    is_active: bool = True

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone_number: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_email_verified: bool = False
    default_role: UserRoleEnum
    student_id_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    memberships: List[InstitutionMembershipSummary] = []
    regulatory_jurisdictions: List[JurisdictionSummary] = []

class UserPasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (minimum 8 characters)")
    confirm_password: Optional[str] = Field(None, min_length=8, max_length=128)

class EmailVerifyRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=255, description="Email verification token")

class EmailResendVerificationRequest(BaseModel):
    email: Optional[EmailStr] = None

