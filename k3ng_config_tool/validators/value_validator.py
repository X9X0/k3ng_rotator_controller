"""
Value Range Validator

Validates numeric setting values against range constraints
"""

from typing import Dict, List, Set, Optional, Any, Union
from pathlib import Path
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators.dependency_validator import ValidationSeverity, ValidationIssue, ValidationResult


class ValueValidator:
    """
    Value range validator

    Validates:
    - Numeric ranges (PWM 0-255, angles, frequencies)
    - Allowed value lists (baud rates)
    - Array constraints (calibration tables)
    - Consistency checks (ascending order)
    """

    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize value validator

        Args:
            rules_file: Path to YAML rules file (default: built-in rules)
        """
        if rules_file is None:
            # Use default rules file
            rules_file = Path(__file__).parent.parent / "data" / "validation_rules" / "values.yaml"

        self.rules_file = Path(rules_file)
        self.rules: Dict[str, Any] = {}
        self._load_rules()

        # Build setting -> rule mapping for fast lookup
        self._setting_rules: Dict[str, List[Dict[str, Any]]] = {}
        self._build_setting_index()

    def _load_rules(self):
        """Load validation rules from YAML file"""
        try:
            with open(self.rules_file, 'r') as f:
                self.rules = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load value validation rules from {self.rules_file}: {e}")

    def _build_setting_index(self):
        """Build index of setting_name -> validation rules"""
        for category, rule_list in self.rules.items():
            if not isinstance(rule_list, list):
                continue

            for rule in rule_list:
                if 'settings' not in rule:
                    continue

                for setting_name in rule['settings']:
                    if setting_name not in self._setting_rules:
                        self._setting_rules[setting_name] = []

                    # Add rule with category info
                    rule_copy = rule.copy()
                    rule_copy['category'] = category
                    self._setting_rules[setting_name].append(rule_copy)

    def validate(self, settings: Dict[str, Any]) -> ValidationResult:
        """
        Validate setting values

        Args:
            settings: Dict of setting_name -> value

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(passed=True)

        for setting_name, value in settings.items():
            if setting_name not in self._setting_rules:
                continue

            rules = self._setting_rules[setting_name]
            for rule in rules:
                self._validate_setting(setting_name, value, rule, result)

        return result

    def _validate_setting(self, setting_name: str, value: Any,
                         rule: Dict[str, Any], result: ValidationResult):
        """Validate a single setting against a rule"""

        # Skip validation if value is None or empty
        if value is None:
            return

        # Handle array values
        if isinstance(value, (list, tuple)):
            self._validate_array(setting_name, value, rule, result)
            return

        # Convert value to number for numeric validation
        try:
            if isinstance(value, str):
                # Try to parse as float
                numeric_value = float(value)
            elif isinstance(value, (int, float)):
                numeric_value = value
            else:
                # Can't validate non-numeric
                return
        except (ValueError, TypeError):
            # Not a number, skip numeric validation
            return

        # Check min/max range
        if 'min' in rule and numeric_value < rule['min']:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                rule_type='value_range',
                message=f"{setting_name} = {value} is below minimum {rule['min']} {rule.get('unit', '')}",
                affected_features=[setting_name],
                suggestion=f"Set {setting_name} to a value between {rule['min']} and {rule.get('max', 'infinity')}"
            ))
            result.passed = False

        if 'max' in rule and numeric_value > rule['max']:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                rule_type='value_range',
                message=f"{setting_name} = {value} exceeds maximum {rule['max']} {rule.get('unit', '')}",
                affected_features=[setting_name],
                suggestion=f"Set {setting_name} to a value between {rule.get('min', 0)} and {rule['max']}"
            ))
            result.passed = False

        # Check warning range
        if 'warning_min' in rule and numeric_value < rule['warning_min']:
            result.warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type='value_range',
                message=f"{setting_name} = {value} is low",
                affected_features=[setting_name],
                suggestion=rule.get('warning_message', f"Consider increasing {setting_name}")
            ))

        if 'warning_max' in rule and numeric_value > rule['warning_max']:
            result.warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type='value_range',
                message=f"{setting_name} = {value} is high",
                affected_features=[setting_name],
                suggestion=rule.get('warning_message', f"Consider decreasing {setting_name}")
            ))

        # Check allowed values
        if 'allowed_values' in rule:
            # Convert to int if value is whole number
            if isinstance(numeric_value, float) and numeric_value.is_integer():
                numeric_value = int(numeric_value)

            if numeric_value not in rule['allowed_values']:
                result.errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule_type='allowed_values',
                    message=f"{setting_name} = {value} is not a valid value",
                    affected_features=[setting_name],
                    suggestion=f"Allowed values: {rule['allowed_values']}"
                ))
                result.passed = False

    def _validate_array(self, setting_name: str, value: Union[List, tuple],
                       rule: Dict[str, Any], result: ValidationResult):
        """Validate array values"""

        # Check array size
        if 'array_min_size' in rule and len(value) < rule['array_min_size']:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                rule_type='array_size',
                message=f"{setting_name} has {len(value)} entries, minimum is {rule['array_min_size']}",
                affected_features=[setting_name],
                suggestion=f"Add at least {rule['array_min_size'] - len(value)} more entries"
            ))
            result.passed = False

        if 'array_max_size' in rule and len(value) > rule['array_max_size']:
            result.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                rule_type='array_size',
                message=f"{setting_name} has {len(value)} entries, maximum is {rule['array_max_size']}",
                affected_features=[setting_name],
                suggestion=f"Remove {len(value) - rule['array_max_size']} entries"
            ))
            result.passed = False

        # Check consistency (ascending order)
        if rule.get('consistency_check') == 'ascending':
            for i in range(len(value) - 1):
                try:
                    if float(value[i]) >= float(value[i + 1]):
                        result.warnings.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            rule_type='array_consistency',
                            message=f"{setting_name}[{i}] = {value[i]} >= {setting_name}[{i+1}] = {value[i+1]}",
                            affected_features=[setting_name],
                            suggestion=rule.get('consistency_message', 'Values should be in ascending order')
                        ))
                except (ValueError, TypeError):
                    # Can't compare, skip
                    pass

        # Validate each array element against min/max
        for i, element in enumerate(value):
            try:
                numeric_value = float(element) if isinstance(element, str) else element

                if 'min' in rule and numeric_value < rule['min']:
                    result.errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        rule_type='value_range',
                        message=f"{setting_name}[{i}] = {element} is below minimum {rule['min']}",
                        affected_features=[setting_name],
                        suggestion=f"Set to value between {rule['min']} and {rule.get('max', 'infinity')}"
                    ))
                    result.passed = False

                if 'max' in rule and numeric_value > rule['max']:
                    result.errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        rule_type='value_range',
                        message=f"{setting_name}[{i}] = {element} exceeds maximum {rule['max']}",
                        affected_features=[setting_name],
                        suggestion=f"Set to value between {rule.get('min', 0)} and {rule['max']}"
                    ))
                    result.passed = False

            except (ValueError, TypeError):
                # Can't validate non-numeric
                continue

    def get_setting_constraints(self, setting_name: str) -> Optional[Dict[str, Any]]:
        """
        Get validation constraints for a setting

        Args:
            setting_name: Setting name

        Returns:
            Dict with constraints or None if no rules
        """
        if setting_name not in self._setting_rules:
            return None

        # Merge all rules for this setting
        constraints = {
            'rules': self._setting_rules[setting_name],
            'has_range': False,
            'has_allowed_values': False,
        }

        for rule in self._setting_rules[setting_name]:
            if 'min' in rule or 'max' in rule:
                constraints['has_range'] = True
                constraints['min'] = rule.get('min')
                constraints['max'] = rule.get('max')
                constraints['unit'] = rule.get('unit')

            if 'allowed_values' in rule:
                constraints['has_allowed_values'] = True
                constraints['allowed_values'] = rule['allowed_values']

        return constraints


if __name__ == "__main__":
    # Test the value validator
    print("=== Value Validator Test ===\n")

    validator = ValueValidator()

    # Test case 1: Valid PWM value
    print("Test 1: Valid PWM value")
    settings = {
        'NORMAL_AZ_SPEED_VOLTAGE': 200,
    }
    result = validator.validate(settings)
    if result.passed:
        print("✓ Validation passed\n")
    else:
        print(f"✗ {len(result.errors)} error(s):\n")
        for error in result.errors:
            print(f"  • {error.message}")
        print()

    # Test case 2: PWM value out of range
    print("Test 2: PWM value out of range (300 > 255)")
    settings = {
        'NORMAL_AZ_SPEED_VOLTAGE': 300,
    }
    result = validator.validate(settings)
    if result.passed:
        print("✓ Validation passed\n")
    else:
        print(f"✗ {len(result.errors)} error(s):\n")
        for error in result.errors:
            print(f"  • {error.message}")
            if error.suggestion:
                print(f"    💡 {error.suggestion}")
        print()

    # Test case 3: Angle out of range
    print("Test 3: Azimuth angle out of range (400 > 360)")
    settings = {
        'AZIMUTH_STARTING_POINT': 400,
    }
    result = validator.validate(settings)
    if result.passed:
        print("✓ Validation passed\n")
    else:
        print(f"✗ {len(result.errors)} error(s):\n")
        for error in result.errors:
            print(f"  • {error.message}")
            if error.suggestion:
                print(f"    💡 {error.suggestion}")
        print()

    # Test case 4: Low speed warning
    print("Test 4: Low motor speed (warning at <50)")
    settings = {
        'NORMAL_AZ_SPEED_VOLTAGE': 30,
    }
    result = validator.validate(settings)
    print(f"Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        print(f"  ⚠️  {warning.message}")
        if warning.suggestion:
            print(f"     💡 {warning.suggestion}")
    print()

    # Test case 5: Multiple settings
    print("Test 5: Multiple settings with mixed results")
    settings = {
        'NORMAL_AZ_SPEED_VOLTAGE': 200,  # Valid
        'AZIMUTH_STARTING_POINT': 450,   # Error (>360)
        'ELEVATION_MAXIMUM_DEGREES': 90,  # Valid
        'NORMAL_EL_SPEED_VOLTAGE': -10,   # Error (<0)
    }
    result = validator.validate(settings)
    print(f"Result: {len(result.errors)} errors, {len(result.warnings)} warnings")
    for error in result.errors:
        print(f"  ✗ {error.message}")
    print()

    # Test constraint lookup
    print("Test 6: Get constraints for setting")
    constraints = validator.get_setting_constraints('NORMAL_AZ_SPEED_VOLTAGE')
    if constraints:
        print(f"NORMAL_AZ_SPEED_VOLTAGE constraints:")
        print(f"  Range: {constraints.get('min')} - {constraints.get('max')} {constraints.get('unit')}")
    print()
