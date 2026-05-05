import pytest
from src.backend.name_parser import suggest_part_name

def test_suggest_part_name_empty():
    assert suggest_part_name([]) == "Unknown_Part"

def test_suggest_part_name_single_file():
    files = ["Mouser_LM358_v1.kicad_sym"]
    assert suggest_part_name(files) == "LM358"

def test_suggest_part_name_zip_hint():
    # Zip name should be preferred over a timestamp-named symbol file
    zip_path = "ul_ESP32-S3-WROOM-1-N16R8.zip"
    files = [
        "2026-05-05_07-59-52.kicad_sym",
        "ESP32-S3-WROOM-1-N16R8.kicad_mod"
    ]
    assert suggest_part_name(files, zip_path) == "ESP32-S3-WROOM-1-N16R8"

def test_suggest_part_name_timestamp_avoidance():
    # Should avoid timestamp even without zip hint if another descriptive file exists
    files = [
        "2026-05-05_07-59-52.kicad_sym",
        "SN74HC595N.kicad_mod"
    ]
    assert suggest_part_name(files) == "SN74HC595N"

def test_suggest_part_name_normalization():
    files = ["My---Messy___Part  Name.kicad_sym"]
    assert suggest_part_name(files) == "My-Messy-Part-Name"

def test_suggest_part_name_vendor_prefixes():
    files = ["ul_LM358.kicad_sym"]
    assert suggest_part_name(files) == "LM358"
    
    files = ["snapeda_NE555.kicad_mod"]
    assert suggest_part_name(files) == "NE555"

