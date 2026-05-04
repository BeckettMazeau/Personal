from enum import Enum
from pydantic import BaseModel, Field
from typing import List

class FileSource(str, Enum):
    static = "static"
    llm_shallow = "llm_shallow"
    llm_deep = "llm_deep"

class FileObject(BaseModel):
    path: str
    filename: str
    extension: str
    size_mb: float
    created_at: float
    confidence_score: int = Field(ge=1, le=3, description="1 (Protect) to 3 (Safe to Delete)")
    source: FileSource
    suggested_action: bool

class FileAssessment(BaseModel):
    file_path: str
    suggested_action: str
    confidence_score: int = Field(
        ge=1, le=3, description="1 (Protect) to 3 (Safe to Delete)"
    )

class StateMap(BaseModel):
    files: List[FileAssessment]
