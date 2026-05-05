from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QCompleter, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List, Dict, Optional

class LibraryBrowser(QWidget):
    """
    A reusable searchable dropdown for selecting KiCad libraries.
    Supports Symbol and Footprint library display with tooltips for full paths.
    
    This widget is used in the global settings and in the batch queue for individual part overrides.
    """
    libraryChanged = pyqtSignal(str)  # Emits the library path when changed

    def __init__(self, label_text: str = "Library:", parent=None):
        super().__init__(parent)
        self._libraries: List[Dict[str, str]] = []
        self._setup_ui(label_text)

    def _setup_ui(self, label_text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.label = QLabel(label_text)
        self.label.setMinimumWidth(150)
        
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Set up completer for searching by nickname
        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo.setCompleter(self.completer)
        
        # Connect signals
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        
        layout.addWidget(self.label)
        layout.addWidget(self.combo, 1)

    def set_libraries(self, libraries: List[Dict[str, str]]):
        """
        Populates the dropdown with library nicknames and paths.
        Expected format: [{"nickname": "...", "path": "..."}]
        """
        self._libraries = libraries
        self.combo.clear()
        
        # Add a placeholder/none option if needed? 
        # Requirement implies choosing from available.
        
        for lib in libraries:
            nickname = lib.get("nickname", "Unknown")
            path = lib.get("path", "")
            self.combo.addItem(nickname, path)
            
            # Set tooltip for each item in the dropdown list
            last_index = self.combo.count() - 1
            self.combo.setItemData(last_index, path, Qt.ItemDataRole.ToolTipRole)

        # Update completer model to match the combo box items
        self.completer.setModel(self.combo.model())

    def get_selected_path(self) -> str:
        """Returns the absolute path of the currently selected library."""
        index = self.combo.currentIndex()
        if index >= 0:
            return self.combo.itemData(index, Qt.ItemDataRole.UserRole)
        return ""

    def set_selected_path(self, path: str):
        """Selects the item matching the given absolute path."""
        for i in range(self.combo.count()):
            if self.combo.itemData(i, Qt.ItemDataRole.UserRole) == path:
                self.combo.setCurrentIndex(i)
                return
        # If not found, we don't change selection or we could clear it
        self.combo.setCurrentIndex(-1)

    def set_collision_error(self, has_collision: bool):
        """
        Highlights the widget in red if a collision is detected.
        Used to alert the user that the part name already exists in the selected library.
        """
        if has_collision:
            # Apply a red border style
            self.combo.setStyleSheet("""
                QComboBox {
                    border: 2px solid #FF0000;
                    border-radius: 4px;
                    background-color: #FFF0F0;
                }
            """)
            self.combo.setToolTip("Collision Warning: Part name already exists in this library!")
        else:
            # Reset to default style
            self.combo.setStyleSheet("")
            # Reset tooltip to the selected path
            path = self.get_selected_path()
            self.combo.setToolTip(path if path else "")

    def _on_index_changed(self, index: int):
        """Handles selection changes and updates the widget tooltip."""
        if index >= 0:
            path = self.combo.itemData(index, Qt.ItemDataRole.UserRole)
            self.combo.setToolTip(path)
            self.libraryChanged.emit(path)
        else:
            self.combo.setToolTip("")
