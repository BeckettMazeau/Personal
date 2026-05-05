from dataclasses import dataclass
from enum import Enum
import re
import pathlib
from typing import Optional

class ImportStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    COLLISION = "Collision"

@dataclass
class ImportTask:
    """
    Represents a single part import operation.
    """
    original_zip_path: str
    extracted_part_name: str
    symbol_source_path: Optional[str] = None
    footprint_source_path: Optional[str] = None
    target_symbol_lib: Optional[str] = None      # Path to .kicad_sym file
    target_footprint_lib: Optional[str] = None   # Path to .pretty directory
    status: ImportStatus = ImportStatus.PENDING
    collision_detected: bool = False
    error_message: Optional[str] = None

def validate_paths(task: ImportTask) -> bool:
    """
    Validates if the proposed part name already exists in the target libraries.
    
    For Symbols: Checks if extracted_part_name exists as a (symbol "NAME"...) entry
    inside the target_symbol_lib (.kicad_sym file).
    
    For Footprints: Checks if [extracted_part_name].kicad_mod exists inside
    the target_footprint_lib (.pretty directory).
    
    Returns:
        bool: True if a collision is detected, False otherwise.
    """
    collision = False
    
    # 1. Check Symbol Collision
    if task.target_symbol_lib:
        symbol_lib_path = pathlib.Path(task.target_symbol_lib)
        if symbol_lib_path.is_file():
            try:
                with open(symbol_lib_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # KiCad v6+ S-expression format for symbols: (symbol "NAME" ...
                    # We use a regex to find the symbol definition while being careful about quotes
                    pattern = rf'\(symbol\s+"{re.escape(task.extracted_part_name)}"'
                    if re.search(pattern, content):
                        collision = True
            except Exception as e:
                # If we can't read the library, we don't assume collision but could flag error
                task.error_message = f"Symbol library access error: {str(e)}"

    # 2. Check Footprint Collision
    if task.target_footprint_lib:
        footprint_lib_path = pathlib.Path(task.target_footprint_lib)
        if footprint_lib_path.is_dir():
            # KiCad footprints are stored as [NAME].kicad_mod inside .pretty folders
            footprint_filename = f"{task.extracted_part_name}.kicad_mod"
            footprint_path = footprint_lib_path / footprint_filename
            if footprint_path.exists():
                collision = True

    # Update task state
    task.collision_detected = collision
    if collision:
        task.status = ImportStatus.COLLISION
    
    return collision
