"""
K3NG Configuration Tool - Motor Tests
Motor control and rotation testing
"""

from typing import List
import time

from ..test_base import SerialTest, TestResult, TestStatus


class StopCommandTest(SerialTest):
    """Test stop command"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Stop Command Test",
            description="Test motor stop command",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test stop command"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            self.command_interface.stop_rotation()
            time.sleep(0.2)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message="Stop command sent successfully"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Stop command failed: {str(e)}",
                error=e
            )


class CWRotationTest(SerialTest):
    """Test clockwise rotation"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="CW Rotation Test",
            description="Test clockwise rotation command",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test CW rotation"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Start CW rotation
            self.command_interface.rotate_cw()
            time.sleep(1.0)  # Rotate for 1 second

            # Stop
            self.command_interface.stop_rotation()
            time.sleep(0.1)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message="CW rotation command executed"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"CW rotation failed: {str(e)}",
                error=e
            )


class CCWRotationTest(SerialTest):
    """Test counter-clockwise rotation"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="CCW Rotation Test",
            description="Test counter-clockwise rotation command",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test CCW rotation"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Start CCW rotation
            self.command_interface.rotate_ccw()
            time.sleep(1.0)  # Rotate for 1 second

            # Stop
            self.command_interface.stop_rotation()
            time.sleep(0.1)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message="CCW rotation command executed"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"CCW rotation failed: {str(e)}",
                error=e
            )


class SpeedControlTest(SerialTest):
    """Test speed control commands"""

    def __init__(self, command_interface=None):
        super().__init__(
            name="Speed Control Test",
            description="Test speed control (X1-X4) commands",
            command_interface=command_interface
        )

    def run_test(self) -> TestResult:
        """Test speed control"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Test all speed levels
            self.command_interface.set_speed_x1()
            time.sleep(0.2)

            self.command_interface.set_speed_x2()
            time.sleep(0.2)

            self.command_interface.set_speed_x3()
            time.sleep(0.2)

            self.command_interface.set_speed_x4()
            time.sleep(0.2)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message="All speed commands sent successfully"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Speed control failed: {str(e)}",
                error=e
            )


class PositionCommandTest(SerialTest):
    """Test position command"""

    def __init__(self, target_azimuth: int, command_interface=None):
        super().__init__(
            name=f"Position {target_azimuth}° Test",
            description=f"Test rotation to {target_azimuth}° azimuth",
            command_interface=command_interface
        )
        self.target_azimuth = target_azimuth

    def run_test(self) -> TestResult:
        """Test position command"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Send position command
            self.command_interface.rotate_azimuth(self.target_azimuth)
            time.sleep(0.5)

            # Query current position
            self.command_interface.query_azimuth()
            time.sleep(0.3)

            # Check response
            responses = self.command_interface.get_last_responses(2)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message=f"Position command sent: {self.target_azimuth}°",
                details=f"Responses: {responses}"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Position command failed: {str(e)}",
                error=e
            )


def create_motor_tests(command_interface=None) -> List[SerialTest]:
    """
    Create all motor control tests

    Args:
        command_interface: K3NGCommandInterface for serial communication

    Returns:
        List of motor tests
    """
    tests = []

    # Basic control tests
    tests.append(StopCommandTest(command_interface))
    tests.append(CWRotationTest(command_interface))
    tests.append(CCWRotationTest(command_interface))
    tests.append(SpeedControlTest(command_interface))

    # Position tests
    positions = [0, 90, 180, 270]
    for position in positions:
        tests.append(PositionCommandTest(position, command_interface))

    return tests
