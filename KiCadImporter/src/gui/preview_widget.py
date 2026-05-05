from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QTabWidget
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import Qt, QSize
import pathlib

class PreviewWidget(QWidget):
    """
    Widget to display SVG previews of KiCad symbols and footprints.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tabs for Symbol and Footprint
        self.tabs = QTabWidget()
        
        # Symbol Preview
        self.symbol_scroll = QScrollArea()
        self.symbol_scroll.setWidgetResizable(True)
        self.symbol_svg = QSvgWidget()
        self.symbol_scroll.setWidget(self.symbol_svg)
        self.tabs.addTab(self.symbol_scroll, "Symbol")

        # Footprint Preview
        self.footprint_scroll = QScrollArea()
        self.footprint_scroll.setWidgetResizable(True)
        self.footprint_svg = QSvgWidget()
        self.footprint_scroll.setWidget(self.footprint_svg)
        self.tabs.addTab(self.footprint_scroll, "Footprint")

        layout.addWidget(QLabel("Component Preview:"))
        
        # Zoom Control
        zoom_layout = QHBoxLayout()
        self.zoom_label = QLabel("Zoom: 100%")
        zoom_layout.addWidget(self.zoom_label)
        
        layout.addLayout(zoom_layout)
        layout.addWidget(self.tabs)

        # Placeholder message
        self.placeholder = QLabel("Select a part to preview")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.placeholder)
        self.placeholder.hide()

        self.zoom_factor = 1.0

    def update_from_task(self, task: ImportTask):
        """
        Updates the preview based on an ImportTask.
        Note: This assumes the SVGs have been generated and paths are known.
        In this implementation, we look for .svg files in a 'previews' subfolder 
        of the temp workspace, or provided via some mechanism.
        
        For the purpose of this component, we expect the caller to have 
        populated paths or we use a convention.
        """
        # Placeholder logic: in a real integration, the paths would be 
        # retrieved from a cache or the ImportTask would have them.
        # Since I can't modify models.py, I'll assume they might be 
        # added to the task dynamically or managed externally.
        
        # For now, we'll just expose the load_previews method and 
        # assume the orchestrator calls it.
        pass

    def load_previews(self, symbol_svg_path: str = None, footprint_svg_path: str = None):
        """
        Loads the SVG files into the preview widgets.
        """
        self.current_symbol_path = symbol_svg_path
        self.current_footprint_path = footprint_svg_path
        
        has_content = False

        if symbol_svg_path and pathlib.Path(symbol_svg_path).exists():
            self.symbol_svg.load(symbol_svg_path)
            self.tabs.setTabEnabled(0, True)
            self.symbol_svg.adjustSize()
            has_content = True
        else:
            self.tabs.setTabEnabled(0, False)

        if footprint_svg_path and pathlib.Path(footprint_svg_path).exists():
            self.footprint_svg.load(footprint_svg_path)
            self.tabs.setTabEnabled(1, True)
            self.footprint_svg.adjustSize()
            has_content = True
        else:
            self.tabs.setTabEnabled(1, False)

        if not has_content:
            self.placeholder.show()
            self.tabs.hide()
        else:
            self.placeholder.hide()
            self.tabs.show()
            # Default to first enabled tab if current is disabled
            if not self.tabs.isTabEnabled(self.tabs.currentIndex()):
                if self.tabs.isTabEnabled(0):
                    self.tabs.setCurrentIndex(0)
                elif self.tabs.isTabEnabled(1):
                    self.tabs.setCurrentIndex(1)
        
        self.reset_zoom()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self._apply_zoom()

    def _apply_zoom(self):
        self.zoom_label.setText(f"Zoom: {int(self.zoom_factor * 100)}%")
        # To zoom, we resize the QSvgWidgets
        # Note: QSvgWidget scales the content to its size
        if self.tabs.isTabEnabled(0):
            base_size = self.symbol_svg.renderer().defaultSize()
            self.symbol_svg.setFixedSize(base_size * self.zoom_factor)
        
        if self.tabs.isTabEnabled(1):
            base_size = self.footprint_svg.renderer().defaultSize()
            self.footprint_svg.setFixedSize(base_size * self.zoom_factor)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor /= 1.1
            
            # Limit zoom
            self.zoom_factor = max(0.1, min(self.zoom_factor, 10.0))
            self._apply_zoom()
            event.accept()
        else:
            super().wheelEvent(event)

    def clear_preview(self):
        """Resets the preview display."""
        self.load_previews(None, None)
