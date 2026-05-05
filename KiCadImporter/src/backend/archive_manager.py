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

        # Special handling for merging .kicad_sym files
        if src.suffix.lower() == '.kicad_sym' and target_path.suffix.lower() == '.kicad_sym':
            # Target is a specific .kicad_sym file (library)
            if not target_path.exists():
                # If target library doesn't exist, just copy the file over as the new library
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target_path)
                return target_path.resolve()
            
            # Merge into existing library
            src_text = src.read_text(encoding='utf-8')
            tgt_text = target_path.read_text(encoding='utf-8')
            
            start_idx = src_text.find("(symbol ")
            if start_idx == -1:
                raise ValueError(f"No symbol found in source file: {src.name}")
                
            end_idx = src_text.rfind(")")
            if end_idx == -1 or end_idx < start_idx:
                raise ValueError(f"Invalid source symbol file format: {src.name}")
                
            symbols_content = src_text[start_idx:end_idx].strip()
            
            import re
            symbol_names = re.findall(r'\(symbol\s+"([^"]+)"', symbols_content)
            for sym_name in symbol_names:
                if f'(symbol "{sym_name}"' in tgt_text:
                    raise FileCollisionError(f"Collision detected: Symbol '{sym_name}' already exists in library '{target_path.name}'")
                    
            tgt_end_idx = tgt_text.rfind(")")
            if tgt_end_idx == -1:
                raise ValueError(f"Invalid target symbol library format: {target_path.name}")
                
            new_tgt_text = tgt_text[:tgt_end_idx] + "\n  " + symbols_content + "\n" + tgt_text[tgt_end_idx:]
            target_path.write_text(new_tgt_text, encoding='utf-8')
            return target_path.resolve()

        # Determine if the target is a file path or a directory path.
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
