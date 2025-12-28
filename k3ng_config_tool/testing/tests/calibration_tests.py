"""
K3NG Configuration Tool - Calibration Tests
Calibration status and quality verification tests
"""

from typing import List
import time

from ..test_base import SerialTest, TestResult, TestStatus


class CalibrationStatusTest(SerialTest):
    """Test calibration status query"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Calibration Status Test",
            description="Test comprehensive calibration status query",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test calibration status query"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Query calibration status
            self.command_interface.query_calibration_status()
            time.sleep(0.5)

            # Check for response
            responses = self.command_interface.get_last_responses(5)  # May be multi-line

            if responses:
                response_text = "\n".join(responses)
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message="Calibration status query successful",
                    details=f"Status:\n{response_text}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to calibration status query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Calibration status query failed: {str(e)}",
                error=e
            )


class CalibrationQualityTest(SerialTest):
    """Test calibration quality check"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Calibration Quality Test",
            description="Test quick calibration quality check",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test calibration quality"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Query calibration quality
            self.command_interface.query_calibration_quality()
            time.sleep(0.3)

            # Check for response
            responses = self.command_interface.get_last_responses(3)

            if responses:
                response_text = "\n".join(responses)

                # Check for quality indicators
                quality_good = "GOOD" in response_text.upper()
                quality_poor = "POOR" in response_text.upper()
                quality_suspect = "SUSPECT" in response_text.upper()

                status_msg = "Unknown"
                if quality_good:
                    status_msg = "GOOD"
                elif quality_suspect:
                    status_msg = "SUSPECT"
                elif quality_poor:
                    status_msg = "POOR"

                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message=f"Calibration quality: {status_msg}",
                    details=f"Response:\n{response_text}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to calibration quality query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Calibration quality check failed: {str(e)}",
                error=e
            )


class CalibrationValuesTest(SerialTest):
    """Test calibration values display"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Calibration Values Test",
            description="Test magnetometer calibration values display",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test calibration values display"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Show calibration values
            self.command_interface.show_mag_calibration_values()
            time.sleep(0.5)

            # Check for response
            responses = self.command_interface.get_last_responses(10)  # May be multi-line

            if responses:
                response_text = "\n".join(responses)
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message="Calibration values retrieved",
                    details=f"Values:\n{response_text}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to calibration values query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Calibration values query failed: {str(e)}",
                error=e
            )


class CalibrationTablesTest(SerialTest):
    """Test calibration tables display"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Calibration Tables Test",
            description="Test display of all calibration tables",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test calibration tables display"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Show all calibration tables
            self.command_interface.show_calibration_tables()
            time.sleep(0.5)

            # Check for response
            responses = self.command_interface.get_last_responses(15)  # May be multi-line

            if responses:
                response_text = "\n".join(responses)
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message="Calibration tables retrieved",
                    details=f"Tables:\n{response_text}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to calibration tables query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Calibration tables query failed: {str(e)}",
                error=e
            )


def create_calibration_tests(command_interface=None) -> List[SerialTest]:
    """
    Create all calibration verification tests

    Args:
        command_interface: K3NGCommandInterface for serial communication

    Returns:
        List of calibration tests
    """
    tests = []

    tests.append(CalibrationStatusTest(command_interface))
    tests.append(CalibrationQualityTest(command_interface))
    tests.append(CalibrationValuesTest(command_interface))
    tests.append(CalibrationTablesTest(command_interface))

    return tests
