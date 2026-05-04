import os
import asyncio
from typing import List, Tuple
from app.models.file_model import FileObject, FileSource

STATIC_EXTENSIONS = {'.exe', '.msi', '.dmg', '.pkg', '.tmp'}

async def scan_directory(directory: str) -> List[FileObject]:
    """Asynchronously scans a directory and applies static triaging."""
    def _scan() -> List[FileObject]:
        files_found = []
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    _, ext = os.path.splitext(file)
                    ext_lower = ext.lower()

                    is_static = ext_lower in STATIC_EXTENSIONS

                    file_obj = FileObject(
                        path=file_path,
                        filename=file,
                        extension=ext_lower,
                        size_mb=stat.st_size / (1024 * 1024),
                        created_at=stat.st_ctime,
                        confidence_score=3 if is_static else 1,
                        source=FileSource.static if is_static else FileSource.llm_shallow, # default to shallow, to be processed
                        suggested_action=True if is_static else False
                    )
                    files_found.append(file_obj)
                except OSError as e:
                    print(f"Error accessing {file_path}: {e}")
                    # Could log this instead
        return files_found

    return await asyncio.to_thread(_scan)

def batch_files(files: List[FileObject], batch_size: int = 20) -> List[List[FileObject]]:
    """Chunks a list of files into batches of a specified size."""
    return [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
