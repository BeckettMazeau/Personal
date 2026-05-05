# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Detect OS to apply appropriate branding
icon_path = None
if sys.platform.startswith('win'):
    icon_path = os.path.join('assets', 'icon.ico')
elif sys.platform == 'darwin':
    icon_path = os.path.join('assets', 'icon.icns')

# Non-python assets to include explicitly in the bundle.
# Only add assets dir if it exists (icon files, SVG templates, etc.)
added_files = []
if os.path.isdir('assets'):
    added_files.append(('assets', 'assets'))

# Ensure we import modules dynamically accessed or not easily picked up
hidden_imports = [
    'src',
    'src.backend',
    'src.backend.env_parser',
    'src.backend.config_manager',
    'src.backend.archive_manager',
    'src.backend.cli_wrapper',
    'src.backend.models',
    'src.backend.name_parser',
    'src.backend.exceptions',
    'src.gui',
    'src.gui.controller',
    'src.gui.main_window',
    'src.gui.library_browser',
    'src.gui.queue_widget',
    'src.gui.preview_widget',
    'src.gui.settings_dialog',
    'src.utils',
]

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KiCadImporter_v1.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed interface (--noconsole)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if icon_path and os.path.isfile(icon_path) else None,
)
