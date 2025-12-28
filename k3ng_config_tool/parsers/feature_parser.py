"""
Feature Parser for K3NG Configuration Files

Extracts FEATURE_* and OPTION_* defines from rotator_features.h
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .preprocessor_parser import PreprocessorParser, DefineNode
except ImportError:
    # For standalone testing
    from preprocessor_parser import PreprocessorParser, DefineNode


@dataclass
class FeatureCategory:
    """Categorizes features for UI organization"""
    name: str
    features: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class FeatureConfig:
    """Complete feature configuration"""
    features: Dict[str, DefineNode]  # All FEATURE_* defines
    options: Dict[str, DefineNode]   # All OPTION_* defines
    languages: Dict[str, DefineNode]  # All LANGUAGE_* defines
    categories: List[FeatureCategory]
    active_features: Set[str]  # Currently enabled features
    active_options: Set[str]   # Currently enabled options


class FeatureParser:
    """
    Parses FEATURE_* and OPTION_* defines from rotator_features.h

    Organizes features into logical categories for UI display
    """

    # Feature categories for UI organization
    FEATURE_CATEGORIES = {
        "Protocol Emulation": [
            "FEATURE_YAESU_EMULATION",
            "FEATURE_EASYCOM_EMULATION",
            "FEATURE_DCU_1_EMULATION",
        ],
        "Elevation Control": [
            "FEATURE_ELEVATION_CONTROL",
        ],
        "Tracking": [
            "FEATURE_MOON_TRACKING",
            "FEATURE_SUN_TRACKING",
            "FEATURE_SATELLITE_TRACKING",
            "FEATURE_AUTOCORRECT",
        ],
        "Clock & GPS": [
            "FEATURE_CLOCK",
            "FEATURE_GPS",
            "FEATURE_RTC_DS1307",
            "FEATURE_RTC_PCF8583",
        ],
        "Position Sensors (Azimuth)": [
            "FEATURE_AZ_POSITION_POTENTIOMETER",
            "FEATURE_AZ_POSITION_ROTARY_ENCODER",
            "FEATURE_AZ_POSITION_PULSE_INPUT",
            "FEATURE_AZ_POSITION_HMC5883L",
            "FEATURE_AZ_POSITION_HMC5883L_USING_JARZEBSKI_LIBRARY",
            "FEATURE_AZ_POSITION_POLOLU_LSM303",
            "FEATURE_AZ_POSITION_ADAFRUIT_LSM303",
            "FEATURE_AZ_POSITION_DFROBOT_QMC5883",
            "FEATURE_AZ_POSITION_MECHASOLUTION_QMC5883",
            "FEATURE_AZ_POSITION_HH12_AS5045_SSI",
            "FEATURE_AZ_POSITION_HH12_AS5045_SSI_RELATIVE",
            "FEATURE_AZ_POSITION_INCREMENTAL_ENCODER",
            "FEATURE_AZ_POSITION_A2_ABSOLUTE_ENCODER",
            "FEATURE_AZ_POSITION_GET_FROM_REMOTE_UNIT",
        ],
        "Position Sensors (Elevation)": [
            "FEATURE_EL_POSITION_POTENTIOMETER",
            "FEATURE_EL_POSITION_ROTARY_ENCODER",
            "FEATURE_EL_POSITION_PULSE_INPUT",
            "FEATURE_EL_POSITION_ADXL345_USING_ADAFRUIT_LIB",
            "FEATURE_EL_POSITION_ADXL345_USING_LOVE_ELECTRON_LIB",
            "FEATURE_EL_POSITION_POLOLU_LSM303",
            "FEATURE_EL_POSITION_ADAFRUIT_LSM303",
            "FEATURE_EL_POSITION_HH12_AS5045_SSI",
            "FEATURE_EL_POSITION_INCREMENTAL_ENCODER",
            "FEATURE_EL_POSITION_MEMSIC_2125",
            "FEATURE_EL_POSITION_A2_ABSOLUTE_ENCODER",
            "FEATURE_EL_POSITION_GET_FROM_REMOTE_UNIT",
        ],
        "Display": [
            "FEATURE_4_BIT_LCD_DISPLAY",
            "FEATURE_ADAFRUIT_I2C_LCD",
            "FEATURE_YOURDUINO_I2C_LCD",
            "FEATURE_RFROBOT_I2C_DISPLAY",
            "FEATURE_YWROBOT_I2C_DISPLAY",
            "FEATURE_SAINSMART_I2C_LCD",
            "FEATURE_MIDAS_I2C_DISPLAY",
            "FEATURE_FABO_LCD_PCF8574_DISPLAY",
            "FEATURE_NEXTION_DISPLAY",
            "FEATURE_TEST_DISPLAY_AT_STARTUP",
        ],
        "Motor Control": [
            "FEATURE_STEPPER_MOTOR",
            "FEATURE_ROTATION_INDICATOR_PIN",
        ],
        "Network & Remote": [
            "FEATURE_ETHERNET",
            "FEATURE_REMOTE_UNIT_SLAVE",
            "FEATURE_MASTER_WITH_SERIAL_SLAVE",
            "FEATURE_MASTER_WITH_ETHERNET_SLAVE",
            "FEATURE_MASTER_SEND_AZ_ROTATION_COMMANDS_TO_REMOTE",
            "FEATURE_MASTER_SEND_EL_ROTATION_COMMANDS_TO_REMOTE",
        ],
        "Calibration": [
            "FEATURE_AZIMUTH_CORRECTION",
            "FEATURE_ELEVATION_CORRECTION",
        ],
        "User Interface": [
            "FEATURE_JOYSTICK_CONTROL",
            "FEATURE_ROTATION_INDICATOR_PIN",
            "FEATURE_PARK",
            "FEATURE_AUTOPARK",
            "FEATURE_AUDIBLE_ALERT",
        ],
        "Advanced Features": [
            "FEATURE_LIMIT_SENSE",
            "FEATURE_AZ_ROTATION_STALL_DETECTION",
            "FEATURE_EL_ROTATION_STALL_DETECTION",
            "FEATURE_ANALOG_OUTPUT_PINS",
            "FEATURE_SNA",
            "FEATURE_POWER_SWITCH",
            "FEATURE_EL_SLOWSTART",
            "FEATURE_EL_SLOW_DOWN",
            "FEATURE_AZ_PRESET_ENCODER",
            "FEATURE_EL_PRESET_ENCODER",
            "FEATURE_ROTARY_ENCODER_SUPPORT",
            "FEATURE_LCD_DISPLAY",
            "FEATURE_I2C_LCD",
            "FEATURE_WIRE_SUPPORT",
        ],
    }

    def __init__(self, file_path: str):
        """Initialize with path to rotator_features.h"""
        self.file_path = Path(file_path)
        self.parser = PreprocessorParser(str(file_path))
        self.features: Dict[str, DefineNode] = {}
        self.options: Dict[str, DefineNode] = {}
        self.languages: Dict[str, DefineNode] = {}

    def parse(self) -> FeatureConfig:
        """
        Parse the features file and categorize defines

        Returns:
            FeatureConfig with all parsed features and options
        """
        result = self.parser.parse()

        if not result.success:
            raise ValueError(f"Failed to parse {self.file_path}: {result.errors}")

        # Categorize defines
        for name, define in result.defines.items():
            if name.startswith("FEATURE_"):
                self.features[name] = define
            elif name.startswith("OPTION_"):
                self.options[name] = define
            elif name.startswith("LANGUAGE_"):
                self.languages[name] = define

        # Determine active features
        active_features = {name for name, define in self.features.items() if define.is_active}
        active_options = {name for name, define in self.options.items() if define.is_active}

        # Build categories
        categories = self._build_categories()

        return FeatureConfig(
            features=self.features,
            options=self.options,
            languages=self.languages,
            categories=categories,
            active_features=active_features,
            active_options=active_options
        )

    def _build_categories(self) -> List[FeatureCategory]:
        """Build feature categories for UI organization"""
        categories = []

        for category_name, feature_names in self.FEATURE_CATEGORIES.items():
            # Only include features that exist in the file
            existing_features = [
                name for name in feature_names
                if name in self.features
            ]

            if existing_features:
                categories.append(FeatureCategory(
                    name=category_name,
                    features=existing_features,
                    description=None  # Could be enhanced with descriptions
                ))

        # Add uncategorized features
        categorized = set()
        for cat in categories:
            categorized.update(cat.features)

        uncategorized = [
            name for name in self.features.keys()
            if name not in categorized
        ]

        if uncategorized:
            categories.append(FeatureCategory(
                name="Other Features",
                features=sorted(uncategorized),
                description="Additional features not categorized"
            ))

        return categories

    def get_feature(self, name: str) -> Optional[DefineNode]:
        """Get a specific feature by name"""
        return self.features.get(name)

    def is_feature_enabled(self, name: str) -> bool:
        """Check if a feature is enabled"""
        return name in self.features and self.features[name].is_active

    def get_option(self, name: str) -> Optional[DefineNode]:
        """Get a specific option by name"""
        return self.options.get(name)

    def is_option_enabled(self, name: str) -> bool:
        """Check if an option is enabled"""
        return name in self.options and self.options[name].is_active

    def get_features_by_category(self, category: str) -> List[DefineNode]:
        """Get all features in a specific category"""
        for cat in self.FEATURE_CATEGORIES:
            if cat == category:
                return [
                    self.features[name]
                    for name in self.FEATURE_CATEGORIES[category]
                    if name in self.features
                ]
        return []

    def get_protocol_emulation(self) -> Optional[str]:
        """Get the active protocol emulation (only one should be active)"""
        protocols = [
            "FEATURE_YAESU_EMULATION",
            "FEATURE_EASYCOM_EMULATION",
            "FEATURE_DCU_1_EMULATION"
        ]
        for protocol in protocols:
            if self.is_feature_enabled(protocol):
                return protocol
        return None

    def get_az_position_sensor(self) -> Optional[str]:
        """Get the active azimuth position sensor"""
        for name in self.features:
            if name.startswith("FEATURE_AZ_POSITION_") and self.is_feature_enabled(name):
                return name
        return None

    def get_el_position_sensor(self) -> Optional[str]:
        """Get the active elevation position sensor"""
        for name in self.features:
            if name.startswith("FEATURE_EL_POSITION_") and self.is_feature_enabled(name):
                return name
        return None


def parse_features(file_path: str) -> FeatureConfig:
    """
    Convenience function to parse features file

    Args:
        file_path: Path to rotator_features.h

    Returns:
        FeatureConfig with all parsed data
    """
    parser = FeatureParser(file_path)
    return parser.parse()


if __name__ == "__main__":
    # Test the feature parser
    import sys

    if len(sys.argv) < 2:
        print("Usage: python feature_parser.py <rotator_features.h>")
        sys.exit(1)

    config = parse_features(sys.argv[1])

    print(f"Parsed {len(config.features)} features")
    print(f"Parsed {len(config.options)} options")
    print(f"Parsed {len(config.languages)} languages")
    print(f"\nActive features: {len(config.active_features)}")
    print(f"Active options: {len(config.active_options)}")

    print(f"\n{len(config.categories)} feature categories:")
    for category in config.categories:
        enabled_count = sum(1 for f in category.features if config.features[f].is_active)
        print(f"  {category.name}: {len(category.features)} features ({enabled_count} enabled)")

    # Show active configuration
    print("\n=== Active Configuration ===")
    print(f"Protocol: {FeatureParser(sys.argv[1]).get_protocol_emulation() or 'None'}")
    parser = FeatureParser(sys.argv[1])
    parser.parse()
    print(f"AZ Sensor: {parser.get_az_position_sensor() or 'None'}")
    print(f"EL Sensor: {parser.get_el_position_sensor() or 'None'}")
    print(f"Elevation Control: {'Yes' if parser.is_feature_enabled('FEATURE_ELEVATION_CONTROL') else 'No'}")
