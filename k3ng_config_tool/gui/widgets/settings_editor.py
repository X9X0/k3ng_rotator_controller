"""
K3NG Configuration Tool - Settings Editor Widget
Displays and edits configuration settings in a tree view
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QLabel, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor

from parsers.settings_parser import SettingsConfig, SettingDefinition


class SettingItem(QTreeWidgetItem):
    """Custom tree widget item for a setting"""

    def __init__(self, setting_name: str, setting_def: SettingDefinition, parent=None):
        super().__init__(parent)
        self.setting_name = setting_name
        self.setting_def = setting_def

        # Column 0: Setting name
        self.setText(0, setting_name)

        # Column 1: Value (editable)
        self.setText(1, str(setting_def.value))

        # Column 2: Unit
        if setting_def.unit:
            self.setText(2, setting_def.unit)

        # Column 3: Description/comment
        if setting_def.comment:
            self.setText(3, setting_def.comment)

        # Set tooltip
        tooltip = f"{setting_name} = {setting_def.value}"
        if setting_def.unit:
            tooltip += f" {setting_def.unit}"
        if setting_def.comment:
            tooltip += f"\n{setting_def.comment}"
        if setting_def.is_eeprom_persistent:
            tooltip += "\n[EEPROM Persistent]"

        self.setToolTip(0, tooltip)
        self.setToolTip(1, tooltip)

        # Make value editable
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)

        # Highlight EEPROM settings
        if setting_def.is_eeprom_persistent:
            self.setBackground(0, QBrush(QColor(255, 255, 220)))
            self.setBackground(1, QBrush(QColor(255, 255, 220)))

    def update_value(self, new_value):
        """Update the setting value"""
        self.setText(1, str(new_value))

        # Try to convert to appropriate type
        if isinstance(self.setting_def.value, int):
            try:
                self.setting_def.value = int(new_value)
            except ValueError:
                pass
        elif isinstance(self.setting_def.value, float):
            try:
                self.setting_def.value = float(new_value)
            except ValueError:
                pass
        else:
            self.setting_def.value = new_value


class SettingsEditorWidget(QWidget):
    """Widget for editing configuration settings"""

    # Signals
    setting_changed = pyqtSignal(str, object)  # setting_name, new_value
    settings_loaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings_config = None
        self.setting_items = {}  # setting_name -> SettingItem
        self.category_items = {}  # category_name -> QTreeWidgetItem

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Settings Configuration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Search/filter box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter settings...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Quick filters
        filter_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("Show All")
        self.show_eeprom_btn = QPushButton("EEPROM Only")
        self.show_motor_btn = QPushButton("Motor Settings")
        self.show_calib_btn = QPushButton("Calibration")

        self.show_all_btn.clicked.connect(lambda: self._filter_view("all"))
        self.show_eeprom_btn.clicked.connect(lambda: self._filter_view("eeprom"))
        self.show_motor_btn.clicked.connect(lambda: self._filter_category("Motor Control"))
        self.show_calib_btn.clicked.connect(lambda: self._filter_category("Calibration"))

        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_eeprom_btn)
        filter_layout.addWidget(self.show_motor_btn)
        filter_layout.addWidget(self.show_calib_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Settings tree
        self.settings_tree = QTreeWidget()
        self.settings_tree.setHeaderLabels(["Setting Name", "Value", "Unit", "Description"])
        self.settings_tree.setAlternatingRowColors(True)
        self.settings_tree.setColumnWidth(0, 350)
        self.settings_tree.setColumnWidth(1, 100)
        self.settings_tree.setColumnWidth(2, 80)
        self.settings_tree.setColumnWidth(3, 400)
        self.settings_tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.settings_tree)

        # Help text
        help_text = QLabel(
            "💡 Tip: Double-click a setting value to edit. "
            "Settings highlighted in yellow are saved to EEPROM."
        )
        help_text.setStyleSheet("padding: 5px; background-color: #ffffcc; border: 1px solid #cccc00;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        # Statistics
        self.stats_label = QLabel("No settings loaded")
        self.stats_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.stats_label)

    def load_settings(self, settings_config: SettingsConfig):
        """Load settings from configuration"""
        self.settings_config = settings_config

        # Block signals while updating
        self.settings_tree.blockSignals(True)

        # Clear existing items
        self.settings_tree.clear()
        self.setting_items.clear()
        self.category_items.clear()

        # Create category items and setting items
        for category in settings_config.categories:
            # Create category item
            category_item = QTreeWidgetItem([category.name, "", "", ""])
            category_item.setExpanded(True)
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            category_item.setBackground(0, QBrush(QColor(200, 220, 255)))
            category_item.setBackground(1, QBrush(QColor(200, 220, 255)))
            category_item.setBackground(2, QBrush(QColor(200, 220, 255)))
            category_item.setBackground(3, QBrush(QColor(200, 220, 255)))
            self.settings_tree.addTopLevelItem(category_item)
            self.category_items[category.name] = category_item

            # Add settings to category
            for setting_name in category.settings:
                if setting_name in settings_config.settings:
                    setting_def = settings_config.settings[setting_name]
                    setting_item = SettingItem(setting_name, setting_def, category_item)
                    self.setting_items[setting_name] = setting_item

        # Re-enable signals
        self.settings_tree.blockSignals(False)

        # Update statistics
        self._update_statistics()

        # Emit loaded signal
        self.settings_loaded.emit()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle setting value change"""
        if not isinstance(item, SettingItem):
            return

        # Only handle changes to column 1 (value)
        if column != 1:
            return

        # Get new value
        new_value = item.text(1).strip()

        # Validate value
        if not self._validate_setting_value(item.setting_def, new_value):
            # Revert to old value
            item.setText(1, str(item.setting_def.value))
            return

        # Update setting config
        if self.settings_config:
            setting_name = item.setting_name
            old_value = item.setting_def.value

            # Convert to appropriate type
            try:
                if isinstance(old_value, int):
                    converted_value = int(new_value)
                elif isinstance(old_value, float):
                    converted_value = float(new_value)
                else:
                    converted_value = new_value

                # Update the setting item
                item.update_value(converted_value)

                # Emit change signal
                self.setting_changed.emit(setting_name, converted_value)

            except ValueError:
                # Revert on conversion error
                item.setText(1, str(old_value))

    def _validate_setting_value(self, setting_def: SettingDefinition, value: str) -> bool:
        """Validate a setting value"""
        if not value:
            return False

        try:
            # Try to convert to the same type as the original value
            if isinstance(setting_def.value, int):
                int_value = int(value)
                # Basic sanity check - most settings should be positive
                # but some can be negative (like angle offsets)
                return -32768 <= int_value <= 32767
            elif isinstance(setting_def.value, float):
                float_value = float(value)
                return -1000000.0 <= float_value <= 1000000.0
            else:
                # String values are always valid
                return True
        except ValueError:
            return False

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        search_text = text.lower()

        for setting_name, item in self.setting_items.items():
            # Check if setting matches search
            matches = (
                search_text in setting_name.lower() or
                search_text in str(item.setting_def.value).lower() or
                (item.setting_def.unit and search_text in item.setting_def.unit.lower()) or
                (item.setting_def.comment and search_text in item.setting_def.comment.lower())
            )

            # Show/hide item
            item.setHidden(not matches)

        # Show/hide categories based on visible children
        for category_name, category_item in self.category_items.items():
            has_visible_children = False
            for i in range(category_item.childCount()):
                if not category_item.child(i).isHidden():
                    has_visible_children = True
                    break

            category_item.setHidden(not has_visible_children)

    def _filter_view(self, filter_type: str):
        """Filter view to show all/eeprom settings"""
        for setting_name, item in self.setting_items.items():
            if filter_type == "all":
                item.setHidden(False)
            elif filter_type == "eeprom":
                item.setHidden(not item.setting_def.is_eeprom_persistent)

        # Show/hide categories
        for category_name, category_item in self.category_items.items():
            has_visible_children = False
            for i in range(category_item.childCount()):
                if not category_item.child(i).isHidden():
                    has_visible_children = True
                    break

            category_item.setHidden(not has_visible_children)

    def _filter_category(self, category_name: str):
        """Show only settings from a specific category"""
        # Hide all categories except the selected one
        for cat_name, category_item in self.category_items.items():
            if cat_name == category_name:
                category_item.setHidden(False)
                # Show all children
                for i in range(category_item.childCount()):
                    category_item.child(i).setHidden(False)
            else:
                category_item.setHidden(True)

    def _update_statistics(self):
        """Update the statistics label"""
        if not self.settings_config:
            self.stats_label.setText("No settings loaded")
            return

        total = len(self.settings_config.settings)
        eeprom = sum(1 for s in self.settings_config.settings.values() if s.is_eeprom_persistent)

        self.stats_label.setText(
            f"Settings: {total} total ({eeprom} EEPROM persistent)"
        )

    def focus_category(self, category_name: str):
        """
        Focus on a specific category by expanding it and scrolling to it

        Args:
            category_name: Name of the category to focus on
        """
        if category_name in self.category_items:
            category_item = self.category_items[category_name]

            # Collapse all other categories
            for name, item in self.category_items.items():
                item.setExpanded(name == category_name)

            # Scroll to the category
            self.setting_tree.scrollToItem(category_item)

            # Highlight it
            self.setting_tree.setCurrentItem(category_item)

    def get_setting_value(self, setting_name: str):
        """Get the current value of a setting"""
        if setting_name in self.setting_items:
            return self.setting_items[setting_name].setting_def.value
        return None

    def set_setting_value(self, setting_name: str, value):
        """Programmatically set a setting value"""
        if setting_name in self.setting_items:
            item = self.setting_items[setting_name]
            if self._validate_setting_value(item.setting_def, str(value)):
                self.settings_tree.blockSignals(True)
                item.update_value(value)
                self.settings_tree.blockSignals(False)
                self._update_statistics()
