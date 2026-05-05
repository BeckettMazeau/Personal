import os
import pytest
import tempfile
import zipfile
import pathlib

from PyQt6.QtWidgets import QApplication, QLineEdit

from src.backend.archive_manager import ArchiveWorkspaceManager
from src.backend.models import ImportTask, ImportStatus, validate_paths
from src.gui.main_window import MainWindow
from src.gui.queue_widget import QueueWidget
from src.gui.controller import ExecutionWorker


@pytest.fixture(scope="session")
def qapp():
    """Provides a QApplication instance for testing PyQt6 widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_zip_nested(tmp_path):
    """Creates a mock zip archive with deeply nested KiCad files (Symptom 7)."""
    zip_path = tmp_path / "nested_test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("deep/nested/folder/part.kicad_sym", "(symbol \"part\" )")
        zf.writestr("another/folder/part.kicad_mod", "(module part )")
    return str(zip_path)


def test_symptom_2_absent_data_binding(qapp):
    """
    Symptom 2: set_queue_widget replaces the placeholder but fails to show() the widget.
    Expected: The injected QueueWidget should be visible.
    """
    window = MainWindow()
    queue = QueueWidget()
    
    window.set_queue_widget(queue)
    
    # This will fail because the main window code hides the placeholder but never 
    # explicitly calls .show() on the newly inserted queue widget.
    assert queue.isVisible() is True, "Symptom 2: QueueWidget was injected but never explicitly shown."


def test_symptom_3_missing_configuration(qapp):
    """
    Symptom 3: The UI lacks mechanisms to configure Target Symbol/Footprint Names and Libraries.
    Expected: QueueWidget should have input fields for configuration.
    """
    queue = QueueWidget()
    
    # We expect the QueueWidget (or a detail panel) to have QLineEdits for the user to configure 
    # target libraries for the specific task.
    line_edits = queue.findChildren(QLineEdit)
    
    assert len(line_edits) > 0, "Symptom 3: Missing input mechanisms for Target Libraries in QueueWidget."


def test_symptom_4_absent_previews(mock_zip_nested):
    """
    Symptom 4: ArchiveWorkspaceManager deletes previous workspaces when processing new zips.
    Expected: Extracting a second archive should not delete the workspace of the first queued task.
    """
    mgr = ArchiveWorkspaceManager()
    
    ws1 = mgr.extract_archive(mock_zip_nested)
    assert os.path.exists(ws1)
    
    # Queueing a second archive
    ws2 = mgr.extract_archive(mock_zip_nested)
    
    # This will fail because extract_archive calls self.cleanup() and deletes ws1
    assert os.path.exists(ws1), "Symptom 4: Previous workspace was prematurely deleted, destroying previews."


def test_symptom_5_ineffective_collision_detection(tmp_path):
    """
    Symptom 5: Overwrite scenarios trigger no interactive warnings or execution prevention.
    Expected: ExecutionWorker should respect task.status == COLLISION and not copy blindly.
    """
    target_lib = tmp_path / "target.kicad_sym"
    target_lib.write_text('(symbol "TestPart" (pin "1") )')
    
    task = ImportTask(
        original_zip_path="dummy.zip",
        extracted_part_name="TestPart",
        symbol_source_path="dummy_src.kicad_sym",
        target_symbol_lib=str(target_lib)
    )
    
    # Validate collision logic (this part works in models.py)
    has_collision = validate_paths(task)
    assert has_collision is True
    assert task.status == ImportStatus.COLLISION
    
    # Mock workspace manager to track copy calls
    class MockWorkspaceMgr:
        called = False
        def copy_to_target(self, src, dst):
            self.called = True
            
    mgr = MockWorkspaceMgr()
    worker = ExecutionWorker([task], mgr)
    worker.run()
    
    # This will fail because ExecutionWorker blindly executes the copy regardless of the collision status
    assert mgr.called is False, "Symptom 5: ExecutionWorker attempted to copy despite COLLISION status."


def test_symptom_6_ambiguous_success_state():
    """
    Symptom 6: The application reports "Successfully imported" even if no target libraries were set.
    Expected: A task with no targets should report failure, not increment the success count.
    """
    task = ImportTask(
        original_zip_path="dummy.zip",
        extracted_part_name="TestPart",
        symbol_source_path="dummy_src.kicad_sym",
        target_symbol_lib=None,  # Missing configuration
        target_footprint_lib=None
    )
    
    class MockWorkspaceMgr:
        def copy_to_target(self, src, dst):
            pass

    mgr = MockWorkspaceMgr()
    worker = ExecutionWorker([task], mgr)
    
    success_count = [0]
    def on_finished(count, errors):
        success_count[0] = count
        
    worker.signals.finished.connect(on_finished)
    worker.run()
    
    # This will fail because ExecutionWorker skips None targets and increments success_count anyway
    assert success_count[0] == 0, "Symptom 6: ExecutionWorker silently succeeded when target libraries were missing."


def test_symptom_7_brittle_archive_handling(mock_zip_nested, tmp_path):
    """
    Symptom 7: The codebase attempts to execute mkdir() on a .kicad_sym file instead of appending.
    Expected: copy_to_target should treat the .kicad_sym target as a file, not a directory.
    """
    mgr = ArchiveWorkspaceManager()
    mgr.extract_archive(mock_zip_nested)
    files = mgr.identify_files()
    
    assert len(files[".kicad_sym"]) == 1
    symbol_src = files[".kicad_sym"][0]
    
    # Create an existing target file
    target_lib = tmp_path / "target.kicad_sym"
    target_lib.write_text("Dummy content")
    
    try:
        # Expected behavior is to copy/append the file.
        # But the broken code does: dst_dir = pathlib.Path(target_dir); dst_dir.mkdir(...)
        # Since target_lib is already a file, mkdir() will raise FileExistsError.
        mgr.copy_to_target(symbol_src, str(target_lib))
        
        # If it miraculously doesn't raise, we assert it didn't turn our file into a directory
        assert target_lib.is_file(), "Symptom 7: target_lib was converted into a directory."
        
    except FileExistsError as e:
        pytest.fail(f"Symptom 7: copy_to_target raised FileExistsError because it treated the target file as a directory. {e}")
