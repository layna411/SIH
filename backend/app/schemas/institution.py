from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from app.models.enums import UserRoleEnum

class InstitutionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    institution_code: str = Field(..., min_length=2, max_length=50)
    institution_type: Optional[str] = Field("COLLEGE", max_length=50)
    state: str = Field(..., min_length=2, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    official_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=30)
    website: Optional[str] = Field(None, max_length=255)
    aicte_permanent_id: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=50)
    is_aicte_verified: Optional[bool] = False

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "institution_code" not in data and "code" in data:
                data["institution_code"] = data["code"]
            elif "code" not in data and "institution_code" in data:
                data["code"] = data["institution_code"]
            if "official_email" not in data and "contact_email" in data:
                data["official_email"] = data["contact_email"]
            elif "contact_email" not in data and "official_email" in data:
                data["contact_email"] = data["official_email"]
        return data

    @field_validator("institution_code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("aicte_permanent_id")
    @classmethod
    def normalize_aicte_id(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        clean = v.strip().upper()
        return clean if clean else None

    @field_validator("official_email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    institution_type: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    official_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    website: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    verification_status: Optional[str] = Field(None, pattern="^(PENDING|VERIFIED|REJECTED)$")
    aicte_permanent_id: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=50)
    is_aicte_verified: Optional[bool] = None

    @field_validator("aicte_permanent_id")
    @classmethod
    def normalize_aicte_id(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        clean = v.strip().upper()
        return clean if clean else None

class InstitutionVerifyAICTE(BaseModel):
    aicte_permanent_id: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=50)
    is_aicte_verified: bool = True

    @field_validator("aicte_permanent_id")
    @classmethod
    def normalize_aicte_id(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        clean = v.strip().upper()
        return clean if clean else None

class InstitutionAliasCreate(BaseModel):
    alias_name: str = Field(..., min_length=2, max_length=255)
    source: Optional[str] = Field("MANUAL", max_length=100)
    is_verified: Optional[bool] = True

    @field_validator("alias_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 2:
            raise ValueError("Alias name must be at least 2 characters.")
        return s

class InstitutionAliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution_id: int
    alias_name: str
    normalized_alias: str
    source: str = "MANUAL"
    is_verified: bool = True
    is_active: bool = True
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    institution_code: str
    institution_type: Optional[str] = "COLLEGE"
    state: str
    district: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    contact_email: str
    official_email: str
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    verification_status: str = "VERIFIED"
    is_active: bool
    is_verified: bool
    aicte_permanent_id: Optional[str] = None
    region: Optional[str] = None
    is_aicte_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    admin_account_email: Optional[str] = None
    default_password: Optional[str] = None
    account_created: Optional[bool] = False
    aliases: Optional[List[InstitutionAliasResponse]] = None

class InstitutionMembershipCreate(BaseModel):
    user_id: int
    institution_id: int
    role: UserRoleEnum
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)

class InstitutionMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    institution_id: int
    role_id: Optional[int] = None
    role: UserRoleEnum
    department: Optional[str] = None
    designation: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class JurisdictionCreate(BaseModel):
    user_id: int
    jurisdiction_type: str = Field("STATE", max_length=50)
    state: str = Field(..., max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    institution_id: Optional[int] = None
    jurisdiction_code: str = Field(..., max_length=50)
    notes: Optional[str] = Field(None, max_length=255)

class JurisdictionResponse(BaseModel):
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
    created_at: datetime
    updated_at: Optional[datetime] = None

