"""
K3NG Configuration Tool - Sensor Tests
Position sensor validation tests
"""

from typing import List
import time

from ..test_base import SerialTest, TestResult, TestStatus


class AzimuthQueryTest(SerialTest):
    """Test azimuth position query"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Azimuth Query Test",
            description="Test azimuth position query command",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test azimuth query"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Query azimuth
            self.command_interface.query_azimuth()
            time.sleep(0.3)

            # Check for response
            responses = self.command_interface.get_last_responses(1)

            if responses:
                response = responses[0]
                # Expected format varies, but should contain azimuth info
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message=f"Azimuth query successful",
                    details=f"Response: {response}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to azimuth query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Azimuth query failed: {str(e)}",
                error=e
            )


class ElevationQueryTest(SerialTest):
    """Test elevation position query"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Elevation Query Test",
            description="Test elevation position query command",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test elevation query"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Query elevation
            self.command_interface.query_elevation()
            time.sleep(0.3)

            # Check for response
            responses = self.command_interface.get_last_responses(1)

            if responses:
                response = responses[0]
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message=f"Elevation query successful",
                    details=f"Response: {response}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to elevation query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Elevation query failed: {str(e)}",
                error=e
            )


class VersionQueryTest(SerialTest):
    """Test version query"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Version Query Test",
            description="Test controller version query",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test version query"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Query version
            self.command_interface.query_code_version()
            time.sleep(0.3)

            # Check for response
            responses = self.command_interface.get_last_responses(1)

            if responses:
                response = responses[0]
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message=f"Version query successful",
                    details=f"Version: {response}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No response to version query"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Version query failed: {str(e)}",
                error=e
            )


class SensorStabilityTest(SerialTest):
    """Test sensor reading stability"""

    def __init__(self, command_interface=None, samples: int = 10):
        super().__init__(
            name="Sensor Stability Test",
            description=f"Test sensor reading stability over {samples} samples",
            command_interface=command_interface
        )
        self.samples = samples

    def run_test(self) -> TestResult:
        """Test sensor stability"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            readings = []

            # Take multiple samples
            for _ in range(self.samples):
                self.command_interface.query_azimuth()
                time.sleep(0.2)

                responses = self.command_interface.get_last_responses(1)
                if responses:
                    readings.append(responses[0])

            if len(readings) >= self.samples * 0.8:  # At least 80% success rate
                return TestResult(
                    name=self.name,
                    status=TestStatus.PASSED,
                    message=f"Sensor stability test passed ({len(readings)}/{self.samples} readings)",
                    details=f"Readings: {readings}"
                )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Insufficient readings ({len(readings)}/{self.samples})"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Stability test failed: {str(e)}",
                error=e
            )


def create_sensor_tests(command_interface=None) -> List[SerialTest]:
    """
    Create all sensor validation tests

    Args:
        command_interface: K3NGCommandInterface for serial communication

    Returns:
        List of sensor tests
    """
    tests = []

    # Query tests
    tests.append(VersionQueryTest(command_interface))
    tests.append(AzimuthQueryTest(command_interface))
    tests.append(ElevationQueryTest(command_interface))

    # Stability test
    tests.append(SensorStabilityTest(command_interface, samples=10))

    return tests
