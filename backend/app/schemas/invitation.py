from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.enums import UserRoleEnum

class UserInviteRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    role: UserRoleEnum
    institution_id: Optional[int] = None
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)
    staff_id_number: Optional[str] = Field(None, max_length=50)
    jurisdiction_state: Optional[str] = Field(None, max_length=100)
    jurisdiction_code: Optional[str] = Field(None, max_length=50)
    jurisdiction_notes: Optional[str] = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full name must contain at least 2 characters.")
        return clean

class UserInviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRoleEnum
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    staff_id_number: Optional[str] = None
    jurisdiction_state: Optional[str] = None
    jurisdiction_code: Optional[str] = None
    status: str
    expires_at: datetime
    created_at: datetime
    delivery_status: str
    invitation_link: Optional[str] = None
    notes: Optional[str] = None

class AcceptInvitationRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=128, description="New account password (min 8 chars)")
    phone_number: Optional[str] = Field(None, max_length=30)

class InvitationValidateResponse(BaseModel):
    is_valid: bool
    email: str
    full_name: str
    role: UserRoleEnum
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    expires_at: datetime
