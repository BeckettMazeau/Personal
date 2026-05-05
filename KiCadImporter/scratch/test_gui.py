import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from gui.main_window import MainWindow

def test_integration_hooks(window):
    """Verifies that external widgets can be inserted."""
    queue_widget = QWidget()
    queue_layout = QVBoxLayout(queue_widget)
    queue_layout.addWidget(QLabel("INTEGRATED QUEUE WIDGET"))
    queue_widget.setStyleSheet("background-color: #444; border: 2px solid green;")
    
    preview_widget = QWidget()
    preview_layout = QVBoxLayout(preview_widget)
    preview_layout.addWidget(QLabel("INTEGRATED PREVIEW WIDGET"))
    preview_widget.setStyleSheet("background-color: #444; border: 2px solid blue;")
    
    window.set_queue_widget(queue_widget)
    window.set_preview_widget(preview_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    # Test integration hooks
    test_integration_hooks(window)
    
    # Connect signal to print to console
    window.zipFileDropped.connect(lambda p: print(f"FILE DROPPED: {p}"))
    
    window.show()
    
    print("GUI started. Close the window to complete the test.")
    sys.exit(app.exec())
