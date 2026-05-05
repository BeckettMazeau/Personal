# KiCadImporter Architecture Document

This document outlines the strict input/output contracts and data structures required for the modular PyQt6 application interfacing with KiCad-CLI. All components must strictly adhere to these interfaces.

## 1. Data Structures

The following data structures define the core contracts between the system's phases. They must be implemented using Python `dataclasses` in a shared models module (e.g., `src/utils/models.py`).

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class KiCadProject:
    """Represents a validated KiCad project."""
    project_path: str       # Absolute path to the .kicad_pro file
    schematic_path: str     # Absolute path to the .kicad_sch file
    pcb_path: str           # Absolute path to the .kicad_pcb file
    version: str            # Detected KiCad version

@dataclass
class ExportOptions:
    """Configuration options for a KiCad-CLI export operation."""
    export_format: str      # e.g., 'pdf', 'svg', 'step', 'gerber'
    output_dir: str         # Absolute path to the destination directory
    layers: List[str]       # List of layers to include (applicable for certain formats)
    dpi: int                # Resolution for applicable formats
    theme: str              # Theme to use (e.g., 'user', 'kicad-default')

@dataclass
class OperationResult:
    """Standardized result object for all backend and processing operations."""
    success: bool           # True if the operation completed without errors
    output_files: List[str] # List of absolute paths to the generated files
    error_message: Optional[str] # Description of the error if success is False
    logs: str               # Raw stdout/stderr from the CLI process
```

## 2. Error Handling

All backend and cross-module errors must raise exceptions inherited from a common base defined in `src/backend/exceptions.py`.
- `KiCadImportError`: Base class.
- Specific errors like `FileCollisionError`, `KiCadCLINotFoundError`, `ArchiveExtractionError`, etc.

## 2. Phase Contracts

### Phase 1: Backend (KiCad-CLI Interfacing)
**Module:** `src/backend/`
**Responsibility:** Execute KiCad-CLI subprocesses and capture their output. No GUI or complex business logic should reside here.

**Contracts:**
- `discover_kicad_cli() -> str`: Returns the path to the KiCad-CLI executable. Raises an exception if not found.
- `execute_export(project: KiCadProject, options: ExportOptions) -> OperationResult`: Runs the CLI command, handles timeouts/crashes, and returns a standardized `OperationResult`.

### Phase 2: Processing (Data Transformation & Validation)
**Module:** `src/utils/`
**Responsibility:** Validate inputs, parse project files to discover schematic/PCB paths, and prepare the `ExportOptions` based on business logic.

**Contracts:**
- `parse_project(directory: str) -> KiCadProject`: Scans a directory, validates the presence of required KiCad files, and returns a populated `KiCadProject`.
- `validate_options(options: ExportOptions) -> bool`: Ensures the selected options are compatible with the requested export format.

### Phase 3: GUI (PyQt6 Interface)
**Module:** `src/gui/`
**Responsibility:** Present the interface to the user, gather input, and trigger Phase 2/1 logic. Must remain non-blocking (use `QThread` or `QRunnable` for backend calls).

**Contracts:**
- Must only interact with the Backend via the `ExportOptions` and `KiCadProject` data structures.
- Must consume `OperationResult` to display success/error dialogs and logs to the user.
