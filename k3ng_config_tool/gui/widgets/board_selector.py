"""
K3NG Configuration Tool - Board Selector Widget
Select Arduino board for pin validation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional

from ...boards.board_database import BoardDatabase, BoardDefinition


class BoardSelectorWidget(QWidget):
    """
    Board selector widget

    Allows user to select Arduino board for pin validation
    and displays board specifications.
    """

    # Signals
    board_selected = pyqtSignal(str)  # board_id

    def __init__(self, parent=None):
        """Initialize board selector"""
        super().__init__(parent)
        self.board_db = BoardDatabase()
        self.selected_board: Optional[BoardDefinition] = None
        self._init_ui()
        self._load_boards()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Arduino Board Selection")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        # Description
        desc = QLabel(
            "Select your Arduino board for automatic pin validation. "
            "The tool will check for PWM capability, interrupt pins, "
            "analog pins, and detect pin conflicts."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Main content layout
        content_layout = QHBoxLayout()

        # Left side - Board list
        list_group = QGroupBox("Available Boards")
        list_layout = QVBoxLayout(list_group)

        self.board_list = QListWidget()
        self.board_list.currentItemChanged.connect(self._on_board_list_selection)
        list_layout.addWidget(self.board_list)

        # Select button
        self.select_btn = QPushButton("Select This Board")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self._on_select_clicked)
        self.select_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:enabled:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                padding: 10px;
                border-radius: 4px;
            }
        """)
        list_layout.addWidget(self.select_btn)

        content_layout.addWidget(list_group, 1)

        # Right side - Board details
        details_group = QGroupBox("Board Specifications")
        details_layout = QVBoxLayout(details_group)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select a board to view specifications...")
        details_layout.addWidget(self.details_text)

        content_layout.addWidget(details_group, 1)

        layout.addLayout(content_layout)

        # Current selection indicator
        self.current_label = QLabel("Current Board: None selected")
        self.current_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.current_label)

    def _load_boards(self):
        """Load available boards into list"""
        boards = self.board_db.get_all_boards()

        for board in boards:
            item = QListWidgetItem(board.board_name)
            item.setData(Qt.ItemDataRole.UserRole, board.board_id)

            # Add icon/indicator for recommended boards
            if 'mega' in board.board_id.lower():
                item.setText(f"⭐ {board.board_name} (Recommended)")

            self.board_list.addItem(item)

    def _on_board_list_selection(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle board list selection change"""
        if not current:
            self.select_btn.setEnabled(False)
            self.details_text.clear()
            return

        # Get board ID from item
        board_id = current.data(Qt.ItemDataRole.UserRole)

        # Load board details
        board = self.board_db.get_board(board_id)
        if not board:
            return

        # Enable select button
        self.select_btn.setEnabled(True)

        # Display board details
        details = self._format_board_details(board)
        self.details_text.setHtml(details)

    def _format_board_details(self, board: BoardDefinition) -> str:
        """Format board details as HTML"""
        # Extract pin information from the board definition
        digital_count = board.pins['digital']['count']
        digital_range = board.pins['digital']['range']
        analog_count = board.pins['analog']['count']
        analog_names = board.pins['analog']['names']
        pwm_pins = board.pins.get('pwm', [])
        interrupt_pins = board.pins.get('interrupt', {})
        i2c = board.pins.get('i2c', {})
        serial_ports = board.pins.get('serial', [])

        html = f"""
        <h2>{board.board_name}</h2>
        <p><strong>Board ID:</strong> {board.board_id}</p>
        <p><strong>MCU:</strong> {board.mcu}</p>
        <p><strong>Description:</strong> {board.description}</p>

        <h3>Pin Capabilities</h3>
        <table style='width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #f0f0f0;'>
                <th style='padding: 5px; text-align: left;'>Type</th>
                <th style='padding: 5px; text-align: left;'>Count</th>
                <th style='padding: 5px; text-align: left;'>Details</th>
            </tr>
            <tr>
                <td style='padding: 5px;'><strong>Digital Pins</strong></td>
                <td style='padding: 5px;'>{digital_count}</td>
                <td style='padding: 5px;'>Pins {digital_range[0]}-{digital_range[1]}</td>
            </tr>
            <tr style='background-color: #f9f9f9;'>
                <td style='padding: 5px;'><strong>Analog Pins</strong></td>
                <td style='padding: 5px;'>{analog_count}</td>
                <td style='padding: 5px;'>{analog_names[0]} to {analog_names[-1]}</td>
            </tr>
            <tr>
                <td style='padding: 5px;'><strong>PWM Pins</strong></td>
                <td style='padding: 5px;'>{len(pwm_pins)}</td>
                <td style='padding: 5px;'>{', '.join(map(str, pwm_pins[:10]))}{', ...' if len(pwm_pins) > 10 else ''}</td>
            </tr>
            <tr style='background-color: #f9f9f9;'>
                <td style='padding: 5px;'><strong>Interrupt Pins</strong></td>
                <td style='padding: 5px;'>{len(interrupt_pins)}</td>
                <td style='padding: 5px;'>{', '.join(f'Pin {pin} (INT{num})' for pin, num in list(interrupt_pins.items())[:5])}</td>
            </tr>
        </table>

        <h3>Communication</h3>
        <p><strong>I2C:</strong> SDA=Pin {i2c.get('sda', 'N/A')}, SCL=Pin {i2c.get('scl', 'N/A')}</p>
        <p><strong>Serial Ports:</strong> {len(serial_ports)} available</p>

        <h3>Why Select This Board?</h3>
        <p>Selecting the correct board enables:</p>
        <ul>
            <li>✅ Automatic PWM pin validation for speed control</li>
            <li>✅ Interrupt pin checking for pulse inputs</li>
            <li>✅ Analog pin verification for potentiometers</li>
            <li>✅ Pin conflict detection</li>
            <li>✅ Board-specific warnings and suggestions</li>
        </ul>
        """

        return html

    def _on_select_clicked(self):
        """Handle select button click"""
        current_item = self.board_list.currentItem()
        if not current_item:
            return

        board_id = current_item.data(Qt.ItemDataRole.UserRole)
        board = self.board_db.get_board(board_id)

        if not board:
            QMessageBox.warning(
                self,
                "Board Not Found",
                f"Could not load board: {board_id}"
            )
            return

        # Update current selection
        self.selected_board = board
        self.current_label.setText(f"Current Board: {board.board_name}")
        self.current_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                font-weight: bold;
                color: #155724;
            }
        """)

        # Emit signal
        self.board_selected.emit(board_id)

        # Show confirmation
        QMessageBox.information(
            self,
            "Board Selected",
            f"✅ Board selected: {board.board_name}\n\n"
            f"Pin validation will now use {board.board_name} specifications.\n"
            f"Navigate to 'Pin Configuration' to assign pins."
        )

    def set_board(self, board_id: str):
        """Set board programmatically"""
        board = self.board_db.get_board(board_id)
        if not board:
            return

        # Find and select item in list
        for i in range(self.board_list.count()):
            item = self.board_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == board_id:
                self.board_list.setCurrentItem(item)
                break

        # Update selection
        self.selected_board = board
        self.current_label.setText(f"Current Board: {board.board_name}")
        self.current_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                font-weight: bold;
                color: #155724;
            }
        """)

    def get_selected_board(self) -> Optional[BoardDefinition]:
        """Get currently selected board"""
        return self.selected_board
