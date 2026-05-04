import pytest
from datetime import datetime
from app.models.file_model import FileObject, SourceEnum
from pydantic import ValidationError

def test_file_object_creation():
    now = datetime.now()
    file_obj = FileObject(
        path="/tmp/test.txt",
        filename="test.txt",
        extension=".txt",
        size_mb=1.5,
        created_at=now,
        confidence_score=2,
        source=SourceEnum.LLM_SHALLOW,
        suggested_action=False
    )
    assert file_obj.path == "/tmp/test.txt"
    assert file_obj.filename == "test.txt"
    assert file_obj.extension == ".txt"
    assert file_obj.size_mb == 1.5
    assert file_obj.created_at == now
    assert file_obj.confidence_score == 2
    assert file_obj.source == SourceEnum.LLM_SHALLOW
    assert file_obj.suggested_action == False

def test_file_object_validation():
    now = datetime.now()
    with pytest.raises(ValidationError):
        FileObject(
            path="/tmp/test.txt",
            filename="test.txt",
            extension=".txt",
            size_mb=1.5,
            created_at=now,
            confidence_score=4,  # Invalid confidence score
        )
