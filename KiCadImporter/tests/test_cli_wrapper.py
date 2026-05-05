import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.backend.cli_wrapper import KiCadCLIWrapper
from src.backend.exceptions import KiCadCLINotFoundError

@pytest.fixture
def wrapper():
    return KiCadCLIWrapper()

@patch('src.backend.cli_wrapper.subprocess.run')
def test_check_kicad_cli_success(mock_run, wrapper):
    mock_run.return_value = MagicMock(returncode=0)
    assert wrapper.check_kicad_cli() is True

@patch('src.backend.cli_wrapper.subprocess.run')
def test_check_kicad_cli_not_found(mock_run, wrapper):
    mock_run.side_effect = FileNotFoundError
    with pytest.raises(KiCadCLINotFoundError):
        wrapper.check_kicad_cli()

@patch('src.backend.cli_wrapper.subprocess.run')
def test_check_kicad_cli_error(mock_run, wrapper):
    mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')
    with pytest.raises(KiCadCLINotFoundError):
        wrapper.check_kicad_cli()

@patch('src.backend.cli_wrapper.subprocess.run')
@patch('src.backend.cli_wrapper.pathlib.Path.exists')
def test_generate_symbol_preview_success(mock_exists, mock_run, wrapper):
    mock_exists.return_value = True
    mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
    
    with patch('src.backend.cli_wrapper.pathlib.Path.mkdir'):
        result = wrapper.generate_symbol_preview('input.kicad_sym', 'output.svg')
        
    assert result.success is True
    assert len(result.output_files) == 1
    assert 'output.svg' in result.output_files[0]
    assert result.error_message is None

@patch('src.backend.cli_wrapper.subprocess.run')
def test_generate_symbol_preview_timeout(mock_run, wrapper):
    mock_run.side_effect = subprocess.TimeoutExpired('cmd', 10, b"out", b"err")
    
    with patch('src.backend.cli_wrapper.pathlib.Path.mkdir'):
        result = wrapper.generate_symbol_preview('input.kicad_sym', 'output.svg')
        
    assert result.success is False
    assert "timed out" in result.error_message

@patch('src.backend.cli_wrapper.subprocess.run')
@patch('src.backend.cli_wrapper.pathlib.Path.exists')
def test_generate_footprint_preview_success(mock_exists, mock_run, wrapper):
    mock_exists.return_value = True
    mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
    
    with patch('src.backend.cli_wrapper.pathlib.Path.mkdir'):
        result = wrapper.generate_footprint_preview('input.kicad_mod', 'output.svg')
        
    assert result.success is True
    assert len(result.output_files) == 1
    assert 'output.svg' in result.output_files[0]

@patch('src.backend.cli_wrapper.subprocess.run')
@patch('src.backend.cli_wrapper.pathlib.Path.exists')
def test_generate_preview_missing_output(mock_exists, mock_run, wrapper):
    mock_exists.return_value = False
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    
    with patch('src.backend.cli_wrapper.pathlib.Path.mkdir'):
        result = wrapper.generate_symbol_preview('input.kicad_sym', 'output.svg')
        
    assert result.success is False
    assert "not found" in result.error_message
