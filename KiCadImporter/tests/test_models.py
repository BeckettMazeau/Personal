import pytest
from unittest.mock import patch, mock_open
from src.backend.models import ImportTask, validate_paths, ImportStatus

def test_import_task_initialization():
    task = ImportTask(
        original_zip_path="test.zip",
        extracted_part_name="TestPart"
    )
    assert task.status == ImportStatus.PENDING
    assert task.collision_detected is False

@patch('src.backend.models.pathlib.Path.is_file')
@patch('builtins.open', new_callable=mock_open, read_data='(symbol "TestPart" (pin ...))')
def test_validate_paths_symbol_collision(mock_file, mock_is_file):
    mock_is_file.return_value = True
    
    task = ImportTask(
        original_zip_path="test.zip",
        extracted_part_name="TestPart",
        target_symbol_lib="/tmp/lib.kicad_sym"
    )
    
    collision = validate_paths(task)
    assert collision is True
    assert task.collision_detected is True
    assert task.status == ImportStatus.COLLISION

@patch('src.backend.models.pathlib.Path.is_file')
@patch('builtins.open', new_callable=mock_open, read_data='(symbol "OtherPart" (pin ...))')
def test_validate_paths_no_symbol_collision(mock_file, mock_is_file):
    mock_is_file.return_value = True
    
    task = ImportTask(
        original_zip_path="test.zip",
        extracted_part_name="TestPart",
        target_symbol_lib="/tmp/lib.kicad_sym"
    )
    
    collision = validate_paths(task)
    assert collision is False
    assert task.collision_detected is False
    assert task.status == ImportStatus.PENDING

@patch('src.backend.models.pathlib.Path.is_dir')
@patch('src.backend.models.pathlib.Path.exists')
def test_validate_paths_footprint_collision(mock_exists, mock_is_dir):
    mock_is_dir.return_value = True
    mock_exists.return_value = True
    
    task = ImportTask(
        original_zip_path="test.zip",
        extracted_part_name="TestPart",
        target_footprint_lib="/tmp/lib.pretty"
    )
    
    collision = validate_paths(task)
    assert collision is True
    assert task.collision_detected is True
    assert task.status == ImportStatus.COLLISION

def test_validate_paths_no_targets():
    task = ImportTask(
        original_zip_path="test.zip",
        extracted_part_name="TestPart"
    )
    collision = validate_paths(task)
    assert collision is False
