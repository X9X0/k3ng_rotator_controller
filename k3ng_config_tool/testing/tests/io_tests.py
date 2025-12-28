"""
K3NG Configuration Tool - I/O Tests
Digital and analog I/O verification tests
"""

from typing import List
import time

from ..test_base import SerialTest, TestResult, TestStatus


class DigitalPinTest(SerialTest):
    """Test digital pin read/write"""

    def __init__(self, pin: int, command_interface=None):
        super().__init__(
            name=f"Digital Pin {pin} Test",
            description=f"Test digital I/O on pin {pin}",
            command_interface=command_interface
        )
        self.pin = pin

    def run_test(self) -> TestResult:
        """Test digital pin"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Initialize pin as output
            self.command_interface.digital_output_init(self.pin)
            time.sleep(0.1)

            # Set HIGH
            self.command_interface.digital_set_high(self.pin)
            time.sleep(0.1)

            # Set LOW
            self.command_interface.digital_set_low(self.pin)
            time.sleep(0.1)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message=f"Pin {self.pin} digital I/O working"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Digital I/O test failed: {str(e)}",
                error=e
            )


class AnalogReadTest(SerialTest):
    """Test analog pin read"""

    def __init__(self, pin: int, command_interface=None):
        super().__init__(
            name=f"Analog Read Pin {pin} Test",
            description=f"Test analog read on pin {pin}",
            command_interface=command_interface
        )
        self.pin = pin

    def run_test(self) -> TestResult:
        """Test analog read"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Read analog value
            self.command_interface.analog_read(self.pin)
            time.sleep(0.2)

            # Check for response
            responses = self.command_interface.get_last_responses(1)

            if responses:
                # Parse response (expected format: "A<pin>:<value>")
                response = responses[0]
                if f"A{self.pin:02d}:" in response:
                    return TestResult(
                        name=self.name,
                        status=TestStatus.PASSED,
                        message=f"Analog read successful: {response}"
                    )

            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message="No valid analog read response received"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"Analog read test failed: {str(e)}",
                error=e
            )


class PWMOutputTest(SerialTest):
    """Test PWM output"""

    def __init__(self, pin: int, command_interface=None):
        super().__init__(
            name=f"PWM Pin {pin} Test",
            description=f"Test PWM output on pin {pin}",
            command_interface=command_interface
        )
        self.pin = pin

    def run_test(self) -> TestResult:
        """Test PWM output"""
        if not self.command_interface:
            return self.skip("No command interface available")

        if not self.command_interface.serial.is_connected:
            return self.skip("Serial port not connected")

        try:
            # Test PWM values
            pwm_values = [0, 128, 255]

            for value in pwm_values:
                self.command_interface.analog_write_pwm(self.pin, value)
                time.sleep(0.1)

            return TestResult(
                name=self.name,
                status=TestStatus.PASSED,
                message=f"PWM output test passed on pin {self.pin}"
            )

        except Exception as e:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILED,
                message=f"PWM test failed: {str(e)}",
                error=e
            )


def create_io_tests(command_interface=None) -> List[SerialTest]:
    """
    Create all I/O tests

    Args:
        command_interface: K3NGCommandInterface for serial communication

    Returns:
        List of I/O tests
    """
    tests = []

    # Digital pin tests (test a few common pins)
    digital_pins = [2, 3, 4, 5]
    for pin in digital_pins:
        tests.append(DigitalPinTest(pin, command_interface))

    # Analog read tests
    analog_pins = [0, 1, 2, 3]
    for pin in analog_pins:
        tests.append(AnalogReadTest(pin, command_interface))

    # PWM tests (common PWM pins on Arduino Mega)
    pwm_pins = [3, 5, 6, 9]
    for pin in pwm_pins:
        tests.append(PWMOutputTest(pin, command_interface))

    return tests
