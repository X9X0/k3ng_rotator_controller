"""
K3NG Configuration Tool - Main Window
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QLabel,
    QStatusBar, QMenuBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from pathlib import Path
import sys

from core.config_manager import ConfigurationManager, ConfigurationPaths
from gui.widgets.feature_selector import FeatureSelectorWidget
from gui.widgets.pin_configurator import PinConfiguratorWidget
from gui.widgets.settings_editor import SettingsEditorWidget
from gui.widgets.serial_console import SerialConsoleWidget
from gui.widgets.test_runner_widget import TestRunnerWidget
from gui.dialogs.export_dialog import ExportDialog


class MainWindow(QMainWindow):
    """Main application window for K3NG Configuration Tool"""

    # Signals
    configuration_loaded = pyqtSignal(ConfigurationManager)
    configuration_saved = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.config_manager = None
        self.project_dir = None
        self.unsaved_changes = False

        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()

    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("K3NG Rotator Configuration Tool")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget with horizontal splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for navigation and content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Navigation tree
        self.nav_tree = self._create_navigation_tree()
        splitter.addWidget(self.nav_tree)

        # Right side: Content area (stacked widget for different panels)
        self.content_stack = QStackedWidget()
        self._create_content_panels()
        splitter.addWidget(self.content_stack)

        # Set initial splitter sizes (navigation: 250px, content: rest)
        splitter.setSizes([250, 1150])

        layout.addWidget(splitter)

    def _create_navigation_tree(self):
        """Create the navigation tree widget"""
        tree = QTreeWidget()
        tree.setHeaderLabel("Navigation")
        tree.setMinimumWidth(200)
        tree.setMaximumWidth(350)

        # Create navigation items
        items = [
            ("Hardware", [
                "Board Selection",
                "Pin Configuration"
            ]),
            ("Features", [
                "Protocol Emulation",
                "Position Sensors",
                "Display",
                "Tracking",
                "I2C Devices",
                "Communication",
                "Ancillary"
            ]),
            ("Settings", [
                "Motor Control",
                "Calibration",
                "Limits",
                "Timing",
                "Other"
            ]),
            ("Validation", []),
            ("Serial Console", []),
            ("Testing", [
                "I/O Tests",
                "Motor Tests",
                "Sensor Tests"
            ]),
            ("Calibration", [
                "Magnetometer",
                "Angular Correction"
            ])
        ]

        self.nav_items = {}

        for parent_text, children in items:
            parent_item = QTreeWidgetItem([parent_text])
            tree.addTopLevelItem(parent_item)
            self.nav_items[parent_text] = parent_item

            for child_text in children:
                child_item = QTreeWidgetItem([child_text])
                parent_item.addChild(child_item)
                self.nav_items[f"{parent_text}/{child_text}"] = child_item

        # Expand all by default
        tree.expandAll()

        # Connect selection change
        tree.currentItemChanged.connect(self._on_navigation_changed)

        return tree

    def _create_content_panels(self):
        """Create content panels for the stacked widget"""
        # Keep track of panel indices
        self.panel_indices = {}

        # Welcome panel (index 0)
        welcome_panel = self._create_welcome_panel()
        self.content_stack.addWidget(welcome_panel)
        self.panel_indices["Welcome"] = 0

        # Hardware section - Pin configurator
        self.pin_configurator = PinConfiguratorWidget()
        self.pin_configurator.pin_changed.connect(self._on_pin_changed)
        self.content_stack.addWidget(self.pin_configurator)
        self.panel_indices["Hardware"] = self.content_stack.count() - 1

        # Feature selector
        self.feature_selector = FeatureSelectorWidget()
        self.feature_selector.feature_changed.connect(self._on_feature_changed)
        self.content_stack.addWidget(self.feature_selector)
        self.panel_indices["Features"] = self.content_stack.count() - 1

        # Settings editor
        self.settings_editor = SettingsEditorWidget()
        self.settings_editor.setting_changed.connect(self._on_setting_changed)
        self.content_stack.addWidget(self.settings_editor)
        self.panel_indices["Settings"] = self.content_stack.count() - 1

        # Serial console
        self.serial_console = SerialConsoleWidget()
        self.serial_console.connected.connect(self._on_serial_connected)
        self.serial_console.disconnected.connect(self._on_serial_disconnected)
        self.content_stack.addWidget(self.serial_console)
        self.panel_indices["Serial Console"] = self.content_stack.count() - 1

        # Test runner widget
        self.test_runner = TestRunnerWidget()
        self.content_stack.addWidget(self.test_runner)
        self.panel_indices["Testing"] = self.content_stack.count() - 1

        # Placeholder panels for other sections
        for section in ["Validation", "Calibration"]:
            placeholder = QLabel(f"{section} panel - To be implemented in next phase")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("font-size: 14px; color: #666;")
            self.content_stack.addWidget(placeholder)
            self.panel_indices[section] = self.content_stack.count() - 1

        # Show welcome panel by default
        self.content_stack.setCurrentIndex(0)

    def _create_welcome_panel(self):
        """Create the welcome/start panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Welcome message
        title = QLabel("K3NG Rotator Configuration Tool")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Phase 7 - Testing Framework")
        subtitle.setStyleSheet("font-size: 16px; color: #666; margin-bottom: 40px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Instructions
        instructions = QLabel(
            "To get started:\n\n"
            "1. File → Open Project to load an existing K3NG configuration\n"
            "2. Use the navigation tree on the left to browse configuration sections\n"
            "3. Make changes in the editor panels\n"
            "4. Validate your configuration before generating files\n"
            "5. File → Generate Files to create new configuration headers"
        )
        instructions.setStyleSheet("font-size: 14px; line-height: 1.6;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)

        # Spacer
        layout.addStretch()

        return widget

    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Save Configuration", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_configuration_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        generate_action = QAction("&Generate Files...", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(self.generate_files)
        file_menu.addAction(generate_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        validate_action = QAction("&Validate Configuration", self)
        validate_action.setShortcut("F5")
        validate_action.triggered.connect(self.validate_configuration)
        tools_menu.addAction(validate_action)

        boards_action = QAction("&Board Database...", self)
        boards_action.triggered.connect(self.show_board_database)
        tools_menu.addAction(boards_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status labels
        self.project_label = QLabel("No project loaded")
        self.board_label = QLabel("Board: None")
        self.validation_label = QLabel("Validation: Not run")

        self.status_bar.addWidget(self.project_label)
        self.status_bar.addPermanentWidget(self.board_label)
        self.status_bar.addPermanentWidget(self.validation_label)

        self.status_bar.showMessage("Ready")

    def _on_navigation_changed(self, current, previous):
        """Handle navigation tree selection change"""
        if current is None:
            return

        item_text = current.text(0)
        parent = current.parent()

        # Determine which panel to show
        section = parent.text(0) if parent else item_text

        # Switch to appropriate panel
        if section in self.panel_indices:
            self.content_stack.setCurrentIndex(self.panel_indices[section])
            self.status_bar.showMessage(f"Viewing: {section}")
        else:
            # Child item selected - still show parent's panel
            full_path = f"{parent.text(0)}/{item_text}" if parent else item_text
            self.status_bar.showMessage(f"Selected: {full_path}")

    def _on_feature_changed(self, feature_name: str, is_active: bool):
        """Handle feature checkbox change"""
        # Mark configuration as having unsaved changes
        self.unsaved_changes = True

        # Update window title to indicate unsaved changes
        if "*" not in self.windowTitle():
            self.setWindowTitle(self.windowTitle() + " *")

        # Clear validation status since config changed
        self.validation_label.setText("Validation: Not run")

        status = "enabled" if is_active else "disabled"
        self.status_bar.showMessage(f"Feature {feature_name} {status}", 3000)

    def _on_pin_changed(self, pin_name: str, new_value: str):
        """Handle pin value change"""
        # Mark configuration as having unsaved changes
        self.unsaved_changes = True

        # Update window title to indicate unsaved changes
        if "*" not in self.windowTitle():
            self.setWindowTitle(self.windowTitle() + " *")

        # Clear validation status since config changed
        self.validation_label.setText("Validation: Not run")

        self.status_bar.showMessage(f"Pin {pin_name} set to {new_value}", 3000)

    def _on_setting_changed(self, setting_name: str, new_value):
        """Handle setting value change"""
        # Mark configuration as having unsaved changes
        self.unsaved_changes = True

        # Update window title to indicate unsaved changes
        if "*" not in self.windowTitle():
            self.setWindowTitle(self.windowTitle() + " *")

        # Clear validation status since config changed
        self.validation_label.setText("Validation: Not run")

        self.status_bar.showMessage(f"Setting {setting_name} = {new_value}", 3000)

    def _on_serial_connected(self, port: str):
        """Handle serial connection established"""
        self.status_bar.showMessage(f"Connected to {port}", 5000)

        # Update test runner with command interface
        if hasattr(self, 'test_runner'):
            command_interface = self.serial_console.get_command_interface()
            self.test_runner.set_command_interface(command_interface)

    def _on_serial_disconnected(self):
        """Handle serial disconnection"""
        self.status_bar.showMessage("Disconnected from serial port", 3000)

    def open_project(self):
        """Open a K3NG project directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select K3NG Project Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if not directory:
            return

        self.load_project(Path(directory))

    def load_project(self, project_dir: Path):
        """Load a K3NG project"""
        try:
            paths = ConfigurationPaths.from_project_dir(project_dir)
            self.config_manager = ConfigurationManager(paths)

            if not self.config_manager.load():
                QMessageBox.critical(
                    self,
                    "Load Error",
                    "Failed to load configuration from project directory"
                )
                return

            self.project_dir = project_dir
            self.project_label.setText(f"Project: {project_dir.name}")
            self.status_bar.showMessage(f"Loaded project from {project_dir}", 5000)

            # Load features into feature selector
            self.feature_selector.load_features(self.config_manager.features_config)

            # Load pins into pin configurator
            self.pin_configurator.load_pins(self.config_manager.pins_config)

            # Load settings into settings editor
            self.settings_editor.load_settings(self.config_manager.settings_config)

            # Emit signal
            self.configuration_loaded.emit(self.config_manager)

            # Update status
            summary = self.config_manager.get_summary()
            self.validation_label.setText("Validation: Not run")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Error loading project: {str(e)}"
            )

    def save_configuration(self):
        """Save the current configuration"""
        if not self.config_manager or not self.project_dir:
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded. Use 'Open Project' first."
            )
            return

        # Confirm save
        reply = QMessageBox.question(
            self,
            "Save Configuration",
            "This will generate configuration files back to the project directory.\n"
            "Backup files (.bak) will be created automatically.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Generate files with backup
            generated_files = self.config_manager.generate_to_project(backup=True)

            # Clear unsaved changes
            self.unsaved_changes = False
            self.setWindowTitle("K3NG Rotator Configuration Tool")

            # Update status
            self.status_bar.showMessage("Configuration saved successfully", 5000)

            # Show success dialog
            files_list = "\n".join([f"  • {f.name}" for f in generated_files[:5]])
            if len(generated_files) > 5:
                files_list += f"\n  ... and {len(generated_files) - 5} more"

            QMessageBox.information(
                self,
                "Save Successful",
                f"Configuration files generated successfully:\n\n{files_list}\n\n"
                f"Backup files (.bak) have been created."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save configuration:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Save failed", 3000)

    def save_configuration_as(self):
        """Save configuration to a new location"""
        if not self.config_manager:
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded. Use 'Open Project' first."
            )
            return

        # Get output directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if not directory:
            return

        output_dir = Path(directory)

        try:
            # Generate files to custom directory
            generated_files = self.config_manager.generate_files(str(output_dir))

            # Update status
            self.status_bar.showMessage(f"Configuration saved to {output_dir}", 5000)

            # Show success dialog
            files_list = "\n".join([f"  • {f.name}" for f in generated_files[:5]])
            if len(generated_files) > 5:
                files_list += f"\n  ... and {len(generated_files) - 5} more"

            QMessageBox.information(
                self,
                "Save As Successful",
                f"Configuration files generated to:\n{output_dir}\n\n{files_list}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save As Error",
                f"Failed to save configuration:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Save as failed", 3000)

    def generate_files(self):
        """Generate configuration .h files"""
        if not self.config_manager:
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded. Use 'Open Project' first."
            )
            return

        # Open export dialog
        dialog = ExportDialog(self.config_manager, self)
        dialog.export_completed.connect(self._on_export_completed)
        dialog.exec()

    def _on_export_completed(self, result):
        """Handle export completion"""
        self.status_bar.showMessage(f"Export completed: {len(result.files_written)} files written", 5000)

    def validate_configuration(self):
        """Validate the current configuration"""
        if not self.config_manager:
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded. Use 'Open Project' first."
            )
            return

        result = self.config_manager.validate()

        if result.passed:
            self.validation_label.setText("Validation: ✓ Passed")
            QMessageBox.information(
                self,
                "Validation Passed",
                "Configuration is valid!"
            )
        else:
            self.validation_label.setText(f"Validation: ✗ {len(result.errors)} errors")
            error_text = "\n\n".join([f"{i+1}. {e.message}" for i, e in enumerate(result.errors[:5])])
            if len(result.errors) > 5:
                error_text += f"\n\n... and {len(result.errors) - 5} more errors"

            QMessageBox.warning(
                self,
                "Validation Failed",
                f"Configuration has {len(result.errors)} error(s):\n\n{error_text}"
            )

    def show_board_database(self):
        """Show board database dialog"""
        # TODO: Implement board database dialog
        QMessageBox.information(
            self,
            "Board Database",
            "Board database viewer (not yet implemented)"
        )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About K3NG Configuration Tool",
            "<h3>K3NG Rotator Configuration & Testing Utility</h3>"
            "<p>Phase 7 - Testing Framework</p>"
            "<p>A comprehensive tool for configuring and testing K3NG rotator controllers.</p>"
            "<p>Built with PyQt6 and PySerial</p>"
        )

    def closeEvent(self, event):
        """Handle window close event"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to exit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Cleanup serial console
        if hasattr(self, 'serial_console'):
            self.serial_console.cleanup()

        event.accept()
