"""
Settings Parser for K3NG Configuration Files

Extracts numeric parameters and calibration settings from rotator_settings.h
"""

from typing import Dict, List, Optional, Union, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import re

try:
    from .preprocessor_parser import PreprocessorParser, DefineNode
except ImportError:
    from preprocessor_parser import PreprocessorParser, DefineNode


@dataclass
class SettingDefinition:
    """Represents a numeric setting"""
    name: str
    value: Union[int, float, List[int], List[float], str, None]
    value_type: str  # 'int', 'float', 'array', 'string', 'unknown'
    unit: Optional[str] = None  # e.g., 'degrees', 'milliseconds', 'Hz'
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    comment: Optional[str] = None
    category: Optional[str] = None
    is_eeprom_persistent: bool = False
    line_number: int = 0

    def __repr__(self) -> str:
        value_str = str(self.value) if self.value is not None else "UNSET"
        if len(value_str) > 50:
            value_str = value_str[:47] + "..."
        unit_str = f" {self.unit}" if self.unit else ""
        eeprom_str = " [EEPROM]" if self.is_eeprom_persistent else ""
        return f"Setting({self.name} = {value_str}{unit_str}{eeprom_str})"


@dataclass
class SettingCategory:
    """Groups related settings"""
    name: str
    settings: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class SettingsConfig:
    """Complete settings configuration"""
    settings: Dict[str, SettingDefinition]
    categories: List[SettingCategory]
    eeprom_settings: Set[str]  # Settings that persist in EEPROM


class SettingsParser:
    """
    Parses numeric settings from rotator_settings.h

    Handles:
    - Integer values
    - Floating point values
    - Arrays (calibration tables)
    - Special constants
    - EEPROM-persistent settings
    """

    # Setting categories
    SETTING_CATEGORIES = {
        "EEPROM Initialization": [
            "AZIMUTH_STARTING_POINT_EEPROM_INITIALIZE",
            "AZIMUTH_ROTATION_CAPABILITY_EEPROM_INITIALIZE",
            "ANALOG_AZ_FULL_CCW_EEPROM_INITIALIZE",
            "ANALOG_AZ_FULL_CW_EEPROM_INITIALIZE",
            "ANALOG_EL_FULL_DOWN_EEPROM_INITIALIZE",
            "ANALOG_EL_FULL_UP_EEPROM_INITIALIZE",
        ],
        "Speed & Rotation": [
            "PWM_SPEED_VOLTAGE_X1", "PWM_SPEED_VOLTAGE_X2",
            "PWM_SPEED_VOLTAGE_X3", "PWM_SPEED_VOLTAGE_X4",
            "AZ_SLOWSTART_DEFAULT", "AZ_SLOWDOWN_DEFAULT",
            "AZ_SLOW_START_UP_TIME", "AZ_SLOW_START_STARTING_PWM",
            "AZ_SLOW_START_STEPS", "AZ_SLOW_DOWN_STEPS",
            "SLOW_DOWN_BEFORE_TARGET_AZ",
            "AZ_SLOW_DOWN_PWM_START", "AZ_SLOW_DOWN_PWM_STOP",
            "AZ_INITIALLY_IN_SLOW_DOWN_PWM",
        ],
        "Frequency Output": [
            "AZ_VARIABLE_FREQ_OUTPUT_LOW",
            "AZ_VARIABLE_FREQ_OUTPUT_HIGH",
            "EL_VARIABLE_FREQ_OUTPUT_LOW",
            "EL_VARIABLE_FREQ_OUTPUT_HIGH",
        ],
        "Tolerance & Limits": [
            "AZIMUTH_TOLERANCE", "ELEVATION_TOLERANCE",
            "AZIMUTH_MAXIMUM_DEGREES", "ELEVATION_MAXIMUM_DEGREES",
            "AZ_MANUAL_ROTATE_CCW_LIMIT", "AZ_MANUAL_ROTATE_CW_LIMIT",
            "EL_MANUAL_ROTATE_DOWN_LIMIT", "EL_MANUAL_ROTATE_UP_LIMIT",
            "OPERATION_TIMEOUT",
        ],
        "Display Settings": [
            "LCD_COLUMNS", "LCD_ROWS",
            "LCD_UPDATE_TIME",
            "DISPLAY_DECIMAL_PLACES",
        ],
        "Sensor Configuration": [
            "AZ_POSITION_ROTARY_ENCODER_DEG_PER_PULSE",
            "EL_POSITION_ROTARY_ENCODER_DEG_PER_PULSE",
            "AZ_POSITION_PULSE_DEG_PER_PULSE",
            "EL_POSITION_PULSE_DEG_PER_PULSE",
            "AZ_POSITION_INCREMENTAL_ENCODER_PULSES_PER_REV",
            "EL_POSITION_INCREMENTAL_ENCODER_PULSES_PER_REV",
        ],
        "Timing": [
            "ENCODER_PRESET_TIMEOUT",
            "REMOTE_BUFFER_TIMEOUT_MS",
            "AZ_MEASUREMENT_FREQUENCY_MS",
            "EL_MEASUREMENT_FREQUENCY_MS",
            "EEPROM_WRITE_DIRTY_CONFIG_TIME",
        ],
        "Calibration Tables": [
            "AZIMUTH_CALIBRATION_FROM_ARRAY",
            "AZIMUTH_CALIBRATION_TO_ARRAY",
            "ELEVATION_CALIBRATION_FROM_ARRAY",
            "ELEVATION_CALIBRATION_TO_ARRAY",
            "POLOLU_LSM_303_MIN_ARRAY",
            "POLOLU_LSM_303_MAX_ARRAY",
        ],
    }

    # Patterns for value parsing
    ARRAY_PATTERN = re.compile(r'\{([^}]+)\}')
    NUMBER_PATTERN = re.compile(r'^-?\d+\.?\d*$')

    def __init__(self, file_path: str):
        """Initialize with path to rotator_settings.h"""
        self.file_path = Path(file_path)
        self.parser = PreprocessorParser(str(file_path))
        self.settings: Dict[str, SettingDefinition] = {}

    def parse(self) -> SettingsConfig:
        """
        Parse the settings file and extract all numeric parameters

        Returns:
            SettingsConfig with all parsed settings
        """
        result = self.parser.parse()

        if not result.success:
            raise ValueError(f"Failed to parse {self.file_path}: {result.errors}")

        # Extract settings
        for name, define in result.defines.items():
            if self._is_setting_define(name):
                setting_def = self._parse_setting_definition(define)
                self.settings[name] = setting_def

        # Build categories
        categories = self._build_categories()

        # Identify EEPROM settings
        eeprom_settings = {
            name for name in self.settings.keys()
            if "_EEPROM_INITIALIZE" in name
        }

        return SettingsConfig(
            settings=self.settings,
            categories=categories,
            eeprom_settings=eeprom_settings
        )

    def _is_setting_define(self, name: str) -> bool:
        """Check if a define is a settings parameter"""
        # Exclude pin names and feature flags
        if name.startswith("FEATURE_") or name.startswith("OPTION_"):
            return False
        if name.startswith("LANGUAGE_"):
            return False

        # Common setting patterns
        setting_keywords = [
            "SPEED", "PWM", "FREQ", "TIMEOUT", "TIME", "DELAY",
            "TOLERANCE", "LIMIT", "MAXIMUM", "MINIMUM",
            "CALIBRATION", "ARRAY", "DEFAULT", "EEPROM",
            "VOLTAGE", "PULSE", "DEGREE", "COLUMNS", "ROWS",
            "UPDATE", "MEASUREMENT", "INTERVAL", "THRESHOLD"
        ]

        name_upper = name.upper()
        return any(keyword in name_upper for keyword in setting_keywords)

    def _parse_setting_definition(self, define: DefineNode) -> SettingDefinition:
        """Parse a single setting definition"""
        value_str = (define.value or "").strip()

        # Determine if EEPROM persistent
        is_eeprom = "_EEPROM_INITIALIZE" in define.name

        # Extract unit from comment if present
        unit = self._extract_unit(define.comment)

        # Parse value
        value, value_type = self._parse_value(value_str)

        # Infer min/max from name or comment
        min_val, max_val = self._infer_bounds(define.name, value, unit)

        # Categorize
        category = self._categorize_setting(define.name)

        return SettingDefinition(
            name=define.name,
            value=value,
            value_type=value_type,
            unit=unit,
            min_value=min_val,
            max_value=max_val,
            comment=define.comment,
            category=category,
            is_eeprom_persistent=is_eeprom,
            line_number=define.line_number
        )

    def _parse_value(self, value_str: str) -> tuple[Any, str]:
        """Parse value string into appropriate type"""
        if not value_str:
            return None, 'unknown'

        # Check for array
        array_match = self.ARRAY_PATTERN.search(value_str)
        if array_match:
            array_content = array_match.group(1)
            elements = [e.strip() for e in array_content.split(',')]

            # Try to parse as numbers
            try:
                # Check if any have decimal points
                if any('.' in e for e in elements):
                    return [float(e) for e in elements], 'array'
                else:
                    return [int(e) for e in elements], 'array'
            except ValueError:
                return elements, 'array'

        # Check for number
        if self.NUMBER_PATTERN.match(value_str):
            try:
                if '.' in value_str:
                    return float(value_str), 'float'
                else:
                    return int(value_str), 'int'
            except ValueError:
                pass

        # Otherwise treat as string
        return value_str, 'string'

    def _extract_unit(self, comment: Optional[str]) -> Optional[str]:
        """Extract unit from comment"""
        if not comment:
            return None

        comment_lower = comment.lower()

        # Common units
        units = {
            'degree': 'degrees',
            'millisecond': 'ms',
            'second': 's',
            'minute': 'min',
            'hz': 'Hz',
            'khz': 'kHz',
            'percent': '%',
            'volt': 'V',
            'pwm': 'PWM',
        }

        for keyword, unit in units.items():
            if keyword in comment_lower:
                return unit

        return None

    def _infer_bounds(self, name: str, value: Any, unit: Optional[str]) -> tuple[Optional[Union[int, float]], Optional[Union[int, float]]]:
        """Infer min/max bounds from name and context"""
        name_lower = name.lower()

        # PWM values: 0-255
        if 'pwm' in name_lower or 'voltage' in name_lower:
            return 0, 255

        # Frequency values depend on range
        if 'freq' in name_lower:
            if 'low' in name_lower:
                return 31, 1000
            elif 'high' in name_lower:
                return 31, 20000
            return 31, 20000

        # Degrees: typically 0-360 for azimuth, -90 to 180 for elevation
        if 'azimuth' in name_lower and ('degree' in name_lower or 'deg' in name_lower):
            return 0, 450  # Can be > 360 for overlap

        if 'elevation' in name_lower and ('degree' in name_lower or 'deg' in name_lower):
            return -20, 180

        # Tolerance: typically small positive values
        if 'tolerance' in name_lower:
            return 0.1, 10.0

        # Timeout/Time: milliseconds, typically 0-60000
        if 'timeout' in name_lower or 'time' in name_lower:
            return 0, 60000

        # Analog values: 0-1023 (10-bit ADC)
        if 'analog' in name_lower:
            return 0, 1023

        return None, None

    def _categorize_setting(self, name: str) -> Optional[str]:
        """Determine setting category"""
        for category, settings in self.SETTING_CATEGORIES.items():
            if name in settings:
                return category

        # Try to infer from name
        if 'EEPROM' in name:
            return "EEPROM Initialization"
        elif any(kw in name for kw in ['SPEED', 'PWM', 'SLOW']):
            return "Speed & Rotation"
        elif 'FREQ' in name:
            return "Frequency Output"
        elif any(kw in name for kw in ['TOLERANCE', 'LIMIT', 'MAXIMUM']):
            return "Tolerance & Limits"
        elif any(kw in name for kw in ['LCD', 'DISPLAY']):
            return "Display Settings"
        elif any(kw in name for kw in ['ENCODER', 'PULSE', 'SENSOR']):
            return "Sensor Configuration"
        elif any(kw in name for kw in ['TIME', 'TIMEOUT', 'DELAY', 'INTERVAL']):
            return "Timing"
        elif 'CALIBRATION' in name or 'ARRAY' in name:
            return "Calibration Tables"

        return "Other Settings"

    def _build_categories(self) -> List[SettingCategory]:
        """Build setting categories"""
        categories_dict: Dict[str, List[str]] = {}

        for name, setting in self.settings.items():
            category = setting.category or "Other Settings"
            if category not in categories_dict:
                categories_dict[category] = []
            categories_dict[category].append(name)

        categories = [
            SettingCategory(name=cat_name, settings=sorted(settings))
            for cat_name, settings in sorted(categories_dict.items())
        ]

        return categories

    def get_setting(self, name: str) -> Optional[SettingDefinition]:
        """Get a specific setting by name"""
        return self.settings.get(name)

    def get_settings_by_category(self, category: str) -> List[SettingDefinition]:
        """Get all settings in a specific category"""
        return [
            setting for setting in self.settings.values()
            if setting.category == category
        ]


def parse_settings(file_path: str) -> SettingsConfig:
    """
    Convenience function to parse settings file

    Args:
        file_path: Path to rotator_settings.h

    Returns:
        SettingsConfig with all parsed data
    """
    parser = SettingsParser(file_path)
    return parser.parse()


if __name__ == "__main__":
    # Test the settings parser
    import sys

    if len(sys.argv) < 2:
        print("Usage: python settings_parser.py <rotator_settings.h>")
        sys.exit(1)

    config = parse_settings(sys.argv[1])

    print(f"Parsed {len(config.settings)} settings")
    print(f"EEPROM-persistent settings: {len(config.eeprom_settings)}")

    print(f"\n{len(config.categories)} setting categories:")
    for category in config.categories:
        print(f"  {category.name}: {len(category.settings)} settings")

    # Show sample settings
    print("\nSample settings (first 15):")
    for i, (name, setting) in enumerate(list(config.settings.items())[:15]):
        print(f"  {setting}")

    # Show EEPROM settings
    print("\n EEPROM-persistent settings:")
    for name in sorted(config.eeprom_settings):
        setting = config.settings[name]
        print(f"  {setting}")
