from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

class OrganizationalUnitBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    unit_type: str = Field("BUREAU", max_length=50) # BUREAU, CELL, REGIONAL_OFFICE, OTHER
    description: Optional[str] = None
    parent_unit_id: Optional[int] = None
    region_code: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[EmailStr] = None
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

class OrganizationalUnitCreate(OrganizationalUnitBase):
    pass

class OrganizationalUnitUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    unit_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    parent_unit_id: Optional[int] = None
    region_code: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip().upper()
        return None

class OrganizationalUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    unit_type: str
    description: Optional[str] = None
    parent_unit_id: Optional[int] = None
    parent_unit_name: Optional[str] = None
    region_code: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: Optional[int] = 0

class BureauMembershipCreate(BaseModel):
    user_id: int
    membership_role: str = Field("BUREAU_OFFICER", max_length=50) # BUREAU_OFFICER, BUREAU_HEAD, REGIONAL_OFFICER, MEMBER
    designation: Optional[str] = Field(None, max_length=100)

class BureauMembershipUpdate(BaseModel):
    membership_role: Optional[str] = Field(None, max_length=50)
    designation: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class BureauMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    organizational_unit_id: int
    unit_code: Optional[str] = None
    unit_name: Optional[str] = None
    membership_role: str
    designation: Optional[str] = None
    is_active: bool
    assigned_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
