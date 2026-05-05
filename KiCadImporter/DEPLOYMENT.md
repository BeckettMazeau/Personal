# Deployment Guide

This document outlines the steps required to build the KiCad Import Tool into a standalone, redistributable executable and package it into an installer.

## Prerequisites

- **Python**: 3.9+ (Tested with Python 3.14.4 / PyInstaller 6.20.0)
- **PyQt6**: 6.11.0+ (Tested with 6.11.0)
- **OS**: Windows (for `.exe` build) or macOS (for `.app` build)
- **Installer Tool**: [Inno Setup 6+](https://jrsoftware.org/isinfo.php) (Windows only, for generating the setup executable)

> **Important**: Always launch the app via `run.py` at the project root — not `src/main.py` directly. The `run.py` script ensures the project root is on `sys.path` so that all `from src.X` imports resolve correctly.

## Environment Setup

Follow these exact steps to reproduce the build in a clean virtual environment.

1. **Create a Clean Virtual Environment**
   Open your terminal and run:
   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment**
   - **Windows:**
     ```cmd
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install Build Dependencies**
   Update `pip` and install the necessary dependencies from the `requirements.txt` file and build utilities:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install pyinstaller setuptools
   ```
   *Note: This will install `PyQt6>=6.6.0` as specified in the requirements.*

4. **Install the Application Package (Optional)**
   Install the current project in editable mode so the entry points and local packages are recognized correctly:
   ```bash
   pip install -e .
   ```

## Building the Standalone Executable

The `build.spec` file has been configured to bundle the application into a single executable (`--onefile`), hiding the console window (`--noconsole`), and explicitly including all non-python assets.

Run the following command:

```bash
pyinstaller build.spec --clean
```

Upon successful completion, the standalone executable will be located in the `dist/` directory:
- Windows: `dist/KiCadImporter_v1.0.exe`
- macOS: `dist/KiCadImporter_v1.0.app`

## Creating the Installer

### Windows (Inno Setup)

An `installer.iss` file is provided to generate a professional setup wizard that handles desktop shortcuts and `.zip` file associations.

1. Open `installer.iss` in the **Inno Setup Compiler**.
2. Click **Compile** to generate the installer.
3. The resulting setup executable will be generated in an `Output/` directory within the project folder.

### macOS (DMG Packaging)

For macOS, you can use `create-dmg` to bundle the generated `.app` file into a distributable DMG image:

```bash
create-dmg \
  --volname "KiCad Import Tool Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "KiCadImporter_v1.0.app" 200 190 \
  --hide-extension "KiCadImporter_v1.0.app" \
  --app-drop-link 400 190 \
  "KiCadImporter_v1.0.dmg" \
  "dist/"
```

## Continuous Integration Notes

This process can be easily automated using CI pipelines (e.g., GitHub Actions). Ensure the pipeline replicates the virtual environment setup, installs the requirements, builds with `pyinstaller build.spec`, and finally packages the artifact using Inno Setup (Windows) or `create-dmg` (macOS).
