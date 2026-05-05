import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.backend.archive_manager import ArchiveWorkspaceManager
from src.backend.exceptions import FileCollisionError

@pytest.fixture
def manager():
    return ArchiveWorkspaceManager()

@patch('src.backend.archive_manager.zipfile.ZipFile')
@patch('src.backend.archive_manager.tempfile.TemporaryDirectory')
def test_extract_archive(mock_temp_dir, mock_zipfile, manager):
    # Setup mocks
    mock_temp_instance = MagicMock()
    mock_temp_instance.name = '/tmp/mock_workspace'
    mock_temp_dir.return_value = mock_temp_instance
    
    mock_zip_instance = MagicMock()
    mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

    # Execute
    result = manager.extract_archive('test.zip')

    # Verify
    assert result == str(Path('/tmp/mock_workspace').resolve())
    mock_zip_instance.extractall.assert_called_once()
    assert manager.workspace_path == Path('/tmp/mock_workspace').resolve()

def test_identify_files_empty(manager):
    assert manager.identify_files() == {".kicad_sym": [], ".kicad_mod": []}

@patch('src.backend.archive_manager.pathlib.Path.rglob')
def test_identify_files_success(mock_rglob, manager):
    manager.workspace_path = Path('/tmp/mock_workspace')
    
    mock_file1 = MagicMock()
    mock_file1.is_file.return_value = True
    mock_file1.suffix = '.kicad_sym'
    mock_file1.resolve.return_value = Path('/tmp/mock_workspace/test.kicad_sym')

    mock_file2 = MagicMock()
    mock_file2.is_file.return_value = True
    mock_file2.suffix = '.kicad_mod'
    mock_file2.resolve.return_value = Path('/tmp/mock_workspace/test.kicad_mod')
    
    mock_file3 = MagicMock()
    mock_file3.is_file.return_value = True
    mock_file3.suffix = '.txt'
    mock_file3.resolve.return_value = Path('/tmp/mock_workspace/test.txt')

    mock_rglob.return_value = [mock_file1, mock_file2, mock_file3]

    result = manager.identify_files()
    assert len(result['.kicad_sym']) == 1
    assert len(result['.kicad_mod']) == 1

@patch('src.backend.archive_manager.shutil.copy2')
@patch('src.backend.archive_manager.pathlib.Path.exists')
def test_copy_to_target_success(mock_exists, mock_copy2, manager):
    mock_exists.side_effect = [True, False] # Source exists, Destination does not exist
    
    with patch('src.backend.archive_manager.pathlib.Path.mkdir') as mock_mkdir:
        result = manager.copy_to_target('/tmp/src/test.kicad_sym', '/tmp/dst')
        
    mock_copy2.assert_called_once()
    assert result.name == 'test.kicad_sym'

@patch('src.backend.archive_manager.pathlib.Path.exists')
def test_copy_to_target_source_missing(mock_exists, manager):
    mock_exists.return_value = False
    
    with pytest.raises(FileNotFoundError):
        manager.copy_to_target('missing.kicad_sym', '/tmp/dst')

@patch('src.backend.archive_manager.pathlib.Path.exists')
def test_copy_to_target_collision(mock_exists, manager):
    mock_exists.side_effect = [True, True] # Source exists, Destination exists
    
    with patch('src.backend.archive_manager.pathlib.Path.mkdir'):
        with pytest.raises(FileCollisionError):
            manager.copy_to_target('/tmp/src/test.kicad_sym', '/tmp/dst')

def test_context_manager():
    with patch('src.backend.archive_manager.ArchiveWorkspaceManager.cleanup') as mock_cleanup:
        with ArchiveWorkspaceManager() as mgr:
            pass
        mock_cleanup.assert_called_once()
