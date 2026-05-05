# Agent Work Boundaries

To prevent parallel merge conflicts and ensure modularity, subsequent agents are restricted to modifying only their designated files and directories. Cross-phase modifications are strictly prohibited unless authorized by the System Architect.

## Agent 1: Backend Developer
**Role:** Implement the KiCad-CLI subprocess execution logic and environment discovery.
**Permitted Files/Directories:**
- `src/backend/*` (e.g., `cli_runner.py`, `environment.py`)
- `tests/test_backend.py`

## Agent 2: Processing Developer
**Role:** Implement project parsing, validation logic, and define the shared data models.
**Permitted Files/Directories:**
- `src/utils/*` (e.g., `models.py`, `parser.py`, `validator.py`)
- `tests/test_utils.py`

## Agent 3: GUI Developer
**Role:** Implement the PyQt6 user interface and handle thread-safe execution of backend tasks.
**Permitted Files/Directories:**
- `src/gui/*` (e.g., `main_window.py`, `components/`, `workers.py`)
- `src/main.py` (Entry point initialization)
- `tests/test_gui.py`

## Shared Resources
If an agent requires modifications to `docs/ARCHITECTURE.md` or `requirements.txt`, they must halt and request approval/changes from the System Architect.
