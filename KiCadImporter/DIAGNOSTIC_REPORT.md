# KiCad Component Importer - Diagnostic Report

## Executive Summary
A multimodal analysis of the application codebase against the reported visual symptoms has revealed severe architectural disconnects between the PyQt6 frontend and the backend logic. The application suffers from incomplete UI bindings, non-thread-safe resource management, incorrect path handling for KiCad files, and silent failures in the execution pipeline.

## Symptom Mapping & Root Cause Analysis

### 1. Unresponsive Interface (Settings Menu)
**Visual Symptom:** Clicking "Settings" does nothing but show a status message.
**Code Failure:** In `src/gui/main_window.py` (Line 51), the `settings_action.triggered` signal is bound to a lambda placeholder `lambda: self.show_message("Settings clicked")` rather than instantiating and executing `SettingsDialog` from `src/gui/settings_dialog.py`. 

### 2. Absent Data Binding
**Visual Symptom:** Dropping a `.zip` file leaves the main UI completely blank (black screen).
**Code Failure:** In `src/gui/main_window.py` (Lines 158-183), the `set_queue_widget` and `set_preview_widget` methods use `self.splitter.replaceWidget(idx, widget)`. While this replaces the placeholder in the layout, newly instantiated `QWidget` objects default to `isVisible() == False`. The application never calls `widget.show()`, leaving the UI structurally present but visually hidden.

### 3. Missing Configuration
**Visual Symptom:** No input fields exist to configure target libraries for a specific imported part.
**Code Failure:** The `ImportTask` data model supports `target_symbol_lib` and `target_footprint_lib`. However, `src/gui/queue_widget.py` and `src/gui/preview_widget.py` contain no input mechanisms (e.g., `QLineEdit` or `LibraryBrowser` instances). The `Controller` silently falls back to global defaults in `config.get()`, leaving the user with no per-task configuration options.

### 4. Absent Previews
**Visual Symptom:** SVG previews fail to render.
**Code Failure:** The `ArchiveWorkspaceManager` is instantiated once in `Controller` and shared across all tasks. When `ProcessingWorker.run()` calls `self.workspace_mgr.extract_archive()`, it immediately invokes `self.cleanup()`. If a user queues multiple `.zip` files, the temporary workspace containing the SVGs and `.kicad_sym` files for the previous tasks is immediately deleted from disk. `PreviewWidget` then fails to load the deleted SVG paths.

### 5. Ineffective Collision Detection
**Visual Symptom:** Overwriting a library triggers no warnings.
**Code Failure:** While `models.py:validate_paths` correctly identifies collisions and sets `task.status = ImportStatus.COLLISION`, `ExecutionWorker.run` completely ignores this status. It blindly calls `self.workspace_mgr.copy_to_target()`. The backend catches the resulting `FileCollisionError` and appends it to an error list, skipping any interactive user confirmation or pre-execution warning.

### 6. Ambiguous Success State
**Visual Symptom:** A generic "Successfully imported 1 parts!" dialogue appears even when files aren't saved.
**Code Failure:** In `ExecutionWorker.run` (Lines 120-128), if `task.target_symbol_lib` is `None` (which happens if the user hasn't configured global defaults in the missing Settings menu), the `if task.symbol_source_path and task.target_symbol_lib:` condition evaluates to `False`. The copy operation is skipped, no error is thrown, and `success_count += 1` executes unconditionally.

### 7. Brittle Archive Handling
**Visual Symptom:** File operations fail for KiCad libraries.
**Code Failure:** In `ArchiveWorkspaceManager.copy_to_target` (Lines 104-107), the code attempts to ensure the destination directory exists via `dst_dir.mkdir(parents=True, exist_ok=True)` where `dst_dir` is `pathlib.Path(target_dir)`. For KiCad symbols, `target_dir` is actually a `.kicad_sym` *file*. The code incorrectly creates a directory with the `.kicad_sym` extension and attempts to copy the source file inside it, resulting in a `FileExistsError` or corrupted library structure.
