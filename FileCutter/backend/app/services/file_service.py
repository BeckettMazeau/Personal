import asyncio
import logging
import os
from pathlib import Path
from typing import List
from app.models.schemas import FileObject, FileSource
from app.core.utils import get_downloads_directory

logger = logging.getLogger(__name__)

STATIC_EXTENSIONS = {'.exe', '.msi', '.dmg', '.pkg', '.tmp'}

async def scan_directory(directory: str = None) -> List[FileObject]:
    """Asynchronously scans a directory and applies static triaging.

    Args:
        directory (str): The root directory to scan.

    Returns:
        List[FileObject]: A list of triaged FileObject instances.
    """
    def _scan() -> List[FileObject]:
        files_found = []
        target_dir = Path(directory) if directory else get_downloads_directory()

        if not target_dir.exists() or not target_dir.is_dir():
            logger.error(f"Directory not found or invalid: {target_dir}")
            return []

        # We use os.walk to handle unreadable directories gracefully
        # Then convert yielded values to Path objects to use pathlib API
        for root, dirs, files in os.walk(str(target_dir)):
            root_path = Path(root)
            for file in files:
                item = root_path / file
                try:
                    stat = item.stat()
                    ext_lower = item.suffix.lower()
                    is_static = ext_lower in STATIC_EXTENSIONS

                    file_obj = FileObject(
                        path=str(item),
                        filename=item.name,
                        extension=ext_lower,
                        size_mb=stat.st_size / (1024 * 1024),
                        created_at=stat.st_ctime,
                        confidence_score=3 if is_static else 1,
                        source=FileSource.static if is_static else FileSource.llm_shallow,
                        suggested_action=True if is_static else False
                    )
                    files_found.append(file_obj)
                except (OSError, PermissionError) as e:
                    logger.error(f"Error accessing file {item}: {e}")

        return files_found

    return await asyncio.to_thread(_scan)
