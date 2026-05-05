import os
import shutil
import tempfile
import zipfile
import pathlib
from typing import Dict, List, Optional
from src.backend.exceptions import FileCollisionError


class ArchiveWorkspaceManager:
    """
    Manages temporary workspaces for extracting and processing KiCad archives.
    
    This class ensures that extracted files are kept in a sandboxed temporary 
    directory which is automatically cleaned up.
    """

    def __init__(self) -> None:
        self._temp_dir_obj: Optional[tempfile.TemporaryDirectory] = None
        self.workspace_path: Optional[pathlib.Path] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        self.cleanup()

    def extract_archive(self, archive_path: str) -> str:
        """
        Extracts a .zip archive into a new temporary directory.
        
        Args:
            archive_path: Path to the .zip file.
            
        Returns:
            The absolute path to the temporary directory.
        """
        # Ensure previous workspace is cleaned up if this is called multiple times
        self.cleanup()
        
        self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="kicad_workspace_")
        self.workspace_path = pathlib.Path(self._temp_dir_obj.name).resolve()
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(self.workspace_path)
            
        return str(self.workspace_path)

    def cleanup(self):
        """Explicitly cleans up the temporary workspace."""
        if self._temp_dir_obj:
            self._temp_dir_obj.cleanup()
            self._temp_dir_obj = None
            self.workspace_path = None

    def identify_files(self) -> Dict[str, List[pathlib.Path]]:
        """
        Parses the workspace and identifies KiCad symbol and footprint files.
        
        Returns:
            A dictionary mapping extension to a list of pathlib.Path objects.
        """
        if not self.workspace_path:
            return {".kicad_sym": [], ".kicad_mod": []}
            
        results = {
            ".kicad_sym": [],
            ".kicad_mod": []
        }
        
        # Walk the directory to find files with matching extensions
        for path in self.workspace_path.rglob("*"):
            if path.is_file():
                ext = path.suffix.lower()
                if ext in results:
                    results[ext].append(path.resolve())
                    
        return results

    def copy_to_target(self, source_path: pathlib.Path | str, target_dir: pathlib.Path | str) -> pathlib.Path:
        """
        Copies a file from the workspace to a target directory with collision detection.
        
        Args:
            source_path: Absolute path to the source file (usually in the workspace).
            target_dir: Absolute path to the destination directory.
            
        Returns:
            The absolute pathlib.Path to the copied file.
            
        Raises:
            FileCollisionError: If a file with the same name already exists in target_dir.
            FileNotFoundError: If the source_path does not exist.
        """
        src = pathlib.Path(source_path)
        dst_dir = pathlib.Path(target_dir)
        
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
            
        # Ensure target directory exists
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        dst_path = dst_dir / src.name
        
        # Collision check
        if dst_path.exists():
            raise FileCollisionError(f"Collision detected: File '{src.name}' already exists in '{target_dir}'")
            
        # Perform the copy
        shutil.copy2(src, dst_path)
        
        return dst_path.resolve()
