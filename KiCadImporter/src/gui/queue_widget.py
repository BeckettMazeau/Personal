from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QStandardItemModel
from src.backend.models import ImportTask, ImportStatus

class QueueWidget(QWidget):
    """
    Widget to display the list of pending imports (ImportTask objects).
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

    def add_task(self, task: ImportTask):
        """
        Adds a new ImportTask to the queue.
        """
        item = QListWidgetItem(task.extracted_part_name)
        item.setData(Qt.ItemDataRole.UserRole, task)
        
        # Add warning icon if collision detected
        if task.collision_detected or task.status == ImportStatus.COLLISION:
            # Note: In a real app, we'd use a themed icon. 
            # For now, we'll use a standard style icon if available or just text indicator.
            item.setToolTip("Collision detected! This part already exists in the target library.")
            # We can use a standard icon from the style
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxWarning)
            item.setIcon(icon)
        else:
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView)
            item.setIcon(icon)

        self.list_widget.addItem(item)

    def clear_tasks(self):
        self.list_widget.clear()

    def _on_item_changed(self, current, previous):
        if current:
            task = current.data(Qt.ItemDataRole.UserRole)
            self.taskSelected.emit(task)
