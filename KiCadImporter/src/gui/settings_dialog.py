from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QComboBox, 
                             QFormLayout, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
from src.backend.config_manager import instance as config
from src.backend.env_parser import get_kicad_libraries

class SettingsDialog(QDialog):
    """
    Modal dialog for managing persistent application settings.
    Handles duplication paths, KiCad CLI location, and default library selections.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Settings")
        self.setMinimumWidth(600)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 1. Default Duplication Location
        self.dup_dir_edit = QLineEdit()
        self.dup_dir_edit.setPlaceholderText("Directory to store duplicate assets...")
        self.dup_dir_btn = QPushButton("Browse...")
        self.dup_dir_btn.clicked.connect(self._browse_dup_dir)
        
        dup_layout = QHBoxLayout()
        dup_layout.addWidget(self.dup_dir_edit)
        dup_layout.addWidget(self.dup_dir_btn)
        form.addRow("Default Duplication Location:", dup_layout)
        
        # 2. Preferred KiCad CLI Path
        self.kicad_cli_edit = QLineEdit()
        self.kicad_cli_edit.setPlaceholderText("Path to kicad-cli binary...")
        self.kicad_cli_btn = QPushButton("Browse...")
        self.kicad_cli_btn.clicked.connect(self._browse_kicad_cli)
        
        cli_layout = QHBoxLayout()
        cli_layout.addWidget(self.kicad_cli_edit)
        cli_layout.addWidget(self.kicad_cli_btn)
        form.addRow("KiCad CLI Path:", cli_layout)
        
        # 3. Theme Settings
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        form.addRow("Application Theme:", self.theme_combo)
        
        # 4. Default Symbol Library
        self.sym_lib_edit = QLineEdit()
        self.sym_lib_edit.setPlaceholderText("Default symbol library (.kicad_sym)...")
        self.sym_lib_btn = QPushButton("Browse...")
        self.sym_lib_btn.clicked.connect(self._browse_sym_lib)
        
        sym_layout = QHBoxLayout()
        sym_layout.addWidget(self.sym_lib_edit)
        sym_layout.addWidget(self.sym_lib_btn)
        form.addRow("Default Symbol Library:", sym_layout)
        
        # 5. Default Footprint Library
        self.fp_lib_edit = QLineEdit()
        self.fp_lib_edit.setPlaceholderText("Default footprint library (.pretty dir)...")
        self.fp_lib_btn = QPushButton("Browse...")
        self.fp_lib_btn.clicked.connect(self._browse_fp_lib)
        
        fp_layout = QHBoxLayout()
        fp_layout.addWidget(self.fp_lib_edit)
        fp_layout.addWidget(self.fp_lib_btn)
        form.addRow("Default Footprint Library:", fp_layout)
        
        layout.addLayout(form)
        
        # Add a separator line for visual clarity
        line = QLabel()
        line.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        layout.addWidget(line)

        # Standard Dialog Buttons (Save / Cancel)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)



    def _browse_dup_dir(self):
        """Opens a directory picker for the duplication location."""
        current = self.dup_dir_edit.text()
        directory = QFileDialog.getExistingDirectory(self, "Select Duplication Directory", current)
        if directory:
            self.dup_dir_edit.setText(directory)

    def _browse_kicad_cli(self):
        """Opens a file picker for the kicad-cli binary."""
        current = self.kicad_cli_edit.text()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select kicad-cli binary", current)
        if file_path:
            self.kicad_cli_edit.setText(file_path)

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

    def load_settings(self):
        """Loads persistent values from the ConfigManager into the UI widgets."""
        self.dup_dir_edit.setText(config.get("last_duplication_directory", ""))
        self.kicad_cli_edit.setText(config.get("kicad_cli_path", ""))
        self.theme_combo.setCurrentText(config.get("theme", "System"))
        
        # Sync default library selections
        self.sym_lib_edit.setText(config.get("last_used_symbol_lib_path", ""))
        self.fp_lib_edit.setText(config.get("last_used_footprint_lib_path", ""))

    def save_settings(self):
        """Validates and persists the current UI values to disk via ConfigManager."""
        config.set("last_duplication_directory", self.dup_dir_edit.text())
        config.set("kicad_cli_path", self.kicad_cli_edit.text())
        config.set("theme", self.theme_combo.currentText())
        
        # Persist library selections
        config.set("last_used_symbol_lib_path", self.sym_lib_edit.text())
        config.set("last_used_footprint_lib_path", self.fp_lib_edit.text())
        
        if config.save():
            self.accept()
        else:
            QMessageBox.critical(self, "Configuration Error", "Could not save settings to disk.")
