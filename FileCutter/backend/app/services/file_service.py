import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List

from app.models.file_model import FileObject, SourceEnum

INSTALLER_EXTENSIONS = {".exe", ".msi", ".dmg", ".pkg"}
TEMP_EXTENSIONS = {".tmp", ".temp", ".bak", ".swp"}


class FileService:
    def __init__(self):
        self.static_extensions = INSTALLER_EXTENSIONS.union(TEMP_EXTENSIONS)

    async def scan_directory(self, directory_path: str) -> List[FileObject]:
        """
        Asynchronously scans a directory and its subdirectories to extract file metadata
        and perform static triaging for installers and temporary files.
        """
        results: List[FileObject] = []
        path = Path(directory_path)

        if not path.exists() or not path.is_dir():
            raise ValueError(f"The path {directory_path} is not a valid directory.")

        for root, _, files in os.walk(directory_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                # Yield control to the event loop to ensure non-blocking behavior
                await asyncio.sleep(0)

                try:
                    stat = os.stat(file_path)
                    size_mb = stat.st_size / (1024 * 1024)
                    created_at = datetime.fromtimestamp(stat.st_ctime)
                    _, extension = os.path.splitext(file_name)
                    extension = extension.lower()

                    file_obj = FileObject(
                        path=file_path,
                        filename=file_name,
                        extension=extension,
                        size_mb=size_mb,
                        created_at=created_at,
                    )

                    # Static Triaging
                    if extension in self.static_extensions:
                        file_obj.confidence_score = 3
                        file_obj.suggested_action = True
                        file_obj.source = SourceEnum.STATIC

                    results.append(file_obj)
                except OSError:
                    # Skip files that can't be accessed
                    continue

        return results
