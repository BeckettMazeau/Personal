import send2trash
import logging

logger = logging.getLogger(__name__)


class SecureDeletionManager:
    """
    Service responsible for safely deleting files.

    CRITICAL: This service must strictly use the `send2trash` library for all
    deletion operations. The use of `os.remove`, `os.unlink`, or `shutil.rmtree`
    is expressly PROHIBITED to ensure safety and allow user recovery of files.
    """

    def __init__(self):
        pass

    def delete_file(self, file_path: str):
        """
        Safely deletes a file by sending it to the operating system's trash/recycle bin.

        Args:
            file_path (str): The absolute path to the file to be deleted.
        """
        logger.info(f"Sending file to trash: {file_path}")
        send2trash.send2trash(file_path)
