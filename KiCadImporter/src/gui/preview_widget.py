from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter
import pathlib


class SvgScalingWidget(QWidget):
    """
    Custom widget that renders an SVG scaled to fit the available space
    while maintaining aspect ratio. Supports zoom via a zoom_factor.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = QSvgRenderer()
        self.zoom_factor = 1.0

    def load(self, path: str):
        self.renderer.load(path)
        self.update()

    def clear(self):
        self.renderer = QSvgRenderer()
        self.update()

    def paintEvent(self, event):
        if not self.renderer.isValid():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get SVG default size and widget size
        svg_size = self.renderer.defaultSize()
        widget_w = self.width()
        widget_h = self.height()

        if svg_size.width() <= 0 or svg_size.height() <= 0:
            return

        # Calculate scale to fit widget, preserving aspect ratio
        scale_x = widget_w / svg_size.width()
        scale_y = widget_h / svg_size.height()
        base_scale = min(scale_x, scale_y)

        # Apply user zoom on top of the fit-to-window scale
        scale = base_scale * self.zoom_factor

        # Calculate the rendered size
        render_w = svg_size.width() * scale
        render_h = svg_size.height() * scale

        # Center the SVG in the widget
        x = (widget_w - render_w) / 2
        y = (widget_h - render_h) / 2

        target = QRectF(x, y, render_w, render_h)
        self.renderer.render(painter, target)
        painter.end()


class PreviewWidget(QWidget):
    """
    Widget to display SVG previews of KiCad symbols and footprints.
    Automatically scales content to fit the available space.
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
        self.symbol_svg = SvgScalingWidget()
        self.tabs.addTab(self.symbol_svg, "Symbol")

        # Footprint Preview
        self.footprint_svg = SvgScalingWidget()
        self.tabs.addTab(self.footprint_svg, "Footprint")

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

    def update_from_task(self, task):
        """
        Updates the preview based on an ImportTask.
        Placeholder — the orchestrator calls load_previews directly.
        """
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
            has_content = True
        else:
            self.symbol_svg.clear()
            self.tabs.setTabEnabled(0, False)

        if footprint_svg_path and pathlib.Path(footprint_svg_path).exists():
            self.footprint_svg.load(footprint_svg_path)
            self.tabs.setTabEnabled(1, True)
            has_content = True
        else:
            self.footprint_svg.clear()
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
        self.symbol_svg.zoom_factor = self.zoom_factor
        self.symbol_svg.update()
        self.footprint_svg.zoom_factor = self.zoom_factor
        self.footprint_svg.update()

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

