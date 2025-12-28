"""
K3NG Configuration Tool - Test Runner Widget
GUI widget for running and displaying hardware tests
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QProgressBar, QLabel, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
from datetime import datetime

from testing.test_engine import TestEngine, create_test_registry
from testing.test_base import TestResult, TestStatus, TestSuiteResult


class TestRunnerThread(QThread):
    """Thread for running tests without blocking UI"""

    finished = pyqtSignal(TestSuiteResult)

    def __init__(self, test_engine, tests, suite_name):
        super().__init__()
        self.test_engine = test_engine
        self.tests = tests
        self.suite_name = suite_name

    def run(self):
        """Run tests in thread"""
        result = self.test_engine.run_tests(self.tests, self.suite_name)
        self.finished.emit(result)


class TestRunnerWidget(QWidget):
    """Widget for running hardware tests"""

    # Signals
    tests_started = pyqtSignal()
    tests_completed = pyqtSignal(TestSuiteResult)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.test_engine = TestEngine()
        self.test_registry = None
        self.command_interface = None
        self.current_result: TestSuiteResult = None
        self.runner_thread = None

        # Connect test engine signals
        self.test_engine.test_started.connect(self._on_test_started)
        self.test_engine.test_completed.connect(self._on_test_completed)
        self.test_engine.suite_started.connect(self._on_suite_started)
        self.test_engine.suite_completed.connect(self._on_suite_completed)
        self.test_engine.progress_updated.connect(self._on_progress_updated)

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>Hardware Testing</h2>")
        layout.addWidget(header)

        description = QLabel(
            "Run automated tests to verify hardware functionality. "
            "Requires serial connection to K3NG controller."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Test selection tree
        test_group = QGroupBox("Available Tests")
        test_layout = QVBoxLayout()

        self.test_tree = QTreeWidget()
        self.test_tree.setHeaderLabel("Tests")
        self.test_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        test_layout.addWidget(self.test_tree)

        # Selection buttons
        selection_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_tests)
        selection_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all_tests)
        selection_layout.addWidget(deselect_all_btn)

        selection_layout.addStretch()
        test_layout.addLayout(selection_layout)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Control panel
        control_layout = QHBoxLayout()

        self.run_btn = QPushButton("Run Selected Tests")
        self.run_btn.clicked.connect(self._run_selected_tests)
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        self.run_btn.setEnabled(False)
        control_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_tests)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        self.report_btn = QPushButton("Generate Report")
        self.report_btn.clicked.connect(self._generate_report)
        self.report_btn.setEnabled(False)
        control_layout.addWidget(self.report_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results area
        results_label = QLabel("<b>Test Results:</b>")
        layout.addWidget(results_label)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 9))
        self.results_text.setPlaceholderText("Test results will appear here...")
        layout.addWidget(self.results_text)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)

    def set_command_interface(self, command_interface):
        """
        Set the command interface for serial tests

        Args:
            command_interface: K3NGCommandInterface instance
        """
        self.command_interface = command_interface

        # Create test registry with command interface
        self.test_registry = create_test_registry(command_interface)

        # Populate test tree
        self._populate_test_tree()

        # Enable run button if connected
        if command_interface and command_interface.serial.is_connected:
            self.run_btn.setEnabled(True)

    def _populate_test_tree(self):
        """Populate the test tree with available tests"""
        self.test_tree.clear()

        if not self.test_registry:
            return

        for category in self.test_registry.categories:
            # Create category item
            category_item = QTreeWidgetItem(self.test_tree)
            category_item.setText(0, f"{category.name} ({len(category.tests)} tests)")
            category_item.setExpanded(True)
            category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            category_item.setCheckState(0, Qt.CheckState.Unchecked)

            # Add test items
            for test in category.tests:
                test_item = QTreeWidgetItem(category_item)
                test_item.setText(0, test.name)
                test_item.setData(0, Qt.ItemDataRole.UserRole, test)
                test_item.setFlags(test_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                test_item.setCheckState(0, Qt.CheckState.Unchecked)

    def _select_all_tests(self):
        """Select all tests"""
        root = self.test_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_item.setCheckState(0, Qt.CheckState.Checked)
            for j in range(category_item.childCount()):
                test_item = category_item.child(j)
                test_item.setCheckState(0, Qt.CheckState.Checked)

    def _deselect_all_tests(self):
        """Deselect all tests"""
        root = self.test_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_item.setCheckState(0, Qt.CheckState.Unchecked)
            for j in range(category_item.childCount()):
                test_item = category_item.child(j)
                test_item.setCheckState(0, Qt.CheckState.Unchecked)

    def _get_selected_tests(self):
        """Get list of selected tests"""
        selected_tests = []
        root = self.test_tree.invisibleRootItem()

        for i in range(root.childCount()):
            category_item = root.child(i)
            for j in range(category_item.childCount()):
                test_item = category_item.child(j)
                if test_item.checkState(0) == Qt.CheckState.Checked:
                    test = test_item.data(0, Qt.ItemDataRole.UserRole)
                    if test:
                        selected_tests.append(test)

        return selected_tests

    def _run_selected_tests(self):
        """Run selected tests"""
        selected_tests = self._get_selected_tests()

        if not selected_tests:
            self.status_label.setText("No tests selected")
            return

        if not self.command_interface or not self.command_interface.serial.is_connected:
            self.status_label.setText("Serial port not connected")
            return

        # Clear results
        self.results_text.clear()
        self.current_result = None

        # Update UI
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.report_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(selected_tests))

        # Emit signal
        self.tests_started.emit()

        # Run tests in thread
        suite_name = f"K3NG Hardware Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.runner_thread = TestRunnerThread(self.test_engine, selected_tests, suite_name)
        self.runner_thread.finished.connect(self._on_thread_finished)
        self.runner_thread.start()

    def _stop_tests(self):
        """Stop test execution"""
        self.test_engine.stop()
        self.status_label.setText("Stopping tests...")

    def _on_test_started(self, test_name: str):
        """Handle test started"""
        self.status_label.setText(f"Running: {test_name}")
        self.results_text.append(f"\n⟳ {test_name}...")

    def _on_test_completed(self, result: TestResult):
        """Handle test completed"""
        # Update last line with result
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()

        # Add result with color
        result_text = str(result)
        if result.passed():
            color = "green"
        elif result.failed():
            color = "red"
        elif result.skipped():
            color = "orange"
        else:
            color = "gray"

        self.results_text.append(f'<span style="color: {color}">{result_text}</span>')

    def _on_suite_started(self, suite_name: str):
        """Handle suite started"""
        self.results_text.append(f"<b>Starting: {suite_name}</b>")
        self.results_text.append("="*60)

    def _on_suite_completed(self, result: TestSuiteResult):
        """Handle suite completed"""
        self.current_result = result

        self.results_text.append("\n" + "="*60)
        self.results_text.append(f"<b>Test Suite Complete</b>")
        self.results_text.append(f"Total: {result.total_tests}")
        self.results_text.append(f'<span style="color: green">Passed: {result.passed_tests}</span>')
        self.results_text.append(f'<span style="color: red">Failed: {result.failed_tests}</span>')
        self.results_text.append(f'<span style="color: orange">Skipped: {result.skipped_tests}</span>')
        self.results_text.append(f"Success Rate: {result.success_rate:.1f}%")
        self.results_text.append(f"Duration: {result.duration:.2f}s")

        # Update status
        if result.all_passed():
            self.status_label.setText("✓ All tests passed!")
            self.status_label.setStyleSheet("padding: 5px; background-color: #c8e6c9; color: #2e7d32;")
        else:
            self.status_label.setText(f"✗ {result.failed_tests} test(s) failed")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffccbc; color: #c62828;")

    def _on_progress_updated(self, current: int, total: int):
        """Handle progress update"""
        self.progress_bar.setValue(current)

    def _on_thread_finished(self):
        """Handle thread finished"""
        # Re-enable UI
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.report_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Emit signal
        if self.current_result:
            self.tests_completed.emit(self.current_result)

    def _generate_report(self):
        """Generate HTML test report"""
        if not self.current_result:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Test Report",
            str(Path.home() / "k3ng_test_report.html"),
            "HTML Files (*.html);;All Files (*)"
        )

        if filename:
            try:
                from testing.report_generator import generate_html_report
                generate_html_report(self.current_result, filename)
                self.status_label.setText(f"Report saved to {filename}")
            except Exception as e:
                self.status_label.setText(f"Failed to generate report: {str(e)}")
