import unittest
from app.core.utils import get_optimal_batch_size, batch_files
from app.models.schemas import FileObject, FileSource
from unittest.mock import patch
import platform

class TestUtils(unittest.TestCase):
    def test_batch_files(self):
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
            for i in range(15)
        ]
        batches = batch_files(files, batch_size=6)
        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 6)
        self.assertEqual(len(batches[1]), 6)
        self.assertEqual(len(batches[2]), 3)

    @patch("app.core.utils.platform.system")
    @patch("app.core.utils.subprocess.run")
    def test_get_optimal_batch_size_linux_rtx5070(self, mock_run, mock_system):
        mock_system.return_value = "Linux"
        mock_run_result = unittest.mock.MagicMock()
        mock_run_result.stdout = "NVIDIA GeForce RTX 5070, 12288 MiB"
        mock_run.return_value = mock_run_result

        batch_size = get_optimal_batch_size()
        self.assertEqual(batch_size, 8)

if __name__ == "__main__":
    unittest.main()
