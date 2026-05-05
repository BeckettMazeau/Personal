import os
import pathlib
import logging
from typing import List, Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.backend.config_manager import instance as config
from src.backend.archive_manager import ArchiveWorkspaceManager
from src.backend.cli_wrapper import KiCadCLIWrapper
from src.backend.name_parser import suggest_part_name
from src.backend.env_parser import KiCadEnvParser
from src.backend.models import ImportTask, ImportStatus, validate_paths
from src.backend.exceptions import KiCadImportError



from src.gui.main_window import MainWindow
from src.gui.queue_widget import QueueWidget
from src.gui.preview_widget import PreviewWidget

logger = logging.getLogger(__name__)

class ProcessingWorker(QRunnable):
    """
    Worker for heavy operations: zip extraction and CLI preview generation.
    """
    class WorkerSignals(QObject):
        finished = pyqtSignal(object) # Returns a list of ImportTask objects
        error = pyqtSignal(str)
        progress = pyqtSignal(str)

    def __init__(self, zip_path: str, workspace_mgr: ArchiveWorkspaceManager, cli: KiCadCLIWrapper):
        super().__init__()
        self.zip_path = zip_path
        self.workspace_mgr = workspace_mgr
        self.cli = cli
        self.signals = self.WorkerSignals()

    def run(self):
        try:
            logger.debug(f"Starting ProcessingWorker for: {self.zip_path}")
            self.signals.progress.emit(f"Extracting {os.path.basename(self.zip_path)}...")
            
            # 1. Extract Archive
            workspace = self.workspace_mgr.extract_archive(self.zip_path)
            logger.debug(f"Archive extracted to workspace: {workspace}")
            
            files = self.workspace_mgr.identify_files()
            logger.debug(f"Identified files: {files}")
            
            # 2. Group files and suggest part name
            all_files = files[".kicad_sym"] + files[".kicad_mod"]
            if not all_files:
                logger.warning("No KiCad symbol or footprint files found in archive.")
                self.signals.error.emit("No KiCad symbol or footprint files found in archive.")
                return

            part_name = suggest_part_name([str(p) for p in all_files], self.zip_path)
            logger.debug(f"Suggested part name: {part_name}")
            
            # 3. Create ImportTask
            task = ImportTask(
                original_zip_path=self.zip_path,
                extracted_part_name=part_name
            )
            
            # Identify specific source paths
            if files[".kicad_sym"]:
                task.symbol_source_path = str(files[".kicad_sym"][0])
            if files[".kicad_mod"]:
                task.footprint_source_path = str(files[".kicad_mod"][0])

            # 4. Generate Previews
            preview_dir = pathlib.Path(workspace) / "previews"
            preview_dir.mkdir(exist_ok=True)
            logger.debug(f"Created preview directory at: {preview_dir}")
            
            previews = {"symbol": None, "footprint": None}
            
            if task.symbol_source_path:
                logger.debug(f"Attempting to generate symbol preview for {task.symbol_source_path}")
                self.signals.progress.emit("Generating symbol preview...")
                out_path = preview_dir / f"{part_name}_sym.svg"
                res = self.cli.generate_symbol_preview(task.symbol_source_path, out_path)
                logger.debug(f"Symbol preview generation result: success={res.success}, error={res.error_message}, output_files={res.output_files}")
                logger.debug(f"Symbol CLI Logs:\n{res.logs}")
                if res.success:
                    previews["symbol"] = res.output_files[0]
            
            if task.footprint_source_path:
                logger.debug(f"Attempting to generate footprint preview for {task.footprint_source_path}")
                self.signals.progress.emit("Generating footprint preview...")
                out_path = preview_dir / f"{part_name}_fp_out"
                res = self.cli.generate_footprint_preview(task.footprint_source_path, out_path)
                logger.debug(f"Footprint preview generation result: success={res.success}, error={res.error_message}, output_files={res.output_files}")
                logger.debug(f"Footprint CLI Logs:\n{res.logs}")
                if res.success:
                    previews["footprint"] = res.output_files[0]

            logger.debug(f"ProcessingWorker finished successfully for {part_name}")
            self.signals.finished.emit((task, previews))

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.signals.error.emit(str(e))


class ExecutionWorker(QRunnable):
    """
    Worker for performing the final file copy operations to prevent blocking the UI.
    """
    class WorkerSignals(QObject):
        finished = pyqtSignal(int, list)  # success_count, list of error strings
        progress = pyqtSignal(str)

    def __init__(self, tasks: List[ImportTask], workspace_mgr: ArchiveWorkspaceManager):
        super().__init__()
        self.tasks = tasks
        self.workspace_mgr = workspace_mgr
        self.signals = self.WorkerSignals()

    def run(self):
        success_count = 0
        errors = []
        
        for task in self.tasks:
            if task.status == ImportStatus.COMPLETED:
                continue

            # Symptom 5: Respect collision status — do not blindly overwrite
            if task.status == ImportStatus.COLLISION:
                errors.append(f"{task.extracted_part_name}: Collision detected — skipped (resolve collision first)")
                continue

            # Symptom 6: Fail tasks that have no target libraries configured
            has_sym_target = bool(task.symbol_source_path and task.target_symbol_lib)
            has_fp_target = bool(task.footprint_source_path and task.target_footprint_lib)
            if not has_sym_target and not has_fp_target:
                task.status = ImportStatus.FAILED
                task.error_message = "No target libraries configured"
                errors.append(f"{task.extracted_part_name}: No target libraries configured")
                continue

            try:
                task.status = ImportStatus.PROCESSING
                self.signals.progress.emit(f"Importing {task.extracted_part_name}...")
                
                # Copy Symbol
                if has_sym_target:
                    self.workspace_mgr.copy_to_target(task.symbol_source_path, task.target_symbol_lib)
                
                # Copy Footprint
                if has_fp_target:
                    self.workspace_mgr.copy_to_target(task.footprint_source_path, task.target_footprint_lib)
                
                task.status = ImportStatus.COMPLETED
                success_count += 1
                
            except Exception as e:
                task.status = ImportStatus.FAILED
                task.error_message = str(e)
                errors.append(f"{task.extracted_part_name}: {str(e)}")
                
        self.signals.finished.emit(success_count, errors)


class Controller(QObject):
    """
    Main controller to orchestrate the application logic and UI.
    """
    
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self.view = main_window
        self.thread_pool = QThreadPool.globalInstance()
        
        # Backend Instances
        self.workspace_mgr = ArchiveWorkspaceManager()
        self.cli = KiCadCLIWrapper()
        self.env_parser = KiCadEnvParser()
        
        # State
        self.tasks: List[ImportTask] = []
        
        # UI Components to be injected
        self.queue_widget = QueueWidget()
        self.preview_widget = PreviewWidget()
        
        self._setup_ui_integration()
        self._connect_signals()
        self._load_state()

    def _setup_ui_integration(self):
        """Injects real widgets into MainWindow hooks."""
        self.view.set_queue_widget(self.queue_widget)
        self.view.set_preview_widget(self.preview_widget)

    def _connect_signals(self):
        """Maps UI signals to controller methods."""
        self.view.zipFileDropped.connect(self.handle_zip_import)
        self.view.executeRequested.connect(self.execute_imports)
        self.view.windowClosing.connect(self.save_state)
        
        self.queue_widget.taskSelected.connect(self.handle_task_selection)

    def _load_state(self):
        """Restores window geometry and paths from config."""
        geom = config.get("window_geometry")
        if geom:
            try:
                self.view.restore_geometry(geom)
            except Exception as e:
                logger.error(f"Failed to restore geometry: {e}")
            
        logger.info("Application state loaded.")

    def save_state(self):
        """Saves current state and geometry to config."""
        # Save geometry
        config.set("window_geometry", self.view.get_geometry())
        
        # Save last used paths if tasks were added
        if self.tasks:
            last_task = self.tasks[-1]
            if last_task.target_symbol_lib:
                config.set("last_used_symbol_lib_path", last_task.target_symbol_lib)
            if last_task.target_footprint_lib:
                config.set("last_used_footprint_lib_path", last_task.target_footprint_lib)
        
        config.save()
        logger.info("Application state saved.")

    @pyqtSlot(str)
    def handle_zip_import(self, zip_path: str):
        """Starts the async process to handle a new zip file."""
        worker = ProcessingWorker(zip_path, self.workspace_mgr, self.cli)
        worker.signals.finished.connect(self.on_processing_finished)
        worker.signals.error.connect(self.on_processing_error)
        worker.signals.progress.connect(lambda msg: self.view.show_message(msg))
        
        self.thread_pool.start(worker)

    def on_processing_finished(self, result):
        task, previews = result
        
        # Set default target libraries from config or last used
        task.target_symbol_lib = config.get("last_used_symbol_lib_path")
        task.target_footprint_lib = config.get("last_used_footprint_lib_path")
        
        # Validate for collisions
        validate_paths(task)
        
        self.tasks.append(task)
        self.queue_widget.add_task(task)
        
        # Store preview paths in the task object (monkey-patching for now as models.py is strict)
        task._previews = previews
        
        self.view.show_message(f"Imported {task.extracted_part_name}", 3000)
        self.view.btn_execute.setEnabled(True)

    def on_processing_error(self, error_msg: str):
        QMessageBox.critical(self.view, "Import Error", f"Failed to process archive:\n{error_msg}")
        self.view.show_message("Ready")

    def handle_task_selection(self, task: ImportTask):
        """Updates the preview area when a task is selected in the queue."""
        if hasattr(task, "_previews"):
            previews = task._previews
            self.preview_widget.load_previews(
                symbol_svg_path=previews.get("symbol"),
                footprint_svg_path=previews.get("footprint")
            )

    def execute_imports(self):
        """Final execution: copy files to target libraries asynchronously."""
        # Disable the execute button to prevent multiple triggers
        self.view.btn_execute.setEnabled(False)
        self.view.show_message("Starting import execution...")
        
        worker = ExecutionWorker(self.tasks, self.workspace_mgr)
        worker.signals.progress.connect(lambda msg: self.view.show_message(msg))
        worker.signals.finished.connect(self.on_execution_finished)
        
        self.thread_pool.start(worker)

    def on_execution_finished(self, success_count: int, errors: list):
        """Callback when the background execution worker finishes."""
        if errors:
            error_msg = "\n".join(errors)
            QMessageBox.warning(self.view, "Import Results", f"Completed {success_count} imports.\n\nErrors:\n{error_msg}")
        else:
            QMessageBox.information(self.view, "Import Results", f"Successfully imported {success_count} parts!")
            
        self.view.show_message("Execution finished.")
        
        # Re-enable execute button if there are still pending/failed tasks
        has_pending = any(t.status != ImportStatus.COMPLETED for t in self.tasks)
        self.view.btn_execute.setEnabled(has_pending)

