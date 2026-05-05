from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QListWidget, QListWidgetItem, QPushButton, 
                             QLabel, QFileDialog, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import pathlib

from src.backend.config_manager import instance as config

class AdvancedLibraryBrowser(QDialog):
    """
    A robust dialog for selecting KiCad libraries with Search, Pinned, and Recents functionality.
    """
    librarySelected = pyqtSignal(str)

    def __init__(self, lib_type: str = "symbol", parent=None):
        super().__init__(parent)
        self.lib_type = lib_type # "symbol" or "footprint"
        self.setWindowTitle(f"Select {lib_type.capitalize()} Library")
        self.resize(600, 400)
        
        self.recent_key = f"recent_{lib_type}_libs"
        self.pinned_key = f"pinned_{lib_type}_libs"
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search libraries...")
        self.search_input.textChanged.connect(self._filter_lists)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        # Browse button
        self.browse_btn = QPushButton("Browse System...")
        self.browse_btn.clicked.connect(self._browse_system)
        search_layout.addWidget(self.browse_btn)
        
        layout.addLayout(search_layout)

        # Tabs for Pinned and Recents
        self.tabs = QTabWidget()
        
        # Pinned Tab
        self.pinned_list = QListWidget()
        self.pinned_list.itemDoubleClicked.connect(self._accept_selection)
        self.tabs.addTab(self.pinned_list, "Pinned")
        
        # Recents Tab
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._accept_selection)
        self.tabs.addTab(self.recent_list, "Recent")
        
        # All Tab
        self.all_list = QListWidget()
        self.all_list.itemDoubleClicked.connect(self._accept_selection)
        self.tabs.addTab(self.all_list, "All Configured")
        
        layout.addWidget(self.tabs)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.pin_btn = QPushButton("Pin/Unpin Selected")
        self.pin_btn.clicked.connect(self._toggle_pin)
        
        self.select_btn = QPushButton("Select")
        self.select_btn.clicked.connect(self._accept_selection)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.pin_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.select_btn)
        
        layout.addLayout(btn_layout)

    def _load_data(self):
        from src.backend.env_parser import get_kicad_libraries
        self.pinned_list.clear()
        self.recent_list.clear()
        self.all_list.clear()
        
        pinned = config.get(self.pinned_key, [])
        recent = config.get(self.recent_key, [])
        
        for p in pinned:
            self._add_item(self.pinned_list, p)
            
        for r in recent:
            if r not in pinned: # Don't duplicate in recents if it's pinned
                self._add_item(self.recent_list, r)
                
        try:
            syms, fps = get_kicad_libraries()
            all_libs = syms if self.lib_type == "symbol" else fps
            for lib in all_libs:
                path_str = lib.get("path", "")
                name = lib.get("nickname", pathlib.Path(path_str).name)
                # Ensure we add using a similar visual format, but with nickname
                item = QListWidgetItem(f"{name} ({pathlib.Path(path_str).name})")
                item.setToolTip(path_str)
                item.setData(Qt.ItemDataRole.UserRole, path_str)
                self.all_list.addItem(item)
        except Exception:
            pass

    def _add_item(self, list_widget, path_str):
        item = QListWidgetItem(pathlib.Path(path_str).name)
        item.setToolTip(path_str)
        item.setData(Qt.ItemDataRole.UserRole, path_str)
        list_widget.addItem(item)

    def _filter_lists(self, text):
        query = text.lower()
        for list_widget in [self.pinned_list, self.recent_list, self.all_list]:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                path_str = item.data(Qt.ItemDataRole.UserRole).lower()
                name_str = item.text().lower()
                item.setHidden(query not in path_str and query not in name_str)

    def _toggle_pin(self):
        current_list = self.tabs.currentWidget()
        item = current_list.currentItem()
        if not item: return
        
        path_str = item.data(Qt.ItemDataRole.UserRole)
        pinned = config.get(self.pinned_key, [])
        
        if path_str in pinned:
            pinned.remove(path_str)
        else:
            pinned.append(path_str)
            
        config.set(self.pinned_key, pinned)
        config.save()
        self._load_data()

    def _add_to_recent(self, path_str):
        recent = config.get(self.recent_key, [])
        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        
        # Keep only last 20 recents
        recent = recent[:20]
        config.set(self.recent_key, recent)
        config.save()
        self._load_data()

    def _browse_system(self):
        if self.lib_type == "symbol":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Symbol Library", "", "KiCad Symbol Library (*.kicad_sym)"
            )
            if file_path:
                self._add_to_recent(file_path)
                self.librarySelected.emit(file_path)
                self.accept()
        else:
            directory = QFileDialog.getExistingDirectory(
                self, "Select Footprint Library (.pretty folder)"
            )
            if directory:
                self._add_to_recent(directory)
                self.librarySelected.emit(directory)
                self.accept()

    def _accept_selection(self):
        current_list = self.tabs.currentWidget()
        item = current_list.currentItem()
        if item:
            path_str = item.data(Qt.ItemDataRole.UserRole)
            self._add_to_recent(path_str)
            self.librarySelected.emit(path_str)
            self.accept()

