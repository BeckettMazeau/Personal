from pydantic import BaseModel, Field
from typing import List


class FileAssessment(BaseModel):
    file_path: str
    suggested_action: str
    confidence_score: int = Field(
        ge=1, le=3, description="1 (Protect) to 3 (Safe to Delete)"
    )


class StateMap(BaseModel):
    files: List[FileAssessment]
