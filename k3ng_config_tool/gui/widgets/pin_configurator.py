"""
K3NG Configuration Tool - Pin Configurator Widget
Displays and edits pin assignments in a table view
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from typing import Optional

from parsers.pin_parser import PinConfig, PinDefinition
from boards.board_database import BoardDefinition


class PinItem(QTreeWidgetItem):
    """Custom tree widget item for a pin"""

    def __init__(self, pin_name: str, pin_def: PinDefinition, parent=None):
        super().__init__(parent)
        self.pin_name = pin_name
        self.pin_def = pin_def

        # Column 0: Pin name
        self.setText(0, pin_name)

        # Column 1: Pin value (editable)
        self.setText(1, pin_def.pin_string)

        # Column 2: Description/comment
        if pin_def.comment:
            self.setText(2, pin_def.comment)

        # Set tooltip
        tooltip = f"{pin_name}: {pin_def.pin_string}"
        if pin_def.comment:
            tooltip += f"\n{pin_def.comment}"
        self.setToolTip(0, tooltip)
        self.setToolTip(1, tooltip)

        # Make pin value editable
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)

        # Color disabled pins differently
        if pin_def.is_disabled:
            self.setForeground(0, QBrush(QColor(128, 128, 128)))
            self.setForeground(1, QBrush(QColor(128, 128, 128)))
            self.setForeground(2, QBrush(QColor(128, 128, 128)))

    def update_value(self, new_value: str):
        """Update the pin value"""
        self.setText(1, new_value)
        self.pin_def.pin_string = new_value

        # Update disabled status
        self.pin_def.is_disabled = (new_value == "0")

        # Update color
        if self.pin_def.is_disabled:
            self.setForeground(0, QBrush(QColor(128, 128, 128)))
            self.setForeground(1, QBrush(QColor(128, 128, 128)))
            self.setForeground(2, QBrush(QColor(128, 128, 128)))
        else:
            self.setForeground(0, QBrush(QColor(0, 0, 0)))
            self.setForeground(1, QBrush(QColor(0, 0, 0)))
            self.setForeground(2, QBrush(QColor(0, 0, 0)))


class PinConfiguratorWidget(QWidget):
    """Widget for configuring pin assignments"""

    # Signals
    pin_changed = pyqtSignal(str, str)  # pin_name, new_value
    pins_loaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pin_config = None
        self.pin_items = {}  # pin_name -> PinItem
        self.group_items = {}  # group_name -> QTreeWidgetItem
        self.selected_board: Optional[BoardDefinition] = None

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Pin Configuration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Search/filter box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter pins...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Quick filters
        filter_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("Show All")
        self.show_assigned_btn = QPushButton("Assigned Only")
        self.show_disabled_btn = QPushButton("Disabled Only")

        self.show_all_btn.clicked.connect(lambda: self._filter_view("all"))
        self.show_assigned_btn.clicked.connect(lambda: self._filter_view("assigned"))
        self.show_disabled_btn.clicked.connect(lambda: self._filter_view("disabled"))

        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_assigned_btn)
        filter_layout.addWidget(self.show_disabled_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Pin tree
        self.pin_tree = QTreeWidget()
        self.pin_tree.setHeaderLabels(["Pin Name", "Value", "Description"])
        self.pin_tree.setAlternatingRowColors(True)
        self.pin_tree.setColumnWidth(0, 300)
        self.pin_tree.setColumnWidth(1, 100)
        self.pin_tree.setColumnWidth(2, 400)
        self.pin_tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.pin_tree)

        # Help text
        help_text = QLabel(
            "💡 Tip: Double-click a pin value to edit. Set to 0 to disable a pin. "
            "Common values: 0-53 (digital), A0-A15 (analog)"
        )
        help_text.setStyleSheet("padding: 5px; background-color: #ffffcc; border: 1px solid #cccc00;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        # Statistics
        self.stats_label = QLabel("No pins loaded")
        self.stats_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.stats_label)

    def load_pins(self, pin_config: PinConfig):
        """Load pins from configuration"""
        self.pin_config = pin_config

        # Block signals while updating
        self.pin_tree.blockSignals(True)

        # Clear existing items
        self.pin_tree.clear()
        self.pin_items.clear()
        self.group_items.clear()

        # Create group items and pin items
        for group in pin_config.groups:
            # Create group item
            group_item = QTreeWidgetItem([group.name, "", ""])
            group_item.setExpanded(True)
            group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            group_item.setBackground(0, QBrush(QColor(230, 230, 250)))
            group_item.setBackground(1, QBrush(QColor(230, 230, 250)))
            group_item.setBackground(2, QBrush(QColor(230, 230, 250)))
            self.pin_tree.addTopLevelItem(group_item)
            self.group_items[group.name] = group_item

            # Add pins to group
            for pin_name in group.pins:
                if pin_name in pin_config.pins:
                    pin_def = pin_config.pins[pin_name]
                    pin_item = PinItem(pin_name, pin_def, group_item)
                    self.pin_items[pin_name] = pin_item

        # Re-enable signals
        self.pin_tree.blockSignals(False)

        # Update statistics
        self._update_statistics()

        # Emit loaded signal
        self.pins_loaded.emit()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle pin value change"""
        if not isinstance(item, PinItem):
            return

        # Only handle changes to column 1 (value)
        if column != 1:
            return

        # Get new value
        new_value = item.text(1).strip()

        # Validate pin value
        if not self._validate_pin_value(new_value):
            # Revert to old value
            item.setText(1, item.pin_def.pin_string)
            return

        # Update pin config
        if self.pin_config:
            pin_name = item.pin_name
            old_value = item.pin_def.pin_string

            # Update the pin item
            item.update_value(new_value)

            # Emit change signal
            self.pin_changed.emit(pin_name, new_value)

            # Update statistics
            self._update_statistics()

    def _validate_pin_value(self, value: str) -> bool:
        """Validate a pin value"""
        if not value:
            return False

        # Allow 0 (disabled)
        if value == "0":
            return True

        # Allow digital pins (numeric)
        try:
            pin_num = int(value)
            # Most Arduino boards have pins 0-99
            return 0 <= pin_num <= 99
        except ValueError:
            pass

        # Allow analog pins (A0-A15)
        if value.startswith("A") or value.startswith("a"):
            try:
                analog_num = int(value[1:])
                return 0 <= analog_num <= 15
            except ValueError:
                return False

        # Allow remote unit pins (100+)
        try:
            pin_num = int(value)
            return 100 <= pin_num <= 200
        except ValueError:
            pass

        return False

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        search_text = text.lower()

        for pin_name, item in self.pin_items.items():
            # Check if pin matches search
            matches = (
                search_text in pin_name.lower() or
                search_text in item.pin_def.pin_string.lower() or
                (item.pin_def.comment and search_text in item.pin_def.comment.lower())
            )

            # Show/hide item
            item.setHidden(not matches)

        # Show/hide groups based on visible children
        for group_name, group_item in self.group_items.items():
            has_visible_children = False
            for i in range(group_item.childCount()):
                if not group_item.child(i).isHidden():
                    has_visible_children = True
                    break

            group_item.setHidden(not has_visible_children)

    def _filter_view(self, filter_type: str):
        """Filter view to show all/assigned/disabled pins"""
        for pin_name, item in self.pin_items.items():
            if filter_type == "all":
                item.setHidden(False)
            elif filter_type == "assigned":
                item.setHidden(item.pin_def.is_disabled)
            elif filter_type == "disabled":
                item.setHidden(not item.pin_def.is_disabled)

        # Show/hide groups
        for group_name, group_item in self.group_items.items():
            has_visible_children = False
            for i in range(group_item.childCount()):
                if not group_item.child(i).isHidden():
                    has_visible_children = True
                    break

            group_item.setHidden(not has_visible_children)

    def _update_statistics(self):
        """Update the statistics label"""
        if not self.pin_config:
            self.stats_label.setText("No pins loaded")
            return

        total = len(self.pin_config.pins)
        assigned = sum(1 for p in self.pin_config.pins.values() if not p.is_disabled)
        disabled = total - assigned

        self.stats_label.setText(
            f"Pins: {assigned}/{total} assigned ({disabled} disabled)"
        )

    def highlight_conflicts(self, conflicting_pins: list):
        """Highlight pins that have conflicts"""
        for pin_name in conflicting_pins:
            if pin_name in self.pin_items:
                item = self.pin_items[pin_name]
                # Set red background for conflicting pins
                item.setBackground(0, QBrush(QColor(255, 200, 200)))
                item.setBackground(1, QBrush(QColor(255, 200, 200)))
                item.setBackground(2, QBrush(QColor(255, 200, 200)))

    def clear_highlights(self):
        """Clear all conflict highlights"""
        for item in self.pin_items.values():
            item.setBackground(0, QBrush(Qt.GlobalColor.white))
            item.setBackground(1, QBrush(Qt.GlobalColor.white))
            item.setBackground(2, QBrush(Qt.GlobalColor.white))

    def get_pin_value(self, pin_name: str) -> str:
        """Get the current value of a pin"""
        if pin_name in self.pin_items:
            return self.pin_items[pin_name].pin_def.pin_string
        return ""

    def set_pin_value(self, pin_name: str, value: str):
        """Programmatically set a pin value"""
        if pin_name in self.pin_items and self._validate_pin_value(value):
            item = self.pin_items[pin_name]
            self.pin_tree.blockSignals(True)
            item.update_value(value)
            self.pin_tree.blockSignals(False)
            self._update_statistics()

    def set_board(self, board: BoardDefinition):
        """Set the Arduino board for pin validation"""
        self.selected_board = board

        # Future enhancement: Validate current pins against board capabilities
        # and highlight any pins that are invalid for the selected board
        # For now, just store the board reference
