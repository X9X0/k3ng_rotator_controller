"""
Pin Configuration Validator

Validates pin assignments against Arduino board capabilities
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from boards.board_database import BoardDatabase
from validators.dependency_validator import ValidationSeverity, ValidationIssue, ValidationResult


# Pin capability requirements for K3NG configuration
PIN_REQUIREMENTS = {
    # PWM-required pins (motor speed control)
    'pwm': [
        'azimuth_speed_voltage',
        'elevation_speed_voltage',
    ],

    # Interrupt-required pins (pulse inputs and encoders)
    'interrupt': [
        'az_incremental_encoder_a_pin',
        'az_incremental_encoder_b_pin',
        'el_incremental_encoder_a_pin',
        'el_incremental_encoder_b_pin',
        'az_position_pulse_pin',
        'el_position_pulse_pin',
        'az_pulse_start_pin',
        'el_pulse_start_pin',
    ],

    # Analog input pins (potentiometers, voltage sensing)
    'analog': [
        'rotator_analog_az',
        'rotator_analog_el',
        'azimuth_analog_input',
        'elevation_analog_input',
        'analog_az_full_ccw',
        'analog_az_full_cw',
        'analog_el_0_degrees',
        'analog_el_max_elevation',
    ],
}


class PinValidator:
    """
    Pin configuration validator with board awareness

    Validates:
    - Pin capability requirements (PWM, interrupt, analog)
    - Pin conflicts (same pin used multiple times)
    - Reserved pin usage (I2C, SPI, Serial)
    - Pin number validity
    """

    def __init__(self, board_database: Optional[BoardDatabase] = None):
        """
        Initialize pin validator

        Args:
            board_database: BoardDatabase instance (creates new if None)
        """
        self.board_db = board_database or BoardDatabase()

    def validate(self, board_id: str, pin_assignments: Dict[str, Any],
                 active_features: Set[str]) -> ValidationResult:
        """
        Validate pin configuration

        Args:
            board_id: Board identifier (e.g., 'arduino_mega_2560')
            pin_assignments: Dict of pin_name -> pin_value
            active_features: Set of enabled feature names

        Returns:
            ValidationResult with errors, warnings, and info
        """
        result = ValidationResult(passed=True)

        # Check if board exists
        board = self.board_db.get_board(board_id)
        if not board:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                rule_type='board_validation',
                message=f"Unknown board: {board_id}",
                affected_features=[],
                suggestion="Select a valid Arduino board"
            ))
            result.passed = False
            return result

        # Filter pin assignments to only those that are enabled (not 0 or disabled)
        active_pins = {
            name: value for name, value in pin_assignments.items()
            if value != 0 and value != '0' and value is not None and value != 'disabled'
        }

        # Validate pin capabilities
        self._validate_pin_capabilities(board_id, active_pins, active_features, result)

        # Detect pin conflicts
        self._validate_pin_conflicts(board_id, active_pins, result)

        # Validate reserved pins
        self._validate_reserved_pins(board_id, active_pins, active_features, result)

        # Validate pin numbers
        self._validate_pin_numbers(board_id, active_pins, result)

        return result

    def _validate_pin_capabilities(self, board_id: str, pin_assignments: Dict[str, Any],
                                   active_features: Set[str], result: ValidationResult):
        """Validate that pins meet required capabilities"""

        # Check PWM pins
        for pin_name in PIN_REQUIREMENTS['pwm']:
            if pin_name in pin_assignments:
                pin_value = pin_assignments[pin_name]
                if isinstance(pin_value, int):
                    if not self.board_db.is_pwm_pin(board_id, pin_value):
                        pwm_pins = self.board_db.get_pwm_pins(board_id)
                        result.errors.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            rule_type='pin_capability',
                            message=f"Pin {pin_name} ({pin_value}) requires PWM capability",
                            affected_features=[pin_name],
                            suggestion=f"Change {pin_name} to a PWM-capable pin: {pwm_pins}"
                        ))
                        result.passed = False

        # Check interrupt pins
        for pin_name in PIN_REQUIREMENTS['interrupt']:
            if pin_name in pin_assignments:
                pin_value = pin_assignments[pin_name]
                if isinstance(pin_value, int):
                    if not self.board_db.is_interrupt_pin(board_id, pin_value):
                        int_pins = self.board_db.get_interrupt_pins(board_id)
                        result.errors.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            rule_type='pin_capability',
                            message=f"Pin {pin_name} ({pin_value}) requires interrupt capability",
                            affected_features=[pin_name],
                            suggestion=f"Change {pin_name} to an interrupt-capable pin: {int_pins}"
                        ))
                        result.passed = False

        # Check analog pins
        for pin_name in PIN_REQUIREMENTS['analog']:
            if pin_name in pin_assignments:
                pin_value = pin_assignments[pin_name]
                if isinstance(pin_value, str) and pin_value.startswith('A'):
                    if not self.board_db.is_analog_pin(board_id, pin_value):
                        board = self.board_db.get_board(board_id)
                        analog_pins = board.pins['analog']['names']
                        result.errors.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            rule_type='pin_capability',
                            message=f"Pin {pin_name} ({pin_value}) requires analog input capability",
                            affected_features=[pin_name],
                            suggestion=f"Change {pin_name} to a valid analog pin: {analog_pins}"
                        ))
                        result.passed = False

    def _validate_pin_conflicts(self, board_id: str, pin_assignments: Dict[str, Any],
                                result: ValidationResult):
        """Detect and report pin conflicts"""

        conflicts = self.board_db.detect_pin_conflicts(board_id, pin_assignments)

        for conflict in conflicts:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                rule_type='pin_conflict',
                message=conflict['message'],
                affected_features=conflict['assignments'],
                suggestion=f"Assign different pins to avoid conflict on pin {conflict['pin']}"
            ))
            result.passed = False

    def _validate_reserved_pins(self, board_id: str, pin_assignments: Dict[str, Any],
                                active_features: Set[str], result: ValidationResult):
        """Validate usage of reserved pins (I2C, SPI, Serial)"""

        board = self.board_db.get_board(board_id)
        if not board:
            return

        # Check I2C pins if I2C features are enabled
        i2c_features = {
            'FEATURE_ADAFRUIT_I2C_LCD',
            'FEATURE_YWROBOT_I2C_DISPLAY',
            'FEATURE_WIRE_SUPPORT',
            'FEATURE_RTC_DS1307',
            'FEATURE_RTC_PCF8583',
            'FEATURE_ADXL345_USING_ADAFRUIT_LIB',
            'FEATURE_ADXL345_USING_LOVE_ELECTRON_LIB',
            'FEATURE_HMC5883L',
            'FEATURE_LSM303',
            'FEATURE_QMC5883',
        }

        if i2c_features & active_features:
            i2c_reserved = self.board_db.get_reserved_pins(board_id, 'i2c')
            for pin_name, pin_value in pin_assignments.items():
                if pin_value in i2c_reserved or (isinstance(pin_value, int) and pin_value in i2c_reserved):
                    result.warnings.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        rule_type='reserved_pin',
                        message=f"Pin {pin_name} ({pin_value}) is reserved for I2C",
                        affected_features=[pin_name],
                        suggestion=f"I2C features are enabled. Ensure pin {pin_value} is not used for other purposes."
                    ))

        # Check SPI pins if SPI features are enabled
        spi_features = {
            'FEATURE_SPI',
            'FEATURE_ETHERNET',
        }

        if spi_features & active_features:
            spi_reserved = self.board_db.get_reserved_pins(board_id, 'spi')
            for pin_name, pin_value in pin_assignments.items():
                if pin_value in spi_reserved or (isinstance(pin_value, int) and pin_value in spi_reserved):
                    result.warnings.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        rule_type='reserved_pin',
                        message=f"Pin {pin_name} ({pin_value}) is reserved for SPI",
                        affected_features=[pin_name],
                        suggestion=f"SPI/Ethernet features are enabled. Ensure pin {pin_value} is not used for other purposes."
                    ))

    def _validate_pin_numbers(self, board_id: str, pin_assignments: Dict[str, Any],
                              result: ValidationResult):
        """Validate that pin numbers are in valid range"""

        board = self.board_db.get_board(board_id)
        if not board:
            return

        for pin_name, pin_value in pin_assignments.items():
            # Skip analog pins (validated separately)
            if isinstance(pin_value, str) and pin_value.startswith('A'):
                continue

            # Skip remote pins (>99)
            if isinstance(pin_value, int) and pin_value > 99:
                continue

            # Validate digital pin range
            if isinstance(pin_value, int):
                pin_range = board.pins['digital']['range']
                if isinstance(pin_range, list) and len(pin_range) == 2:
                    min_pin, max_pin = pin_range
                    if pin_value < min_pin or pin_value > max_pin:
                        result.errors.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            rule_type='pin_range',
                            message=f"Pin {pin_name} ({pin_value}) is out of valid range",
                            affected_features=[pin_name],
                            suggestion=f"Valid pin range for {board.board_name}: {min_pin}-{max_pin}"
                        ))
                        result.passed = False

    def get_pin_suggestions(self, board_id: str, capability: str) -> List[int]:
        """
        Get suggested pins for a capability

        Args:
            board_id: Board identifier
            capability: Required capability ('pwm', 'interrupt', 'analog')

        Returns:
            List of suggested pin numbers
        """
        if capability == 'pwm':
            return self.board_db.get_pwm_pins(board_id)
        elif capability == 'interrupt':
            return self.board_db.get_interrupt_pins(board_id)
        else:
            return []

    def explain_pin_requirements(self, pin_name: str) -> Dict[str, Any]:
        """
        Explain requirements for a pin

        Args:
            pin_name: Configuration pin name

        Returns:
            Dict with requirement information
        """
        info = {
            'pin_name': pin_name,
            'required_capability': None,
            'description': '',
            'notes': []
        }

        # Check capability requirements
        for capability, pins in PIN_REQUIREMENTS.items():
            if pin_name in pins:
                info['required_capability'] = capability
                if capability == 'pwm':
                    info['description'] = 'This pin controls motor speed using PWM'
                    info['notes'].append('Must be connected to a PWM-capable pin')
                elif capability == 'interrupt':
                    info['description'] = 'This pin reads pulses and requires interrupt capability'
                    info['notes'].append('Must be connected to an interrupt-capable pin')
                    info['notes'].append('Used for encoders or pulse position sensors')
                elif capability == 'analog':
                    info['description'] = 'This pin reads analog voltage'
                    info['notes'].append('Must be connected to an analog input pin (A0-A15)')
                    info['notes'].append('Used for potentiometer position sensors')
                break

        return info


if __name__ == "__main__":
    # Test the pin validator
    from boards.board_database import BoardDatabase

    print("=== Pin Validator Test ===\n")

    db = BoardDatabase()
    validator = PinValidator(db)

    # Test case 1: Valid Arduino Mega configuration
    print("Test 1: Valid Mega configuration")
    pin_config = {
        'azimuth_speed_voltage': 10,  # PWM pin
        'elevation_speed_voltage': 11,  # PWM pin
        'az_incremental_encoder_a_pin': 2,  # Interrupt pin
        'az_incremental_encoder_b_pin': 3,  # Interrupt pin
        'rotator_analog_az': 'A0',  # Analog pin
        'rotate_cw': 5,
        'rotate_ccw': 6,
    }
    active_features = {
        'FEATURE_AZ_POSITION_ROTARY_ENCODER',
        'FEATURE_ELEVATION_CONTROL',
    }

    result = validator.validate('arduino_mega_2560', pin_config, active_features)
    if result.passed:
        print("✓ Configuration is valid!\n")
    else:
        print(f"✗ Found {len(result.errors)} error(s):\n")
        for error in result.errors:
            print(f"  • {error.message}")
            print(f"    Affected: {', '.join(error.affected_features)}")
            if error.suggestion:
                print(f"    💡 {error.suggestion}")
            print()

    # Test case 2: Invalid Uno configuration (PWM pin not PWM-capable)
    print("\nTest 2: Invalid Uno configuration (pin 13 not PWM)")
    pin_config_invalid = {
        'azimuth_speed_voltage': 13,  # Pin 13 is NOT PWM on Uno!
        'az_incremental_encoder_a_pin': 2,  # Interrupt pin
        'rotator_analog_az': 'A0',
    }
    active_features_uno = {
        'FEATURE_AZ_POSITION_ROTARY_ENCODER',
    }

    result = validator.validate('arduino_uno', pin_config_invalid, active_features_uno)
    if result.passed:
        print("✓ Configuration is valid!\n")
    else:
        print(f"✗ Found {len(result.errors)} error(s):\n")
        for error in result.errors:
            print(f"  • {error.message}")
            print(f"    Affected: {', '.join(error.affected_features)}")
            if error.suggestion:
                print(f"    💡 {error.suggestion}")
            print()

    # Test case 3: Pin conflict
    print("\nTest 3: Pin conflict (pin 10 used twice)")
    pin_config_conflict = {
        'azimuth_speed_voltage': 10,
        'brake_az': 10,  # Conflict!
        'az_incremental_encoder_a_pin': 2,
    }

    result = validator.validate('arduino_mega_2560', pin_config_conflict, set())
    if result.passed:
        print("✓ Configuration is valid!\n")
    else:
        print(f"✗ Found {len(result.errors)} error(s):\n")
        for error in result.errors:
            print(f"  • {error.message}")
            print(f"    Affected: {', '.join(error.affected_features)}")
            if error.suggestion:
                print(f"    💡 {error.suggestion}")
            print()

    # Test pin requirements
    print("\nPin Requirements:")
    for pin_name in ['azimuth_speed_voltage', 'az_incremental_encoder_a_pin', 'rotator_analog_az']:
        info = validator.explain_pin_requirements(pin_name)
        print(f"\n{info['pin_name']}:")
        print(f"  Capability: {info['required_capability']}")
        print(f"  Description: {info['description']}")
        for note in info['notes']:
            print(f"  • {note}")
