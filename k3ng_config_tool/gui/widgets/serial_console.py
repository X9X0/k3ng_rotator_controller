"""
K3NG Configuration Tool - Serial Console Widget
Provides serial terminal interface for K3NG controllers
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QComboBox, QLabel, QGroupBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat
from datetime import datetime

from serial.serial_manager import SerialManager, SerialPort
from serial.command_interface import K3NGCommandInterface


class SerialConsoleWidget(QWidget):
    """Widget for serial communication console"""

    # Signals
    connected = pyqtSignal(str)  # port
    disconnected = pyqtSignal()
    command_sent = pyqtSignal(str)  # command

    def __init__(self, parent=None):
        super().__init__(parent)

        # Serial components
        self.serial_manager = SerialManager()
        self.command_interface = K3NGCommandInterface(self.serial_manager)

        # Command history
        self.command_history = []
        self.history_index = -1

        # Connect signals
        self.serial_manager.connected.connect(self._on_connected)
        self.serial_manager.disconnected.connect(self._on_disconnected)
        self.serial_manager.data_received.connect(self._on_data_received)
        self.serial_manager.error_occurred.connect(self._on_error)
        self.command_interface.command_sent.connect(self._on_command_sent)

        self._init_ui()
        self._update_port_list()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Serial Console")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Connection settings group
        connection_group = QGroupBox("Connection Settings")
        connection_layout = QHBoxLayout()

        # Port selection
        port_label = QLabel("Port:")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        connection_layout.addWidget(port_label)
        connection_layout.addWidget(self.port_combo)

        # Baud rate
        baud_label = QLabel("Baud:")
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(300, 115200)
        self.baud_spin.setValue(9600)
        self.baud_spin.setSingleStep(100)
        connection_layout.addWidget(baud_label)
        connection_layout.addWidget(self.baud_spin)

        # Refresh ports button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._update_port_list)
        connection_layout.addWidget(self.refresh_btn)

        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._toggle_connection)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        connection_layout.addWidget(self.connect_btn)

        connection_layout.addStretch()
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)

        # Console output
        console_layout = QVBoxLayout()

        # Toolbar
        toolbar_layout = QHBoxLayout()

        # Timestamp checkbox
        self.timestamp_check = QCheckBox("Timestamps")
        self.timestamp_check.setChecked(True)
        toolbar_layout.addWidget(self.timestamp_check)

        # Auto-scroll checkbox
        self.autoscroll_check = QCheckBox("Auto-scroll")
        self.autoscroll_check.setChecked(True)
        toolbar_layout.addWidget(self.autoscroll_check)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_console)
        toolbar_layout.addWidget(clear_btn)

        # Save log button
        save_log_btn = QPushButton("Save Log")
        save_log_btn.clicked.connect(self._save_log)
        toolbar_layout.addWidget(save_log_btn)

        toolbar_layout.addStretch()
        console_layout.addLayout(toolbar_layout)

        # Console text area
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setStyleSheet(
            "font-family: 'Courier New', monospace; "
            "font-size: 10pt; "
            "background-color: #1e1e1e; "
            "color: #d4d4d4;"
        )
        console_layout.addWidget(self.console_text)

        layout.addLayout(console_layout)

        # Command input
        input_layout = QHBoxLayout()

        # Command templates dropdown
        self.template_combo = QComboBox()
        self.template_combo.addItem("-- Quick Commands --")
        self.template_combo.addItem("Query Azimuth (\\?AZ)")
        self.template_combo.addItem("Query Elevation (\\?EL)")
        self.template_combo.addItem("Query Version (\\?CV)")
        self.template_combo.addItem("Calibration Status (\\?CAL)")
        self.template_combo.addItem("Calibration Quality (\\?CQ)")
        self.template_combo.addItem("Stop Rotation (S)")
        self.template_combo.addItem("Rotate CW (R)")
        self.template_combo.addItem("Rotate CCW (L)")
        self.template_combo.addItem("Rotate Up (U)")
        self.template_combo.addItem("Rotate Down (D)")
        self.template_combo.addItem("Help (H)")
        self.template_combo.currentTextChanged.connect(self._on_template_selected)
        input_layout.addWidget(self.template_combo)

        # Command input field
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command (e.g., \\?AZ, S, M180, etc.)")
        self.command_input.returnPressed.connect(self._send_command)
        input_layout.addWidget(self.command_input)

        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_command)
        self.send_btn.setEnabled(False)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # Status
        self.status_label = QLabel("Not connected")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)

    def _update_port_list(self):
        """Update the list of available serial ports"""
        current_port = self.port_combo.currentText()

        self.port_combo.clear()

        ports = self.serial_manager.list_ports()

        if not ports:
            self.port_combo.addItem("No ports found")
            self.connect_btn.setEnabled(False)
        else:
            for port in ports:
                self.port_combo.addItem(f"{port.device} - {port.description}", port.device)

            # Try to select previously selected port
            if current_port:
                index = self.port_combo.findText(current_port, Qt.MatchFlag.MatchStartsWith)
                if index >= 0:
                    self.port_combo.setCurrentIndex(index)

            self.connect_btn.setEnabled(True)

    def _toggle_connection(self):
        """Toggle serial connection"""
        if self.serial_manager.is_connected:
            self.serial_manager.disconnect()
        else:
            port = self.port_combo.currentData()
            if not port:
                port = self.port_combo.currentText().split(' -')[0]

            baud = self.baud_spin.value()
            self.serial_manager.connect(port, baud)

    def _on_connected(self, port: str):
        """Handle connection established"""
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.send_btn.setEnabled(True)
        self.port_combo.setEnabled(False)
        self.baud_spin.setEnabled(False)
        self.refresh_btn.setEnabled(False)

        self.status_label.setText(f"Connected to {port} at {self.baud_spin.value()} baud")
        self.status_label.setStyleSheet("padding: 5px; background-color: #c8e6c9; color: #2e7d32;")

        self._append_system_message(f"Connected to {port}")
        self.connected.emit(port)

    def _on_disconnected(self):
        """Handle disconnection"""
        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.send_btn.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.baud_spin.setEnabled(True)
        self.refresh_btn.setEnabled(True)

        self.status_label.setText("Not connected")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")

        self._append_system_message("Disconnected")
        self.disconnected.emit()

    def _on_data_received(self, data: str):
        """Handle data received from serial port"""
        self._append_received_message(data)

    def _on_error(self, error: str):
        """Handle serial error"""
        self._append_error_message(error)

    def _on_command_sent(self, command: str):
        """Handle command sent"""
        # Already displayed in _send_command
        pass

    def _send_command(self):
        """Send command from input field"""
        command = self.command_input.text().strip()

        if not command:
            return

        if not self.serial_manager.is_connected:
            self._append_error_message("Not connected to serial port")
            return

        # Add to history
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = len(self.command_history)

        # Display sent command
        self._append_sent_message(command)

        # Send via command interface
        self.command_interface.send_raw(command)

        # Clear input
        self.command_input.clear()

        # Emit signal
        self.command_sent.emit(command)

    def _on_template_selected(self, text: str):
        """Handle template selection"""
        if " (" in text:
            # Extract command from template
            command = text.split("(")[1].split(")")[0]
            self.command_input.setText(command)
            self.command_input.setFocus()

            # Reset combo box
            self.template_combo.setCurrentIndex(0)

    def _append_system_message(self, message: str):
        """Append system message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamp_check.isChecked() else ""

        format = QTextCharFormat()
        format.setForeground(QColor("#808080"))

        if timestamp:
            self._append_text(f"[{timestamp}] ", format)

        format.setForeground(QColor("#9cdcfe"))
        self._append_text(f"[SYSTEM] {message}\n", format)

    def _append_sent_message(self, message: str):
        """Append sent message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamp_check.isChecked() else ""

        format = QTextCharFormat()
        format.setForeground(QColor("#808080"))

        if timestamp:
            self._append_text(f"[{timestamp}] ", format)

        format.setForeground(QColor("#4ec9b0"))
        self._append_text("TX: ", format)

        format.setForeground(QColor("#d4d4d4"))
        self._append_text(f"{message}\n", format)

    def _append_received_message(self, message: str):
        """Append received message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamp_check.isChecked() else ""

        format = QTextCharFormat()
        format.setForeground(QColor("#808080"))

        if timestamp:
            self._append_text(f"[{timestamp}] ", format)

        format.setForeground(QColor("#ce9178"))
        self._append_text("RX: ", format)

        format.setForeground(QColor("#d4d4d4"))
        self._append_text(f"{message}\n", format)

    def _append_error_message(self, message: str):
        """Append error message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamp_check.isChecked() else ""

        format = QTextCharFormat()
        format.setForeground(QColor("#808080"))

        if timestamp:
            self._append_text(f"[{timestamp}] ", format)

        format.setForeground(QColor("#f48771"))
        self._append_text(f"[ERROR] {message}\n", format)

    def _append_text(self, text: str, format: QTextCharFormat):
        """Append formatted text to console"""
        cursor = self.console_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, format)

        # Auto-scroll if enabled
        if self.autoscroll_check.isChecked():
            self.console_text.setTextCursor(cursor)
            self.console_text.ensureCursorVisible()

    def _clear_console(self):
        """Clear console output"""
        self.console_text.clear()
        self._append_system_message("Console cleared")

    def _save_log(self):
        """Save console log to file"""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Console Log",
            str(Path.home() / "k3ng_console.log"),
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.console_text.toPlainText())
                self._append_system_message(f"Log saved to {filename}")
            except Exception as e:
                self._append_error_message(f"Failed to save log: {str(e)}")

    def keyPressEvent(self, event):
        """Handle key press events for command history"""
        if event.key() == Qt.Key.Key_Up:
            # Navigate backwards in history
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key.Key_Down:
            # Navigate forwards in history
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            elif self.history_index >= len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)

    def get_serial_manager(self) -> SerialManager:
        """Get the serial manager instance"""
        return self.serial_manager

    def get_command_interface(self) -> K3NGCommandInterface:
        """Get the command interface instance"""
        return self.command_interface

    def cleanup(self):
        """Cleanup resources"""
        if self.serial_manager.is_connected:
            self.serial_manager.disconnect()
