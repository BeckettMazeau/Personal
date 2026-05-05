import sys
import os
from setuptools import setup, find_packages

is_windows = sys.platform.startswith('win')
is_mac = sys.platform == 'darwin'

setup(
    name="KiCadImporter",
    version="1.0.0",
    description="Standalone executable for the KiCad Import Tool",
    author="Beckett Mazeau",
    packages=find_packages(include=["src", "src.*"]),
    install_requires=[
        "PyQt6>=6.6.0",
        "pyinstaller>=6.0.0"
    ],
    entry_points={
        "console_scripts": [
            "kicad-importer=src.main:main",
        ]
    },
    package_data={
        # Ensure non-Python assets are included if distributed via source
        "": ["*.svg", "*.png", "*.ico", "*.icns", "*.json"],
    },
)
