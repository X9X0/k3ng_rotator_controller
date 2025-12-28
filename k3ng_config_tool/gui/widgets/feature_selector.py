"""
K3NG Configuration Tool - Feature Selector Widget
Displays features in a tree view with checkboxes for enabling/disabling
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QIcon

from parsers.feature_parser import FeatureConfig


class FeatureItem(QTreeWidgetItem):
    """Custom tree widget item for a feature"""

    def __init__(self, feature_name: str, feature_def, parent=None):
        super().__init__(parent)
        self.feature_name = feature_name
        self.feature_def = feature_def

        # Set feature text
        self.setText(0, feature_name)

        # Set tooltip with comment/description
        if feature_def.comment:
            self.setToolTip(0, feature_def.comment)

        # Make it checkable
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        # Set initial check state
        if feature_def.is_active:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)

    def update_check_state(self, is_active: bool):
        """Update the checkbox state"""
        if is_active:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)


class FeatureSelectorWidget(QWidget):
    """Widget for selecting/deselecting features"""

    # Signals
    feature_changed = pyqtSignal(str, bool)  # feature_name, is_active
    features_loaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.feature_config = None
        self.feature_items = {}  # feature_name -> FeatureItem
        self.category_items = {}  # category_name -> QTreeWidgetItem

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Features Configuration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Search/filter box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter features...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Quick filters
        filter_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("Show All")
        self.show_enabled_btn = QPushButton("Enabled Only")
        self.show_disabled_btn = QPushButton("Disabled Only")

        self.show_all_btn.clicked.connect(lambda: self._filter_view("all"))
        self.show_enabled_btn.clicked.connect(lambda: self._filter_view("enabled"))
        self.show_disabled_btn.clicked.connect(lambda: self._filter_view("disabled"))

        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_enabled_btn)
        filter_layout.addWidget(self.show_disabled_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Feature tree
        self.feature_tree = QTreeWidget()
        self.feature_tree.setHeaderLabel("Features")
        self.feature_tree.setAlternatingRowColors(True)
        self.feature_tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.feature_tree)

        # Statistics
        self.stats_label = QLabel("No features loaded")
        self.stats_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.stats_label)

    def load_features(self, feature_config: FeatureConfig):
        """Load features from configuration"""
        self.feature_config = feature_config

        # Block signals while updating
        self.feature_tree.blockSignals(True)

        # Clear existing items
        self.feature_tree.clear()
        self.feature_items.clear()
        self.category_items.clear()

        # Create category items and feature items
        for category in feature_config.categories:
            # Create category item
            category_item = QTreeWidgetItem([category.name])
            category_item.setExpanded(True)
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self.feature_tree.addTopLevelItem(category_item)
            self.category_items[category.name] = category_item

            # Add features to category
            for feature_name in category.features:
                if feature_name in feature_config.features:
                    feature_def = feature_config.features[feature_name]
                    feature_item = FeatureItem(feature_name, feature_def, category_item)
                    self.feature_items[feature_name] = feature_item

        # Re-enable signals
        self.feature_tree.blockSignals(False)

        # Update statistics
        self._update_statistics()

        # Emit loaded signal
        self.features_loaded.emit()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle feature checkbox change"""
        if not isinstance(item, FeatureItem):
            return

        # Get new state
        is_active = (item.checkState(0) == Qt.CheckState.Checked)

        # Update feature config
        if self.feature_config:
            feature_name = item.feature_name
            if is_active:
                self.feature_config.active_features.add(feature_name)
                item.feature_def.is_active = True
            else:
                self.feature_config.active_features.discard(feature_name)
                item.feature_def.is_active = False

            # Emit change signal
            self.feature_changed.emit(feature_name, is_active)

            # Update statistics
            self._update_statistics()

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        search_text = text.lower()

        for feature_name, item in self.feature_items.items():
            # Check if feature matches search
            matches = (
                search_text in feature_name.lower() or
                (item.feature_def.comment and search_text in item.feature_def.comment.lower())
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
        """Filter view to show all/enabled/disabled features"""
        for feature_name, item in self.feature_items.items():
            if filter_type == "all":
                item.setHidden(False)
            elif filter_type == "enabled":
                item.setHidden(not item.feature_def.is_active)
            elif filter_type == "disabled":
                item.setHidden(item.feature_def.is_active)

        # Show/hide categories
        for category_name, category_item in self.category_items.items():
            has_visible_children = False
            for i in range(category_item.childCount()):
                if not category_item.child(i).isHidden():
                    has_visible_children = True
                    break

            category_item.setHidden(not has_visible_children)

    def _update_statistics(self):
        """Update the statistics label"""
        if not self.feature_config:
            self.stats_label.setText("No features loaded")
            return

        total = len(self.feature_config.features)
        enabled = len(self.feature_config.active_features)
        disabled = total - enabled

        self.stats_label.setText(
            f"Features: {enabled}/{total} enabled ({disabled} disabled)"
        )

    def highlight_conflicts(self, conflicting_features: list):
        """Highlight features that have conflicts"""
        for feature_name in conflicting_features:
            if feature_name in self.feature_items:
                item = self.feature_items[feature_name]
                # Set red background for conflicting features
                item.setBackground(0, QBrush(QColor(255, 200, 200)))

    def clear_highlights(self):
        """Clear all conflict highlights"""
        for item in self.feature_items.values():
            item.setBackground(0, QBrush(Qt.GlobalColor.white))

    def get_enabled_features(self) -> set:
        """Get set of enabled feature names"""
        if self.feature_config:
            return self.feature_config.active_features.copy()
        return set()

    def set_feature_enabled(self, feature_name: str, enabled: bool):
        """Programmatically enable/disable a feature"""
        if feature_name in self.feature_items:
            item = self.feature_items[feature_name]
            self.feature_tree.blockSignals(True)
            item.update_check_state(enabled)
            self.feature_tree.blockSignals(False)

            # Update config
            if self.feature_config:
                if enabled:
                    self.feature_config.active_features.add(feature_name)
                    item.feature_def.is_active = True
                else:
                    self.feature_config.active_features.discard(feature_name)
                    item.feature_def.is_active = False

            self._update_statistics()
