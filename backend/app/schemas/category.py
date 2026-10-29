from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CategoryBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    default_sla_days: int = Field(default=7, ge=1, le=90)

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_sla_days: Optional[int] = Field(None, ge=1, le=90)
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
