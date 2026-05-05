import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from src.backend.config_manager import ConfigManager
from src.backend.exceptions import ConfigurationError

@pytest.fixture
def manager():
    with patch('src.backend.config_manager.Path.exists', return_value=False):
        return ConfigManager(config_path=Path('/tmp/mock_config.json'))

def test_initialization_defaults(manager):
    assert manager.get("last_used_symbol_lib_path") == ""
    assert manager.get("window_geometry") == {}

@patch('src.backend.config_manager.Path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='{"last_used_symbol_lib_path": "/some/path"}')
def test_load_success(mock_file, mock_exists):
    mock_exists.return_value = True
    mgr = ConfigManager(config_path=Path('/tmp/mock_config.json'))
    assert mgr.get("last_used_symbol_lib_path") == "/some/path"

@patch('src.backend.config_manager.Path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='invalid json')
@patch('src.backend.config_manager.ConfigManager._handle_corrupted_config')
def test_load_invalid_json(mock_handle_corrupt, mock_file, mock_exists):
    mock_exists.return_value = True
    mgr = ConfigManager(config_path=Path('/tmp/mock_config.json'))
    mock_handle_corrupt.assert_called_once()

@patch('src.backend.config_manager.Path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='["not", "a", "dict"]')
@patch('src.backend.config_manager.ConfigManager._handle_corrupted_config')
def test_load_not_a_dict(mock_handle_corrupt, mock_file, mock_exists):
    mock_exists.return_value = True
    mgr = ConfigManager(config_path=Path('/tmp/mock_config.json'))
    mock_handle_corrupt.assert_called_once()

def test_set_and_get(manager):
    manager.set("new_key", "new_value")
    assert manager.get("new_key") == "new_value"
    assert manager.get("non_existent", "default_val") == "default_val"

@patch('src.backend.config_manager.Path.mkdir')
@patch('builtins.open', new_callable=mock_open)
@patch('src.backend.config_manager.Path.replace')
def test_save_success(mock_replace, mock_file, mock_mkdir, manager):
    manager.set("test_key", "test_val")
    result = manager.save()
    assert result is True
    mock_mkdir.assert_called()
    mock_file.assert_called_with(Path('/tmp/mock_config.tmp'), 'w', encoding='utf-8')
    mock_replace.assert_called_once()

@patch('src.backend.config_manager.Path.mkdir')
def test_save_permission_error(mock_mkdir, manager):
    mock_mkdir.side_effect = PermissionError
    result = manager.save()
    assert result is False
