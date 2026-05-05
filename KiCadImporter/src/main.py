# KiCadImporter Entry Point

import sys
import logging
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.controller import Controller


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    
    app = QApplication(sys.argv)
    

    
    app.setApplicationName("KiCad Importer")
    app.setOrganizationName("KiCadTooling")
    
    # Initialize UI
    window = MainWindow()
    
    # Initialize Controller (Orchestrator)
    # The controller manages the connection between view and backend
    controller = Controller(window)
    
    # Handle "Open With" files passed via command line
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.lower().endswith('.zip'):
                logging.getLogger(__name__).debug(f"Open With: Submitting {arg} to controller")
                controller.handle_zip_import(arg)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
