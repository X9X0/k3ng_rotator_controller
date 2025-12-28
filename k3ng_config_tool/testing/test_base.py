"""
K3NG Configuration Tool - Test Base Classes
Base classes and types for testing framework
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    status: TestStatus
    duration: float = 0.0  # seconds
    message: str = ""
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    expected: Any = None
    actual: Any = None
    error: Optional[Exception] = None

    def passed(self) -> bool:
        """Check if test passed"""
        return self.status == TestStatus.PASSED

    def failed(self) -> bool:
        """Check if test failed"""
        return self.status == TestStatus.FAILED

    def skipped(self) -> bool:
        """Check if test was skipped"""
        return self.status == TestStatus.SKIPPED

    def __str__(self):
        status_symbols = {
            TestStatus.PASSED: "✓",
            TestStatus.FAILED: "✗",
            TestStatus.SKIPPED: "⊝",
            TestStatus.ERROR: "⚠",
            TestStatus.PENDING: "○",
            TestStatus.RUNNING: "⟳",
        }
        symbol = status_symbols.get(self.status, "?")
        msg = f"{symbol} {self.name}"
        if self.duration > 0:
            msg += f" ({self.duration:.2f}s)"
        if self.message:
            msg += f": {self.message}"
        return msg


@dataclass
class TestSuiteResult:
    """Result of a test suite"""
    name: str
    test_results: List[TestResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Total duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def total_tests(self) -> int:
        """Total number of tests"""
        return len(self.test_results)

    @property
    def passed_tests(self) -> int:
        """Number of passed tests"""
        return sum(1 for t in self.test_results if t.passed())

    @property
    def failed_tests(self) -> int:
        """Number of failed tests"""
        return sum(1 for t in self.test_results if t.failed())

    @property
    def skipped_tests(self) -> int:
        """Number of skipped tests"""
        return sum(1 for t in self.test_results if t.skipped())

    @property
    def error_tests(self) -> int:
        """Number of tests with errors"""
        return sum(1 for t in self.test_results if t.status == TestStatus.ERROR)

    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    def all_passed(self) -> bool:
        """Check if all tests passed"""
        return self.failed_tests == 0 and self.error_tests == 0 and self.total_tests > 0

    def __str__(self):
        return (
            f"{self.name}: {self.passed_tests}/{self.total_tests} passed "
            f"({self.success_rate:.1f}%) in {self.duration:.2f}s"
        )


class BaseTest:
    """
    Base class for all tests

    Subclasses should implement:
    - setup() - Optional setup before test
    - teardown() - Optional cleanup after test
    - run_test() - Actual test implementation
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.result: Optional[TestResult] = None

    def setup(self):
        """Setup before test execution (override in subclass)"""
        pass

    def teardown(self):
        """Cleanup after test execution (override in subclass)"""
        pass

    def run_test(self) -> TestResult:
        """
        Execute the test (override in subclass)

        Returns:
            TestResult with status and details
        """
        raise NotImplementedError("Subclasses must implement run_test()")

    def execute(self) -> TestResult:
        """
        Execute the test with setup/teardown

        Returns:
            TestResult with status and details
        """
        start_time = datetime.now()

        try:
            # Setup
            self.setup()

            # Run test
            self.result = self.run_test()

            # Teardown
            self.teardown()

        except Exception as e:
            # Handle unexpected errors
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.result = TestResult(
                name=self.name,
                status=TestStatus.ERROR,
                duration=duration,
                message=f"Test error: {str(e)}",
                error=e,
                timestamp=start_time
            )

            try:
                self.teardown()
            except Exception:
                pass  # Ignore teardown errors

        # Update duration
        if self.result:
            end_time = datetime.now()
            self.result.duration = (end_time - start_time).total_seconds()

        return self.result

    def skip(self, reason: str = "") -> TestResult:
        """
        Mark test as skipped

        Args:
            reason: Reason for skipping

        Returns:
            TestResult with skipped status
        """
        return TestResult(
            name=self.name,
            status=TestStatus.SKIPPED,
            message=reason or "Test skipped",
            timestamp=datetime.now()
        )

    def assert_true(self, condition: bool, message: str = ""):
        """Assert that condition is true"""
        if not condition:
            raise AssertionError(message or "Assertion failed: condition is not true")

    def assert_false(self, condition: bool, message: str = ""):
        """Assert that condition is false"""
        if condition:
            raise AssertionError(message or "Assertion failed: condition is not false")

    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert that actual equals expected"""
        if actual != expected:
            raise AssertionError(
                message or f"Assertion failed: {actual} != {expected}"
            )

    def assert_not_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert that actual does not equal expected"""
        if actual == expected:
            raise AssertionError(
                message or f"Assertion failed: {actual} == {expected}"
            )

    def assert_in_range(self, value: float, min_val: float, max_val: float, message: str = ""):
        """Assert that value is in range [min_val, max_val]"""
        if not (min_val <= value <= max_val):
            raise AssertionError(
                message or f"Assertion failed: {value} not in range [{min_val}, {max_val}]"
            )


class SerialTest(BaseTest):
    """
    Base class for tests that require serial communication

    Provides serial command interface access
    """

    def __init__(self, name: str, description: str = "", command_interface=None):
        super().__init__(name, description)
        self.command_interface = command_interface
        self.requires_hardware = True

    def send_command(self, command: str):
        """Send command via serial interface"""
        if not self.command_interface:
            raise RuntimeError("No command interface available")

        if not self.command_interface.serial.is_connected:
            raise RuntimeError("Serial port not connected")

        self.command_interface.send_raw(command)

    def wait_for_response(self, timeout: float = 2.0) -> Optional[str]:
        """
        Wait for response from controller

        Args:
            timeout: Timeout in seconds

        Returns:
            Response string or None if timeout
        """
        import time
        start = time.time()

        while time.time() - start < timeout:
            responses = self.command_interface.get_last_responses(1)
            if responses:
                return responses[0]
            time.sleep(0.1)

        return None
