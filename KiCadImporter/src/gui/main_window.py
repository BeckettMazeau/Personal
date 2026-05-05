import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QStackedWidget, QMenuBar, QStatusBar,
    QLabel, QFileDialog, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QCloseEvent

class MainWindow(QMainWindow):
    """
    Primary application window for the KiCad Importer.
    Handles the high-level layout, drag-and-drop zip file interception,
    and provides hooks for external component integration.
    """
    
    zipFileDropped = pyqtSignal(str)
    executeRequested = pyqtSignal()
    windowClosing = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("KiCad Component Importer")
        self.setMinimumSize(1000, 700)
        
        # Enable Drag and Drop
        self.setAcceptDrops(True)
        
        # Initialize UI components
        self._init_menu_bar()
        self._init_central_widget()
        self._init_status_bar()
        
        # Apply modern styling
        self._apply_styles()
        
    def _init_menu_bar(self):
        """Initializes the standard menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Zip...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._handle_open_zip)
        file_menu.addAction(open_action)
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(lambda: self.show_message("Settings clicked (Placeholder)"))
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _init_central_widget(self):
        """Initializes the central layout with placeholders."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter for Part Queue and Preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Placeholders
        self.queue_placeholder = QLabel("Part Queue Placeholder")
        self.queue_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_placeholder.setStyleSheet("background-color: #2b2b2b; border: 1px dashed #555; color: #888;")
        
        self.preview_placeholder = QLabel("Preview Area Placeholder\nDrop a .zip file here")
        self.preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_placeholder.setStyleSheet("background-color: #2b2b2b; border: 1px dashed #555; color: #888;")
        
        self.splitter.addWidget(self.queue_placeholder)
        self.splitter.addWidget(self.preview_placeholder)
        
        # Set initial sizes (30% queue, 70% preview)
        self.splitter.setSizes([300, 700])
        
        self.main_layout.addWidget(self.splitter)
        
        # Execute Button
        self.btn_execute = QPushButton("Execute Import")
        self.btn_execute.setMinimumHeight(50)
        self.btn_execute.setEnabled(False) # Disabled until we have tasks
        self.btn_execute.clicked.connect(self.executeRequested.emit)
        self.main_layout.addWidget(self.btn_execute)
        
    def _init_status_bar(self):
        """Initializes the persistent status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def _apply_styles(self):
        """Applies a modern dark-mode aesthetic."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-bottom: 1px solid #3f3f3f;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3f3f3f;
            }
            QMenu::item:selected {
                background-color: #007acc;
            }
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #3f3f3f;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            QPushButton:hover:enabled {
                background-color: #0098ff;
            }
        """)

    # --- Component Integration Hooks ---
    
    def set_queue_widget(self, widget: QWidget):
        """
        Hook to insert the Part Queue widget.
        Replaces the placeholder in the left pane of the splitter.
        """
        # Find the index of the placeholder
        idx = self.splitter.indexOf(self.queue_placeholder)
        if idx != -1:
            self.queue_placeholder.hide()
            self.splitter.replaceWidget(idx, widget)
            self.queue_placeholder = widget # Track the new widget
        else:
            # If already replaced, just add/replace logic could be more complex
            # For now, we assume a single replacement
            pass

    def set_preview_widget(self, widget: QWidget):
        """
        Hook to insert the Preview widget.
        Replaces the placeholder in the right pane of the splitter.
        """
        idx = self.splitter.indexOf(self.preview_placeholder)
        if idx != -1:
            self.preview_placeholder.hide()
            self.splitter.replaceWidget(idx, widget)
            self.preview_placeholder = widget
            
    # --- Drag and Drop Handling ---
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Intercepts drag events to check for .zip files."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(".zip") for url in urls):
                event.acceptProposedAction()
                self.status_bar.showMessage("Release to import zip archive...")
                return
        event.ignore()
        
    def dropEvent(self, event: QDropEvent):
        """Handles the drop event and extracts file paths."""
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".zip"):
                self.status_bar.showMessage(f"Processing: {os.path.basename(file_path)}")
                self.zipFileDropped.emit(file_path)
        event.acceptProposedAction()
        
    # --- Action Handlers ---
    
    def _handle_open_zip(self):
        """Manual file dialog for opening zip archives."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open KiCad Component Zip", "", "Zip Archives (*.zip)"
        )
        if file_path:
            self.zipFileDropped.emit(file_path)
            self.status_bar.showMessage(f"Processing: {os.path.basename(file_path)}")
            
    def _show_about(self):
        """Displays the about dialog."""
        QMessageBox.about(
            self, "About KiCad Importer",
            "<h3>KiCad Component Importer</h3>"
            "<p>A tool to facilitate importing symbols and footprints into KiCad libraries.</p>"
            "<p>Version: 0.1.0</p>"
        )
        
    def show_message(self, message: str, timeout: int = 5000):
        """Helper to show a message in the status bar."""
        self.status_bar.showMessage(message, timeout)

    def closeEvent(self, event: QCloseEvent):
        """Emits signal when window is closing."""
        self.windowClosing.emit()
        super().closeEvent(event)

    def get_geometry(self) -> str:
        """Returns the window geometry as a hex string."""
        return self.saveGeometry().toHex().data().decode()

    def restore_geometry(self, geometry_hex: str):
        """Restores the window geometry from a hex string."""
        if geometry_hex:
            self.restoreGeometry(bytes.fromhex(geometry_hex))
