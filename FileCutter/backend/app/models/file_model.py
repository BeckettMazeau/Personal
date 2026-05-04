from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceEnum(str, Enum):
    STATIC = "static"
    LLM_SHALLOW = "llm_shallow"
    LLM_DEEP = "llm_deep"


class FileObject(BaseModel):
    path: str
    filename: str
    extension: str
    size_mb: float
    created_at: datetime
    confidence_score: Optional[int] = Field(None, ge=1, le=3)
    source: Optional[SourceEnum] = None
    suggested_action: Optional[bool] = None
