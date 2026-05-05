import pytest
from unittest.mock import patch
from src.backend.name_parser import suggest_part_name

def test_suggest_part_name_empty():
    assert suggest_part_name([]) == "Unknown_Part"

def test_suggest_part_name_single_file():
    files = ["Mouser_LM358_v1.kicad_sym"]
    assert suggest_part_name(files) == "LM358"

def test_suggest_part_name_multiple_files_common_denominator():
    files = [
        "Mouser_LM358_v1.kicad_sym",
        "DigiKey_LM358.kicad_mod",
        "LM358_3dmodel.step"
    ]
    # "LM358" is common to all
    assert suggest_part_name(files) == "LM358"

def test_suggest_part_name_complex_names():
    files = [
        "TexasInstruments_SN74HC595N.kicad_sym",
        "SN74HC595N_footprint.kicad_mod"
    ]
    assert "SN74HC595N" in suggest_part_name(files)

@patch('src.backend.name_parser.os.path.getsize')
@patch('src.backend.name_parser.os.path.exists')
def test_suggest_part_name_no_common_substring(mock_exists, mock_getsize):
    # Mock os.path.getsize to force fallback behavior
    mock_exists.return_value = True
    mock_getsize.side_effect = [100, 200, 50]
    
    files = [
        "A.kicad_sym",
        "B.kicad_mod",
        "C.step"
    ]
    # File B is the largest, so it should fallback to 'B'
    assert suggest_part_name(files) == "B"

def test_suggest_part_name_normalization():
    files = ["My---Messy___Part  Name.kicad_sym"]
    assert suggest_part_name(files) == "My-Messy-Part-Name"
