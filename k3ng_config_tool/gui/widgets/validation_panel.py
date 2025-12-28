"""
K3NG Configuration Tool - Validation Panel Widget
Display validation errors, warnings, and info with auto-fix capabilities
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QMessageBox, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QAction
from typing import Optional, List
from pathlib import Path

from ...validators.dependency_validator import (
    ValidationResult,
    ValidationIssue,
    ValidationSeverity
)


class ValidationPanel(QWidget):
    """
    Validation panel widget displaying validation results

    Features:
    - Tabbed view: Errors / Warnings / Info
    - Clickable items with feature navigation
    - Auto-fix button for resolvable issues
    - Export validation report
    - Real-time validation updates
    """

    # Signals
    validation_requested = pyqtSignal()
    fix_requested = pyqtSignal(list)  # List of features to fix
    feature_selected = pyqtSignal(str)  # Feature name to navigate to

    def __init__(self, parent=None):
        """Initialize validation panel"""
        super().__init__(parent)
        self.validation_result: Optional[ValidationResult] = None
        self._init_ui()

    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)

        # Header with validation status
        header_layout = QHBoxLayout()

        self.status_label = QLabel("No validation run")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
        """)
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()

        # Validate button
        self.validate_btn = QPushButton("Validate Configuration")
        self.validate_btn.clicked.connect(self.validation_requested.emit)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self.validate_btn)

        layout.addLayout(header_layout)

        # Tab widget for issues
        self.tabs = QTabWidget()

        # Errors tab
        self.errors_tree = self._create_issues_tree()
        self.tabs.addTab(self.errors_tree, "Errors (0)")

        # Warnings tab
        self.warnings_tree = self._create_issues_tree()
        self.tabs.addTab(self.warnings_tree, "Warnings (0)")

        # Info tab
        self.info_tree = self._create_issues_tree()
        self.tabs.addTab(self.info_tree, "Info (0)")

        layout.addWidget(self.tabs)

        # Footer with action buttons
        footer_layout = QHBoxLayout()

        self.auto_fix_btn = QPushButton("Auto-Fix Issues")
        self.auto_fix_btn.clicked.connect(self._on_auto_fix_clicked)
        self.auto_fix_btn.setEnabled(False)
        self.auto_fix_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        footer_layout.addWidget(self.auto_fix_btn)

        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self._on_export_clicked)
        self.export_btn.setEnabled(False)
        footer_layout.addWidget(self.export_btn)

        footer_layout.addStretch()

        layout.addLayout(footer_layout)

    def _create_issues_tree(self) -> QTreeWidget:
        """Create tree widget for displaying issues"""
        tree = QTreeWidget()
        tree.setHeaderLabels(["Issue", "Details"])
        tree.setColumnWidth(0, 400)
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        tree.itemClicked.connect(self._on_item_clicked)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_context_menu)
        return tree

    def set_validation_result(self, result: ValidationResult):
        """
        Update panel with new validation results

        Args:
            result: ValidationResult from validator
        """
        self.validation_result = result

        # Clear existing items
        self.errors_tree.clear()
        self.warnings_tree.clear()
        self.info_tree.clear()

        # Update status label
        if result.passed:
            self.status_label.setText(f"✅ Validation Passed ({result.total_issues} suggestions)")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #d4edda;
                    color: #155724;
                }
            """)
        else:
            self.status_label.setText(f"❌ Validation Failed ({len(result.errors)} errors)")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #f8d7da;
                    color: #721c24;
                }
            """)

        # Populate errors
        for issue in result.errors:
            self._add_issue_to_tree(self.errors_tree, issue)

        # Populate warnings
        for issue in result.warnings:
            self._add_issue_to_tree(self.warnings_tree, issue)

        # Populate info
        for issue in result.info:
            self._add_issue_to_tree(self.info_tree, issue)

        # Update tab labels with counts
        self.tabs.setTabText(0, f"Errors ({len(result.errors)})")
        self.tabs.setTabText(1, f"Warnings ({len(result.warnings)})")
        self.tabs.setTabText(2, f"Info ({len(result.info)})")

        # Enable/disable auto-fix button
        has_auto_fixable = any(
            issue.auto_fixable
            for issue in result.errors + result.warnings + result.info
        )
        self.auto_fix_btn.setEnabled(has_auto_fixable)

        # Enable export button
        self.export_btn.setEnabled(True)

        # Expand all items
        self.errors_tree.expandAll()
        self.warnings_tree.expandAll()
        self.info_tree.expandAll()

        # Switch to errors tab if there are errors
        if result.errors:
            self.tabs.setCurrentIndex(0)

    def _add_issue_to_tree(self, tree: QTreeWidget, issue: ValidationIssue):
        """Add validation issue to tree widget"""
        # Create top-level item
        item = QTreeWidgetItem(tree)
        item.setText(0, issue.message)
        item.setText(1, issue.rule_type.replace('_', ' ').title())
        item.setData(0, Qt.ItemDataRole.UserRole, issue)

        # Set color based on severity
        if issue.severity == ValidationSeverity.ERROR:
            item.setForeground(0, QColor("#dc3545"))
        elif issue.severity == ValidationSeverity.WARNING:
            item.setForeground(0, QColor("#ffc107"))
        else:
            item.setForeground(0, QColor("#17a2b8"))

        # Add auto-fix indicator
        if issue.auto_fixable:
            item.setText(0, f"🔧 {issue.message}")

        # Add affected features as children
        if issue.affected_features:
            features_item = QTreeWidgetItem(item)
            features_item.setText(0, "Affected Features:")
            features_item.setForeground(0, QColor("#6c757d"))

            for feature in issue.affected_features:
                feature_item = QTreeWidgetItem(features_item)
                feature_item.setText(0, feature)
                feature_item.setData(0, Qt.ItemDataRole.UserRole, feature)

        # Add suggestion as child
        if issue.suggestion:
            suggestion_item = QTreeWidgetItem(item)
            suggestion_item.setText(0, f"💡 Suggestion: {issue.suggestion}")
            suggestion_item.setForeground(0, QColor("#28a745"))

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click - navigate to feature if applicable"""
        # Check if this is a feature item
        feature_data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(feature_data, str) and feature_data.startswith("FEATURE_"):
            self.feature_selected.emit(feature_data)

    def _show_context_menu(self, position):
        """Show context menu for tree items"""
        tree = self.sender()
        item = tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Get issue data
        issue_data = item.data(0, Qt.ItemDataRole.UserRole)

        if isinstance(issue_data, ValidationIssue):
            # Copy message action
            copy_action = QAction("Copy Message", self)
            copy_action.triggered.connect(
                lambda: self._copy_to_clipboard(issue_data.message)
            )
            menu.addAction(copy_action)

            # Auto-fix action if applicable
            if issue_data.auto_fixable:
                fix_action = QAction("Apply Auto-Fix", self)
                fix_action.triggered.connect(
                    lambda: self._apply_single_fix(issue_data)
                )
                menu.addAction(fix_action)

        elif isinstance(issue_data, str) and issue_data.startswith("FEATURE_"):
            # Navigate to feature
            nav_action = QAction(f"Go to {issue_data}", self)
            nav_action.triggered.connect(
                lambda: self.feature_selected.emit(issue_data)
            )
            menu.addAction(nav_action)

            # Copy feature name
            copy_action = QAction("Copy Feature Name", self)
            copy_action.triggered.connect(
                lambda: self._copy_to_clipboard(issue_data)
            )
            menu.addAction(copy_action)

        menu.exec(tree.viewport().mapToGlobal(position))

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def _apply_single_fix(self, issue: ValidationIssue):
        """Apply auto-fix for single issue"""
        if not issue.auto_fixable:
            return

        reply = QMessageBox.question(
            self,
            "Apply Auto-Fix",
            f"Apply automatic fix for:\n\n{issue.message}\n\n{issue.suggestion or ''}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.fix_requested.emit([issue])

    def _on_auto_fix_clicked(self):
        """Handle auto-fix button click"""
        if not self.validation_result:
            return

        # Collect all auto-fixable issues
        fixable_issues = [
            issue for issue in
            self.validation_result.errors +
            self.validation_result.warnings +
            self.validation_result.info
            if issue.auto_fixable
        ]

        if not fixable_issues:
            return

        # Confirm with user
        message = f"Apply automatic fixes for {len(fixable_issues)} issues?\n\n"
        message += "\n".join(f"• {issue.message}" for issue in fixable_issues[:5])
        if len(fixable_issues) > 5:
            message += f"\n... and {len(fixable_issues) - 5} more"

        reply = QMessageBox.question(
            self,
            "Apply Auto-Fixes",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.fix_requested.emit(fixable_issues)

    def _on_export_clicked(self):
        """Export validation report to file"""
        if not self.validation_result:
            return

        # Ask user for file location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Validation Report",
            "validation_report.txt",
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )

        if not filename:
            return

        try:
            report = self._generate_report()

            with open(filename, 'w') as f:
                f.write(report)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Validation report exported to:\n{filename}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export validation report:\n{str(e)}"
            )

    def _generate_report(self) -> str:
        """Generate text report of validation results"""
        if not self.validation_result:
            return "No validation results available"

        lines = []
        lines.append("=" * 70)
        lines.append("K3NG Configuration Tool - Validation Report")
        lines.append("=" * 70)
        lines.append("")

        # Summary
        lines.append("Summary")
        lines.append("-" * 70)
        status = "PASSED" if self.validation_result.passed else "FAILED"
        lines.append(f"Status: {status}")
        lines.append(f"Errors: {len(self.validation_result.errors)}")
        lines.append(f"Warnings: {len(self.validation_result.warnings)}")
        lines.append(f"Info: {len(self.validation_result.info)}")
        lines.append("")

        # Errors
        if self.validation_result.errors:
            lines.append("Errors")
            lines.append("-" * 70)
            for i, issue in enumerate(self.validation_result.errors, 1):
                lines.append(f"{i}. {issue.message}")
                if issue.affected_features:
                    lines.append(f"   Affects: {', '.join(issue.affected_features)}")
                if issue.suggestion:
                    lines.append(f"   Suggestion: {issue.suggestion}")
                lines.append("")

        # Warnings
        if self.validation_result.warnings:
            lines.append("Warnings")
            lines.append("-" * 70)
            for i, issue in enumerate(self.validation_result.warnings, 1):
                lines.append(f"{i}. {issue.message}")
                if issue.affected_features:
                    lines.append(f"   Affects: {', '.join(issue.affected_features)}")
                if issue.suggestion:
                    lines.append(f"   Suggestion: {issue.suggestion}")
                lines.append("")

        # Info
        if self.validation_result.info:
            lines.append("Information")
            lines.append("-" * 70)
            for i, issue in enumerate(self.validation_result.info, 1):
                lines.append(f"{i}. {issue.message}")
                if issue.affected_features:
                    lines.append(f"   Affects: {', '.join(issue.affected_features)}")
                if issue.suggestion:
                    lines.append(f"   Suggestion: {issue.suggestion}")
                lines.append("")

        lines.append("=" * 70)
        lines.append("End of Report")
        lines.append("=" * 70)

        return "\n".join(lines)

    def clear(self):
        """Clear validation panel"""
        self.validation_result = None
        self.errors_tree.clear()
        self.warnings_tree.clear()
        self.info_tree.clear()
        self.status_label.setText("No validation run")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
        """)
        self.tabs.setTabText(0, "Errors (0)")
        self.tabs.setTabText(1, "Warnings (0)")
        self.tabs.setTabText(2, "Info (0)")
        self.auto_fix_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
