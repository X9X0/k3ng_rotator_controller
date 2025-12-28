"""
Dependency Validator for K3NG Configuration

Validates feature dependencies, conflicts, and requirements based on rules
extracted from rotator_dependencies.h
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import yaml


class ValidationSeverity(Enum):
    """Severity level of validation issue"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: ValidationSeverity
    rule_type: str  # 'mutual_exclusivity', 'required_dependency', etc.
    message: str
    affected_features: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None
    auto_fixable: bool = False

    def __repr__(self) -> str:
        symbol = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[self.severity.value]
        features_str = ", ".join(self.affected_features) if self.affected_features else ""
        return f"{symbol} [{self.severity.value.upper()}] {self.message}\n   Affects: {features_str}"


@dataclass
class ValidationResult:
    """Result of validation"""
    passed: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    auto_fixes: List[str] = field(default_factory=list)  # Features to auto-enable/disable

    @property
    def total_issues(self) -> int:
        return len(self.errors) + len(self.warnings) + len(self.info)

    def __repr__(self) -> str:
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"ValidationResult({status}, {len(self.errors)} errors, {len(self.warnings)} warnings)"


class DependencyValidator:
    """
    Validates configuration dependencies using rule engine

    Loads rules from YAML and validates feature configurations
    """

    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize validator with rules file

        Args:
            rules_file: Path to YAML rules file (default: built-in rules)
        """
        if rules_file is None:
            # Use default rules file
            rules_file = Path(__file__).parent.parent / "data" / "validation_rules" / "dependencies.yaml"

        self.rules_file = Path(rules_file)
        self.rules: Dict[str, Any] = {}
        self._load_rules()

    def _load_rules(self):
        """Load validation rules from YAML file"""
        try:
            with open(self.rules_file, 'r') as f:
                self.rules = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load validation rules from {self.rules_file}: {e}")

    def validate(self, active_features: Set[str], active_options: Set[str]) -> ValidationResult:
        """
        Validate configuration against all rules

        Args:
            active_features: Set of active FEATURE_* defines
            active_options: Set of active OPTION_* defines

        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(passed=True)
        active_all = active_features | active_options

        # Run all validation rules
        self._validate_mutual_exclusivity(active_all, result)
        self._validate_required_dependencies(active_all, result)
        self._apply_auto_enablement(active_all, result)
        self._check_conditional_disable(active_all, result)

        # Mark as failed if any errors
        result.passed = len(result.errors) == 0

        return result

    def _validate_mutual_exclusivity(self, active: Set[str], result: ValidationResult):
        """Validate mutual exclusivity rules"""
        rules = self.rules.get('mutual_exclusivity', [])

        for rule in rules:
            group_name = rule['group']
            features = rule['features']
            max_count = rule.get('max_count', 1)
            min_count = rule.get('min_count', 0)
            when_condition = rule.get('when')

            # Check if rule applies (conditional rules)
            if when_condition and when_condition not in active:
                continue

            # Count active features in this group
            active_in_group = [f for f in features if f in active]
            count = len(active_in_group)

            # Check max count
            if count > max_count:
                result.errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule_type='mutual_exclusivity',
                    message=rule['error_message'],
                    affected_features=active_in_group,
                    suggestion=f"Disable all but one of: {', '.join(active_in_group)}"
                ))

            # Check min count
            if count < min_count:
                result.errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule_type='mutual_exclusivity',
                    message=rule['error_message'],
                    affected_features=features,
                    suggestion=f"Enable at least {min_count} from: {', '.join(features)}"
                ))

    def _validate_required_dependencies(self, active: Set[str], result: ValidationResult):
        """Validate required dependencies"""
        rules = self.rules.get('required_dependencies', [])

        for rule in rules:
            feature = rule['feature']

            # Skip if feature not active
            if feature not in active:
                continue

            # Check 'requires' (all must be present)
            if 'requires' in rule:
                required = rule['requires']
                missing = [r for r in required if r not in active]
                if missing:
                    result.errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        rule_type='required_dependency',
                        message=rule['error_message'],
                        affected_features=[feature] + missing,
                        suggestion=f"Enable: {', '.join(missing)}",
                        auto_fixable=True
                    ))
                    # Add to auto-fixes
                    result.auto_fixes.extend(missing)

            # Check 'requires_any' (at least one must be present)
            if 'requires_any' in rule:
                required_any = rule['requires_any']
                has_any = any(r in active for r in required_any)
                if not has_any:
                    result.errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        rule_type='required_dependency',
                        message=rule['error_message'],
                        affected_features=[feature] + required_any,
                        suggestion=f"Enable one of: {', '.join(required_any)}"
                    ))

            # Check 'conflicts_with' (none can be present)
            if 'conflicts_with' in rule:
                conflicts = rule['conflicts_with']
                conflicting = [c for c in conflicts if c in active]
                if conflicting:
                    result.errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        rule_type='conflict',
                        message=rule['error_message'],
                        affected_features=[feature] + conflicting,
                        suggestion=f"Disable: {', '.join(conflicting)}",
                        auto_fixable=True
                    ))

    def _apply_auto_enablement(self, active: Set[str], result: ValidationResult):
        """Check auto-enablement rules and suggest fixes"""
        rules = self.rules.get('auto_enablement', [])

        for rule in rules:
            should_enable = False

            # Check trigger (single feature)
            if 'trigger' in rule:
                trigger = rule['trigger']
                if isinstance(trigger, list):
                    should_enable = any(t in active for t in trigger)
                else:
                    should_enable = trigger in active

            # Check trigger_any (at least one)
            if 'trigger_any' in rule:
                trigger_any = rule['trigger_any']
                should_enable = any(t in active for t in trigger_any)

            if should_enable:
                auto_enable = rule['auto_enable']
                missing = [f for f in auto_enable if f not in active]

                if missing:
                    result.info.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        rule_type='auto_enablement',
                        message=rule['message'],
                        affected_features=missing,
                        suggestion=f"Auto-enable: {', '.join(missing)}",
                        auto_fixable=True
                    ))
                    result.auto_fixes.extend(missing)

    def _check_conditional_disable(self, active: Set[str], result: ValidationResult):
        """Check conditional disable rules"""
        rules = self.rules.get('conditional_disable', [])

        for rule in rules:
            feature = rule['feature']

            # Skip if feature not active
            if feature not in active:
                continue

            # Check if required features are present
            if 'requires' in rule:
                required = rule['requires']
                missing = [r for r in required if r not in active]

                if missing:
                    result.warnings.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        rule_type='conditional_disable',
                        message=rule['message'],
                        affected_features=[feature] + missing,
                        suggestion=f"Either enable {', '.join(missing)} or disable {feature}"
                    ))

    def get_auto_fixes(self, active_features: Set[str], active_options: Set[str]) -> Dict[str, Set[str]]:
        """
        Get auto-fix suggestions

        Args:
            active_features: Set of active features
            active_options: Set of active options

        Returns:
            Dict with 'enable' and 'disable' sets
        """
        result = self.validate(active_features, active_options)

        return {
            'enable': set(result.auto_fixes),
            'disable': set()  # Would be populated by conflict resolution
        }

    def explain_feature_requirements(self, feature: str) -> Dict[str, Any]:
        """
        Explain requirements for a specific feature

        Args:
            feature: Feature name to explain

        Returns:
            Dict with requirement information
        """
        info = {
            'requires': [],
            'requires_any': [],
            'conflicts_with': [],
            'auto_enables': [],
            'part_of_group': None
        }

        # Check required dependencies
        for rule in self.rules.get('required_dependencies', []):
            if rule['feature'] == feature:
                if 'requires' in rule:
                    info['requires'].extend(rule['requires'])
                if 'requires_any' in rule:
                    info['requires_any'].extend(rule['requires_any'])
                if 'conflicts_with' in rule:
                    info['conflicts_with'].extend(rule['conflicts_with'])

        # Check mutual exclusivity groups
        for rule in self.rules.get('mutual_exclusivity', []):
            if feature in rule['features']:
                info['part_of_group'] = {
                    'name': rule['group'],
                    'members': rule['features'],
                    'max_count': rule.get('max_count', 1)
                }

        # Check auto-enablement
        for rule in self.rules.get('auto_enablement', []):
            trigger = rule.get('trigger', [])
            trigger_any = rule.get('trigger_any', [])

            if feature in trigger or feature in trigger_any:
                info['auto_enables'].extend(rule['auto_enable'])

        return info


if __name__ == "__main__":
    # Test the validator
    print("Testing Dependency Validator\n")

    validator = DependencyValidator()

    # Test case 1: Valid configuration
    print("=== Test 1: Valid Configuration ===")
    active_features = {
        'FEATURE_YAESU_EMULATION',
        'FEATURE_AZ_POSITION_POTENTIOMETER',
        'FEATURE_ELEVATION_CONTROL',
        'FEATURE_EL_POSITION_POTENTIOMETER',
    }
    active_options = set()

    result = validator.validate(active_features, active_options)
    print(result)
    print(f"Auto-fixes suggested: {result.auto_fixes}\n")

    # Test case 2: Multiple protocols (error)
    print("=== Test 2: Multiple Protocols (Should Error) ===")
    active_features = {
        'FEATURE_YAESU_EMULATION',
        'FEATURE_EASYCOM_EMULATION',  # Conflict!
        'FEATURE_AZ_POSITION_POTENTIOMETER',
    }

    result = validator.validate(active_features, set())
    print(result)
    for error in result.errors:
        print(f"  {error}")
    print()

    # Test case 3: Missing dependency
    print("=== Test 3: Missing Dependency (Should Error) ===")
    active_features = {
        'FEATURE_MOON_TRACKING',  # Requires ELEVATION_CONTROL + CLOCK
        'FEATURE_AZ_POSITION_POTENTIOMETER',
    }

    result = validator.validate(active_features, set())
    print(result)
    for error in result.errors:
        print(f"  {error}")
    print()

    # Test case 4: Auto-enablement
    print("=== Test 4: Auto-Enablement (Should Suggest) ===")
    active_features = {
        'FEATURE_GPS',  # Should auto-enable FEATURE_CLOCK
        'FEATURE_AZ_POSITION_POTENTIOMETER',
    }
    active_options = {
        'OPTION_GPS_USE_TINY_GPS_LIBRARY',
    }

    result = validator.validate(active_features, active_options)
    print(result)
    for info in result.info:
        print(f"  {info}")
    print(f"Auto-fixes: {result.auto_fixes}\n")

    # Test case 5: Explain feature requirements
    print("=== Test 5: Explain Feature Requirements ===")
    requirements = validator.explain_feature_requirements('FEATURE_MOON_TRACKING')
    print(f"FEATURE_MOON_TRACKING requires:")
    print(f"  All of: {requirements['requires']}")
    print(f"  Conflicts with: {requirements['conflicts_with']}")
    print()
