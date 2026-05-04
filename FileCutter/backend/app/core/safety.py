import os
import send2trash
import logging
from typing import List

logger = logging.getLogger(__name__)

# Load secret from environment variables
SERVER_SIDE_SECRET = os.getenv("CONFIRMATION_TOKEN_SECRET", "super_secret_confirmation_token_123")

class SecureDeletionManager:
    """
    Service responsible for safely deleting files.

    CRITICAL: This service must strictly use the `send2trash` library for all
    deletion operations. The use of `os.remove`, `os.unlink`, or `shutil.rmtree`
    is expressly PROHIBITED to ensure safety and allow user recovery of files.
    """

    def __init__(self):
        pass

    def delete_files(self, file_paths: List[str], confirmation_token: str):
        """
        Safely deletes multiple files by sending them to the operating system's trash/recycle bin.

        Args:
            file_paths (List[str]): The absolute paths to the files to be deleted.
            confirmation_token (str): Token to authorize the deletion.
        """
        if confirmation_token != SERVER_SIDE_SECRET:
            raise ValueError("Invalid confirmation token. Deletion aborted.")

        deleted_count = 0
        for file_path in file_paths:
            # Explicit validation: ensure it's a file that exists
            if not os.path.exists(file_path):
                logger.warning(f"File not found, skipping: {file_path}")
                continue
            if not os.path.isfile(file_path):
                 logger.warning(f"Path is not a file, skipping: {file_path}")
                 continue

            logger.info(f"Sending file to trash: {file_path}")
            try:
                send2trash.send2trash(file_path)
                deleted_count += 1
            except Exception as e:
                 logger.error(f"Failed to send {file_path} to trash: {e}")

        return {"status": "success", "deleted_count": deleted_count}
