import unittest
from unittest.mock import patch, MagicMock
from app.core.safety import SecureDeletionManager


class TestSecureDeletionManager(unittest.TestCase):
    @patch("app.core.safety.send2trash.send2trash")
    @patch("requests.post")
    def test_delete_file_uses_send2trash(self, mock_requests_post, mock_send2trash):
        # Mocking an imaginary LM Studio API call if it were part of the deletion flow
        mock_response = MagicMock()
        mock_response.json.return_value = {"action": "delete", "confidence": 3}
        mock_requests_post.return_value = mock_response

        manager = SecureDeletionManager()
        test_path = "/path/to/test/file.txt"

        manager.delete_file(test_path)

        # Verify send2trash is called
        mock_send2trash.assert_called_once_with(test_path)


if __name__ == "__main__":
    unittest.main()
