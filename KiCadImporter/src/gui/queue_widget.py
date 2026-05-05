from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QLabel, QLineEdit, QHBoxLayout, QPushButton, QFileDialog,
                             QGroupBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QStandardItemModel
from src.backend.models import ImportTask, ImportStatus

class QueueWidget(QWidget):
    """
    Widget to display the list of pending imports (ImportTask objects)
    and provide per-task configuration fields for target libraries.
    """
    taskSelected = pyqtSignal(ImportTask)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        
        layout.addWidget(QLabel("Import Queue:"))
        layout.addWidget(self.list_widget)

        # --- Per-task configuration panel ---
        config_group = QGroupBox("Task Configuration")
        config_layout = QFormLayout()

        # Target Symbol Library path
        sym_row = QHBoxLayout()
        self.sym_lib_edit = QLineEdit()
        self.sym_lib_edit.setPlaceholderText("Target symbol library (.kicad_sym)...")
        self.sym_lib_edit.textChanged.connect(self._on_sym_lib_changed)
        sym_browse = QPushButton("Browse...")
        sym_browse.clicked.connect(self._browse_sym_lib)
        sym_row.addWidget(self.sym_lib_edit)
        sym_row.addWidget(sym_browse)
        config_layout.addRow("Symbol Library:", sym_row)

        # Target Footprint Library path
        fp_row = QHBoxLayout()
        self.fp_lib_edit = QLineEdit()
        self.fp_lib_edit.setPlaceholderText("Target footprint library (.pretty dir)...")
        self.fp_lib_edit.textChanged.connect(self._on_fp_lib_changed)
        fp_browse = QPushButton("Browse...")
        fp_browse.clicked.connect(self._browse_fp_lib)
        fp_row.addWidget(self.fp_lib_edit)
        fp_row.addWidget(fp_browse)
        config_layout.addRow("Footprint Library:", fp_row)

        # Part name override
        self.part_name_edit = QLineEdit()
        self.part_name_edit.setPlaceholderText("Part name (auto-detected)...")
        self.part_name_edit.textChanged.connect(self._on_part_name_changed)
        config_layout.addRow("Part Name:", self.part_name_edit)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

    def add_task(self, task: ImportTask):
        """
        Adds a new ImportTask to the queue.
        """
        import pathlib
        sym_name = pathlib.Path(task.symbol_source_path).name if task.symbol_source_path else "No symbol"
        fp_name = pathlib.Path(task.footprint_source_path).name if task.footprint_source_path else "No footprint"
        
        display_text = f"{task.extracted_part_name}\n  └ {sym_name}\n  └ {fp_name}"
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, task)
        
        # Add warning icon if collision detected
        if task.collision_detected or task.status == ImportStatus.COLLISION:
            item.setToolTip("Collision detected! This part already exists in the target library.")
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxWarning)
            item.setIcon(icon)
        else:
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView)
            item.setIcon(icon)

        self.list_widget.addItem(item)

    def clear_tasks(self):
        self.list_widget.clear()

    def _get_current_task(self) -> ImportTask | None:
        """Returns the currently selected ImportTask, or None."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_item_changed(self, current, previous):
        if current:
            task = current.data(Qt.ItemDataRole.UserRole)
            # Populate configuration fields with the selected task's data
            self.sym_lib_edit.blockSignals(True)
            self.fp_lib_edit.blockSignals(True)
            self.part_name_edit.blockSignals(True)

            self.sym_lib_edit.setText(task.target_symbol_lib or "")
            self.fp_lib_edit.setText(task.target_footprint_lib or "")
            self.part_name_edit.setText(task.extracted_part_name or "")

            self.sym_lib_edit.blockSignals(False)
            self.fp_lib_edit.blockSignals(False)
            self.part_name_edit.blockSignals(False)

            self.taskSelected.emit(task)

    def _on_sym_lib_changed(self, text: str):
        task = self._get_current_task()
        if task:
            task.target_symbol_lib = text if text else None

    def _on_fp_lib_changed(self, text: str):
        task = self._get_current_task()
        if task:
            task.target_footprint_lib = text if text else None

    def _on_part_name_changed(self, text: str):
        task = self._get_current_task()
        if task and text:
            task.extracted_part_name = text

    def _browse_sym_lib(self):
        from src.gui.library_browser import AdvancedLibraryBrowser
        dialog = AdvancedLibraryBrowser(lib_type="symbol", parent=self)
        dialog.librarySelected.connect(lambda path: self.sym_lib_edit.setText(path))
        dialog.exec()

    def _browse_fp_lib(self):
        from src.gui.library_browser import AdvancedLibraryBrowser
        dialog = AdvancedLibraryBrowser(lib_type="footprint", parent=self)
        dialog.librarySelected.connect(lambda path: self.fp_lib_edit.setText(path))
        dialog.exec()
