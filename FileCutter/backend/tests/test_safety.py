import pytest
import os
import tempfile
from unittest.mock import patch
from app.core.safety import SecureDeletionManager

def test_secure_deletion_manager_valid_token():
    manager = SecureDeletionManager(server_secret="secret123")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("test")

        with patch('send2trash.send2trash') as mock_send2trash:
            failed = manager.delete_files([file_path], confirmation_token="secret123")
            assert len(failed) == 0
            mock_send2trash.assert_called_once_with(file_path)

def test_secure_deletion_manager_invalid_token():
    manager = SecureDeletionManager(server_secret="secret123")

    with pytest.raises(PermissionError):
        manager.delete_files(["/tmp/test.txt"], confirmation_token="wrong_token")

def test_secure_deletion_manager_failure():
    manager = SecureDeletionManager(server_secret="secret123")

    with patch('send2trash.send2trash', side_effect=Exception("Failed")):
        failed = manager.delete_files(["/tmp/test.txt"], confirmation_token="secret123")
        assert len(failed) == 1
        assert failed[0] == "/tmp/test.txt"
