"""
Root-level entry point for the KiCad Import Tool.
Run with: python run.py
This ensures the project root is on sys.path so that
'from src.backend...' and 'from src.gui...' imports resolve correctly.
"""
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
