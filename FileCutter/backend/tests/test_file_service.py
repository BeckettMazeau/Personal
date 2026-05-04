import unittest
import asyncio
import os
from unittest.mock import patch, MagicMock
from app.services.file_service import scan_directory
from app.core.utils import batch_files
from app.models.schemas import FileObject, FileSource

class TestFileService(unittest.TestCase):

    @patch("app.services.file_service.os.walk")
    @patch("app.services.file_service.os.stat")
    def test_scan_directory(self, mock_stat, mock_walk):
        # Setup mock directory structure
        mock_walk.return_value = [
            ("/test_dir", ("subdir",), ("test.exe", "document.pdf", "temp.tmp")),
        ]

        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1048576 # 1MB
        mock_stat_result.st_ctime = 1600000000.0
        mock_stat.return_value = mock_stat_result

        # Run async function
        files = asyncio.run(scan_directory("/test_dir"))

        self.assertEqual(len(files), 3)

        exe_file = next(f for f in files if f.filename == "test.exe")
        self.assertEqual(exe_file.confidence_score, 3)
        self.assertEqual(exe_file.source, FileSource.static)
        self.assertTrue(exe_file.suggested_action)

        pdf_file = next(f for f in files if f.filename == "document.pdf")
        self.assertEqual(pdf_file.confidence_score, 1)
        self.assertEqual(pdf_file.source, FileSource.llm_shallow)
        self.assertFalse(pdf_file.suggested_action)

        tmp_file = next(f for f in files if f.filename == "temp.tmp")
        self.assertEqual(tmp_file.confidence_score, 3)
        self.assertEqual(tmp_file.source, FileSource.static)
        self.assertTrue(tmp_file.suggested_action)

    def test_batch_files(self):
        # Create dummy files
        files = [
            FileObject(
                path=f"/test/file{i}.txt",
                filename=f"file{i}.txt",
                extension=".txt",
                size_mb=1.0,
                created_at=100.0,
                confidence_score=1,
                source=FileSource.llm_shallow,
                suggested_action=False
            )
            for i in range(45)
        ]

        batches = batch_files(files, batch_size=20)

        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 20)
        self.assertEqual(len(batches[1]), 20)
        self.assertEqual(len(batches[2]), 5)


if __name__ == "__main__":
    unittest.main()
