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
    
    Multiple workspaces are maintained simultaneously so that previously
    extracted archives remain accessible for preview rendering.
    """

    def __init__(self) -> None:
        self._workspaces: List[tempfile.TemporaryDirectory] = []
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
        
        Previous workspaces are preserved so that their files (SVG previews,
        source KiCad files) remain accessible for the UI.
        
        Args:
            archive_path: Path to the .zip file.
            
        Returns:
            The absolute path to the temporary directory.
        """
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="kicad_workspace_")
        self._workspaces.append(temp_dir_obj)
        self.workspace_path = pathlib.Path(temp_dir_obj.name).resolve()
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(self.workspace_path)
            
        return str(self.workspace_path)

    def cleanup(self):
        """Explicitly cleans up all temporary workspaces."""
        for ws in self._workspaces:
            try:
                ws.cleanup()
            except Exception:
                pass
        self._workspaces.clear()
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

    def copy_to_target(self, source_path: pathlib.Path | str, target: pathlib.Path | str) -> pathlib.Path:
        """
        Copies a file from the workspace to a target location with collision detection.
        
        The target parameter is interpreted intelligently:
        - If target is an existing file or has a KiCad file extension (.kicad_sym, .kicad_mod),
          the source file is copied into the target's *parent* directory.
        - Otherwise target is treated as a directory path.
        
        Args:
            source_path: Absolute path to the source file (usually in the workspace).
            target: Absolute path to the destination file or directory.
            
        Returns:
            The absolute pathlib.Path to the copied file.
            
        Raises:
            FileCollisionError: If a file with the same name already exists in target_dir.
            FileNotFoundError: If the source_path does not exist.
        """
        src = pathlib.Path(source_path)
        target_path = pathlib.Path(target)
        
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Determine if the target is a file path or a directory path.
        # If the target already exists as a file, or has a known KiCad file extension,
        # treat it as a file path and use its parent as the destination directory.
        kicad_file_extensions = {'.kicad_sym', '.kicad_mod'}
        if target_path.is_file() or target_path.suffix.lower() in kicad_file_extensions:
            dst_dir = target_path.parent
        else:
            dst_dir = target_path
            
        # Ensure target directory exists
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        dst_path = dst_dir / src.name
        
        # Collision check
        if dst_path.exists():
            raise FileCollisionError(f"Collision detected: File '{src.name}' already exists in '{dst_dir}'")
            
        # Perform the copy
        shutil.copy2(src, dst_path)
        
        return dst_path.resolve()
