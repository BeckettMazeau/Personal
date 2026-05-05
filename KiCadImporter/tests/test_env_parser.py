import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.backend.env_parser import KiCadEnvParser, LibraryEntry

@pytest.fixture
def parser():
    with patch('src.backend.env_parser.KiCadEnvParser._initialize'):
        p = KiCadEnvParser()
        p.env_vars = {}
        p.config_path = None
        return p

def test_expand_path_vars_simple(parser):
    parser.env_vars = {"KICAD8_SYMBOL_DIR": "/kicad/symbols"}
    path = "${KICAD8_SYMBOL_DIR}/Test.kicad_sym"
    expanded = parser.expand_path_vars(path)
    assert "/kicad/symbols/Test.kicad_sym" in expanded.replace('\\', '/')

def test_expand_path_vars_round_brackets(parser):
    parser.env_vars = {"KICAD8_FOOTPRINT_DIR": "/kicad/fps"}
    path = "$(KICAD8_FOOTPRINT_DIR)/Test.pretty"
    expanded = parser.expand_path_vars(path)
    assert "/kicad/fps/Test.pretty" in expanded.replace('\\', '/')

def test_expand_path_vars_missing_var(parser):
    parser.env_vars = {}
    path = "${MISSING_VAR}/Test.kicad_sym"
    expanded = parser.expand_path_vars(path)
    assert "${MISSING_VAR}/Test.kicad_sym" in expanded.replace('\\', '/')

@patch('src.backend.env_parser.pathlib.Path.exists')
@patch('builtins.open', new_callable=MagicMock)
def test_parse_lib_table_success(mock_open, mock_exists, parser):
    parser.config_path = Path("/config")
    mock_exists.return_value = True
    
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.read.return_value = '''
(sym_lib_table
  (lib (name "TestLib") (type "KiCad") (uri "${KICAD8_SYMBOL_DIR}/TestLib.kicad_sym") (options "") (descr ""))
  (lib (name "AnotherLib") (type "KiCad") (uri "/absolute/path/AnotherLib.kicad_sym") (options "") (descr ""))
)
'''
    
    parser.env_vars = {"KICAD8_SYMBOL_DIR": "/kicad/symbols"}
    
    entries = parser.parse_lib_table("sym-lib-table")
    assert len(entries) == 2
    assert entries[0].nickname == "TestLib"
    assert "TestLib.kicad_sym" in entries[0].path
    assert entries[1].nickname == "AnotherLib"

@patch('src.backend.env_parser.pathlib.Path.exists')
def test_parse_lib_table_no_config(mock_exists, parser):
    parser.config_path = None
    assert parser.parse_lib_table("sym-lib-table") == []

@patch('src.backend.env_parser.pathlib.Path.exists')
def test_parse_lib_table_file_missing(mock_exists, parser):
    parser.config_path = Path("/config")
    mock_exists.return_value = False
    assert parser.parse_lib_table("sym-lib-table") == []
