import logging
import os
from pathlib import Path
from typing import List, Optional

import send2trash

from app.core.config import settings
from app.core.nonces import NonceStore
from app.core.paths import safe_resolve

logger = logging.getLogger(__name__)


class SecureDeletionManager:
    """
    Service responsible for safely deleting files.

    CRITICAL: This service must strictly use the `send2trash` library for all
    deletion operations. The use of `os.remove`, `os.unlink`, or `shutil.rmtree`
    is expressly PROHIBITED to ensure safety and allow user recovery of files.
    """

    def __init__(self, allowed_root: Optional[Path] = None):
        self.allowed_root = Path(allowed_root) if allowed_root else Path(settings.downloads_path)

    def delete_files(self, file_paths: List[str], nonce: str, nonce_store: NonceStore):
        """
        Safely delete files by sending them to the OS trash.

        Authorization: a one-time `nonce` previously issued by `nonce_store`
        and bound to the exact set of `file_paths` must be presented. The
        nonce is consumed on use. Each path is then re-resolved and verified
        to live inside `self.allowed_root` before deletion.
        """
        if not nonce_store.consume(nonce, file_paths):
            raise ValueError(
                "Invalid, expired, reused, or path-mismatched deletion nonce."
            )

        resolved_paths: List[Path] = []
        for raw_path in file_paths:
            try:
                resolved = safe_resolve(raw_path, self.allowed_root)
            except ValueError as e:
                raise ValueError(f"Refusing to delete {raw_path!r}: {e}") from e
            resolved_paths.append(resolved)

        deleted_count = 0
        for resolved in resolved_paths:
            path_str = str(resolved)
            if not os.path.exists(path_str):
                logger.warning(f"File not found, skipping: {path_str}")
                continue
            if not os.path.isfile(path_str):
                logger.warning(f"Path is not a file, skipping: {path_str}")
                continue

            logger.info(f"Sending file to trash: {path_str}")
            try:
                send2trash.send2trash(path_str)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to send {path_str} to trash: {e}")

        return {"status": "success", "deleted_count": deleted_count}
