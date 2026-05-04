from typing import List
from app.models.schemas import FileObject

def batch_files(files: List[FileObject], batch_size: int = 20) -> List[List[FileObject]]:
    """Chunks a list of files into batches of a specified size."""
    return [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
