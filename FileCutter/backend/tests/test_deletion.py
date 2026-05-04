import unittest
import os
from unittest.mock import patch, MagicMock
from app.core.safety import SecureDeletionManager
from app.core.config import settings


class TestSecureDeletionManager(unittest.TestCase):
    @patch("app.core.safety.send2trash.send2trash")
    @patch("app.core.safety.os.path.exists")
    @patch("app.core.safety.os.path.isfile")
    def test_delete_files_success(self, mock_isfile, mock_exists, mock_send2trash):
        manager = SecureDeletionManager()
        test_paths = ["/path/to/test/file1.txt", "/path/to/test/file2.txt"]

        mock_exists.return_value = True
        mock_isfile.return_value = True

        result = manager.delete_files(test_paths, settings.confirmation_token_secret)

        self.assertEqual(result["deleted_count"], 2)
        mock_send2trash.assert_any_call(test_paths[0])
        mock_send2trash.assert_any_call(test_paths[1])
        self.assertEqual(mock_send2trash.call_count, 2)

    def test_delete_files_invalid_token(self):
        manager = SecureDeletionManager()
        test_paths = ["/path/to/test/file1.txt"]

        with self.assertRaisesRegex(ValueError, "Invalid confirmation token"):
            manager.delete_files(test_paths, "wrong_token")

    @patch("app.core.safety.send2trash.send2trash")
    @patch("app.core.safety.os.path.exists")
    @patch("app.core.safety.os.path.isfile")
    def test_delete_files_skips_non_existent(self, mock_isfile, mock_exists, mock_send2trash):
         manager = SecureDeletionManager()
         test_paths = ["/path/to/test/exists.txt", "/path/to/test/missing.txt"]

         # The first exists, the second does not
         mock_exists.side_effect = [True, False]
         mock_isfile.side_effect = [True] # Only called for the existing one

         result = manager.delete_files(test_paths, settings.confirmation_token_secret)

         self.assertEqual(result["deleted_count"], 1)
         mock_send2trash.assert_called_once_with(test_paths[0])


if __name__ == "__main__":
    unittest.main()
