"""
K3NG Configuration Tool - Export Dialog
Handles export of configuration to .h files
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QLineEdit, QPushButton, QLabel,
    QFileDialog, QCheckBox, QTextEdit, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path

from core.export_manager import ExportManager, ExportMode, ExportResult
from core.config_manager import ConfigurationManager


class ExportDialog(QDialog):
    """Dialog for exporting configuration to .h files"""

    export_completed = pyqtSignal(ExportResult)

    def __init__(self, config_manager: ConfigurationManager, parent=None):
        super().__init__(parent)

        self.config_manager = config_manager
        self.export_manager = ExportManager()

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Export Configuration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>Export Configuration to .h Files</h2>")
        layout.addWidget(header)

        description = QLabel(
            "Generate rotator_features.h, rotator_pins.h, and rotator_settings.h "
            "from the current configuration."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Export mode selection
        mode_group = QGroupBox("Export Mode")
        mode_layout = QVBoxLayout()

        self.modify_existing_radio = QRadioButton("Modify Existing Files")
        self.modify_existing_radio.setChecked(True)
        self.modify_existing_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.modify_existing_radio)

        modify_desc = QLabel(
            "   Overwrites existing rotator_features.h, rotator_pins.h, and rotator_settings.h\n"
            "   in the selected directory. Backups are created automatically."
        )
        modify_desc.setStyleSheet("color: #666; font-size: 9pt;")
        mode_layout.addWidget(modify_desc)

        mode_layout.addSpacing(10)

        self.new_profile_radio = QRadioButton("Create New Profile")
        self.new_profile_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.new_profile_radio)

        new_profile_desc = QLabel(
            "   Creates new files with a custom suffix (e.g., rotator_features_my_config.h).\n"
            "   Original files are not modified."
        )
        new_profile_desc.setStyleSheet("color: #666; font-size: 9pt;")
        mode_layout.addWidget(new_profile_desc)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Profile name input (for new profile mode)
        profile_group = QGroupBox("Profile Name")
        profile_layout = QHBoxLayout()

        profile_layout.addWidget(QLabel("Suffix:"))

        self.profile_input = QLineEdit()
        self.profile_input.setPlaceholderText("e.g., custom, my_config, test")
        self.profile_input.setEnabled(False)
        profile_layout.addWidget(self.profile_input)

        profile_example = QLabel("Example: rotator_features_<suffix>.h")
        profile_example.setStyleSheet("color: #666; font-size: 9pt;")
        profile_layout.addWidget(profile_example)

        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        # Output directory selection
        dir_group = QGroupBox("Output Directory")
        dir_layout = QHBoxLayout()

        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select directory...")
        self.dir_input.setReadOnly(True)

        # Set default directory to K3NG rotator controller directory if available
        if self.config_manager.paths:
            default_dir = self.config_manager.paths.features_file.parent
            self.dir_input.setText(str(default_dir))

        dir_layout.addWidget(self.dir_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)

        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.backup_checkbox = QCheckBox("Create backups of existing files")
        self.backup_checkbox.setChecked(True)
        options_layout.addWidget(self.backup_checkbox)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Results area
        results_label = QLabel("<b>Export Results:</b>")
        layout.addWidget(results_label)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 9))
        self.results_text.setMaximumHeight(150)
        self.results_text.setPlaceholderText("Export results will appear here...")
        layout.addWidget(self.results_text)

        # Button box
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._perform_export)
        self.export_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _on_mode_changed(self):
        """Handle export mode change"""
        is_new_profile = self.new_profile_radio.isChecked()
        self.profile_input.setEnabled(is_new_profile)

        # Backup only makes sense for modify existing mode
        self.backup_checkbox.setEnabled(self.modify_existing_radio.isChecked())

    def _browse_directory(self):
        """Open directory browser"""
        current_dir = self.dir_input.text() or str(Path.home())

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir
        )

        if directory:
            self.dir_input.setText(directory)

    def _perform_export(self):
        """Perform the export operation"""
        # Validate inputs
        output_dir = Path(self.dir_input.text())

        if not output_dir or not output_dir.exists():
            QMessageBox.warning(
                self,
                "Invalid Directory",
                "Please select a valid output directory."
            )
            return

        # Determine mode
        if self.new_profile_radio.isChecked():
            mode = ExportMode.NEW_PROFILE
            profile_suffix = self.profile_input.text().strip()

            if not profile_suffix:
                QMessageBox.warning(
                    self,
                    "Missing Profile Name",
                    "Please enter a profile suffix for the new profile mode."
                )
                return

            # Validate profile suffix (should be alphanumeric with underscores)
            if not profile_suffix.replace('_', '').isalnum():
                QMessageBox.warning(
                    self,
                    "Invalid Profile Name",
                    "Profile suffix should contain only letters, numbers, and underscores."
                )
                return

            profile_suffix = f"_{profile_suffix}"
        else:
            mode = ExportMode.MODIFY_EXISTING
            profile_suffix = ""

        create_backup = self.backup_checkbox.isChecked()

        # Confirm overwrite if modifying existing
        if mode == ExportMode.MODIFY_EXISTING:
            reply = QMessageBox.question(
                self,
                "Confirm Overwrite",
                "This will overwrite existing configuration files in:\n\n"
                f"{output_dir}\n\n"
                f"{'Backups will be created.' if create_backup else 'No backups will be created.'}\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # Perform export
        self.results_text.clear()
        self.results_text.append("Exporting configuration...\n")
        self.export_btn.setEnabled(False)

        try:
            result = self.export_manager.export(
                output_dir,
                self.config_manager.features_config,
                self.config_manager.pins_config,
                self.config_manager.settings_config,
                mode=mode,
                profile_suffix=profile_suffix,
                create_backup=create_backup
            )

            # Display results
            self.results_text.append(str(result))

            if result.success:
                self.results_text.append("\n" + "="*50)
                self.results_text.append("✓ Export completed successfully!")

                # Emit signal
                self.export_completed.emit(result)

                # Show success message
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Configuration exported successfully!\n\n"
                    f"{len(result.files_written)} files written to:\n{output_dir}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    "Export failed. See results for details."
                )

        except Exception as e:
            self.results_text.append(f"\n✗ Export failed: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export:\n\n{str(e)}"
            )
        finally:
            self.export_btn.setEnabled(True)

    def get_last_export_dir(self) -> str:
        """Get the last selected export directory"""
        return self.dir_input.text()
