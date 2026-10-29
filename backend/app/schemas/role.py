from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
