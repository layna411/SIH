from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)

class InternalNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=5000)
