import send2trash
import secrets
import logging
from typing import List

logger = logging.getLogger(__name__)

class SecureDeletionManager:
    """
    Service responsible for safely deleting files.

    CRITICAL: This service must strictly use the `send2trash` library for all
    deletion operations. The use of `os.remove`, `os.unlink`, or `shutil.rmtree`
    is expressly PROHIBITED to ensure safety and allow user recovery of files.
    """

    def __init__(self, server_secret: str):
        """
        Initializes the SecureDeletionManager with a server-side secret
        used to validate confirmation tokens.
        """
        self.server_secret = server_secret

    def delete_files(self, file_paths: List[str], confirmation_token: str) -> List[str]:
        """
        Safely deletes a list of files by sending them to the operating system's trash/recycle bin.
        Requires a valid confirmation token to proceed.

        Args:
            file_paths (List[str]): A list of absolute paths to the files to be deleted.
            confirmation_token (str): A token that must match the server secret to authorize deletion.

        Returns:
            List[str]: A list of file paths that failed to be deleted.
        """
        if not secrets.compare_digest(confirmation_token, self.server_secret):
            raise PermissionError("Invalid confirmation token. Deletion aborted.")

        failed_deletions = []
        for file_path in file_paths:
            try:
                # Strictly using send2trash for safety
                logger.info(f"Sending file to trash: {file_path}")
                send2trash.send2trash(file_path)
            except Exception as e:
                logger.error(f"Failed to send file to trash: {file_path}. Error: {e}")
                failed_deletions.append(file_path)

        return failed_deletions
