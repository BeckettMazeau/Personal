import pytest
import os
import tempfile
from app.services.file_service import FileService
from app.models.file_model import SourceEnum

@pytest.mark.asyncio
async def test_scan_directory():
    service = FileService()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("test")
        with open(os.path.join(temp_dir, "test.exe"), "w") as f:
            f.write("test installer")
        with open(os.path.join(temp_dir, "test.tmp"), "w") as f:
            f.write("test temp")

        results = await service.scan_directory(temp_dir)

        assert len(results) == 3

        # Check static triaging
        exe_file = next(f for f in results if f.extension == ".exe")
        assert exe_file.confidence_score == 3
        assert exe_file.suggested_action == True
        assert exe_file.source == SourceEnum.STATIC

        tmp_file = next(f for f in results if f.extension == ".tmp")
        assert tmp_file.confidence_score == 3
        assert tmp_file.suggested_action == True
        assert tmp_file.source == SourceEnum.STATIC

        txt_file = next(f for f in results if f.extension == ".txt")
        assert txt_file.confidence_score is None
        assert txt_file.suggested_action is None
        assert txt_file.source is None
