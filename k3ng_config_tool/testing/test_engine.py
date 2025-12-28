"""
K3NG Configuration Tool - Test Engine
Orchestrates test execution and result collection
"""

from typing import List, Optional, Callable
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from .test_base import BaseTest, TestResult, TestSuiteResult, TestStatus


class TestEngine(QObject):
    """
    Test execution engine

    Manages test execution, progress reporting, and result collection
    """

    # Signals
    test_started = pyqtSignal(str)  # test name
    test_completed = pyqtSignal(TestResult)  # test result
    suite_started = pyqtSignal(str)  # suite name
    suite_completed = pyqtSignal(TestSuiteResult)  # suite result
    progress_updated = pyqtSignal(int, int)  # current, total

    def __init__(self):
        super().__init__()
        self.running = False
        self.current_result: Optional[TestSuiteResult] = None

    def run_tests(self, tests: List[BaseTest], suite_name: str = "Test Suite") -> TestSuiteResult:
        """
        Run a list of tests

        Args:
            tests: List of test instances
            suite_name: Name of the test suite

        Returns:
            TestSuiteResult with all results
        """
        self.running = True
        self.current_result = TestSuiteResult(
            name=suite_name,
            start_time=datetime.now()
        )

        self.suite_started.emit(suite_name)
        total_tests = len(tests)

        for idx, test in enumerate(tests):
            if not self.running:
                # Execution was stopped
                break

            self.test_started.emit(test.name)
            self.progress_updated.emit(idx + 1, total_tests)

            try:
                result = test.execute()
                self.current_result.test_results.append(result)
                self.test_completed.emit(result)
            except Exception as e:
                # Unexpected error during test execution
                error_result = TestResult(
                    name=test.name,
                    status=TestStatus.ERROR,
                    message=f"Unexpected error: {str(e)}",
                    error=e,
                    timestamp=datetime.now()
                )
                self.current_result.test_results.append(error_result)
                self.test_completed.emit(error_result)

        self.current_result.end_time = datetime.now()
        self.suite_completed.emit(self.current_result)
        self.running = False

        return self.current_result

    def stop(self):
        """Stop test execution"""
        self.running = False

    def is_running(self) -> bool:
        """Check if tests are currently running"""
        return self.running


class TestCategory:
    """
    Test category for organizing tests

    Groups related tests together
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tests: List[BaseTest] = []

    def add_test(self, test: BaseTest):
        """Add a test to this category"""
        self.tests.append(test)

    def get_tests(self) -> List[BaseTest]:
        """Get all tests in this category"""
        return self.tests

    def __len__(self):
        return len(self.tests)


class TestRegistry:
    """
    Registry of all available tests

    Organizes tests by category for UI display
    """

    def __init__(self):
        self.categories: List[TestCategory] = []

    def add_category(self, category: TestCategory):
        """Add a test category"""
        self.categories.append(category)

    def get_category(self, name: str) -> Optional[TestCategory]:
        """Get a category by name"""
        for category in self.categories:
            if category.name == name:
                return category
        return None

    def get_all_tests(self) -> List[BaseTest]:
        """Get all tests from all categories"""
        all_tests = []
        for category in self.categories:
            all_tests.extend(category.tests)
        return all_tests

    def get_tests_by_category(self, category_name: str) -> List[BaseTest]:
        """Get all tests in a specific category"""
        category = self.get_category(category_name)
        if category:
            return category.get_tests()
        return []

    def get_category_names(self) -> List[str]:
        """Get names of all categories"""
        return [cat.name for cat in self.categories]

    def total_tests(self) -> int:
        """Get total number of tests"""
        return sum(len(cat) for cat in self.categories)


def create_test_registry(command_interface=None) -> TestRegistry:
    """
    Create and populate the test registry with all available tests

    Args:
        command_interface: K3NGCommandInterface for serial tests

    Returns:
        TestRegistry with all tests
    """
    from .tests.io_tests import create_io_tests
    from .tests.motor_tests import create_motor_tests
    from .tests.sensor_tests import create_sensor_tests
    from .tests.calibration_tests import create_calibration_tests

    registry = TestRegistry()

    # I/O Tests
    io_category = TestCategory("I/O Verification", "Digital and analog I/O testing")
    io_tests = create_io_tests(command_interface)
    for test in io_tests:
        io_category.add_test(test)
    registry.add_category(io_category)

    # Motor Tests
    motor_category = TestCategory("Motor Control", "Motor rotation and speed testing")
    motor_tests = create_motor_tests(command_interface)
    for test in motor_tests:
        motor_category.add_test(test)
    registry.add_category(motor_category)

    # Sensor Tests
    sensor_category = TestCategory("Position Sensors", "Position sensor validation")
    sensor_tests = create_sensor_tests(command_interface)
    for test in sensor_tests:
        sensor_category.add_test(test)
    registry.add_category(sensor_category)

    # Calibration Tests
    calibration_category = TestCategory("Calibration", "Calibration verification")
    calibration_tests = create_calibration_tests(command_interface)
    for test in calibration_tests:
        calibration_category.add_test(test)
    registry.add_category(calibration_category)

    return registry
