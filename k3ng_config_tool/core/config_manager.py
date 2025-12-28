"""
Configuration Manager for K3NG Rotator Controller

Provides unified interface to all configuration aspects: features, pins, settings
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.feature_parser import FeatureParser, FeatureConfig
from parsers.pin_parser import PinParser, PinConfig
from parsers.settings_parser import SettingsParser, SettingsConfig
from validators.dependency_validator import DependencyValidator, ValidationResult
from validators.pin_validator import PinValidator
from validators.value_validator import ValueValidator
from boards.board_database import BoardDatabase
from generators.template_engine import TemplateEngine


@dataclass
class ConfigurationPaths:
    """Paths to K3NG configuration files"""
    project_dir: Path
    features_file: Path
    pins_file: Path
    settings_file: Path
    hardware_file: Optional[Path] = None

    @classmethod
    def from_project_dir(cls, project_dir: str) -> 'ConfigurationPaths':
        """Create paths from K3NG project directory"""
        base = Path(project_dir) / "k3ng_rotator_controller"
        return cls(
            project_dir=Path(project_dir),
            features_file=base / "rotator_features.h",
            pins_file=base / "rotator_pins.h",
            settings_file=base / "rotator_settings.h",
            hardware_file=base / "rotator_hardware.h"
        )


@dataclass
class ConfigurationSummary:
    """Summary of current configuration"""
    protocol: Optional[str]
    az_sensor: Optional[str]
    el_sensor: Optional[str]
    has_elevation: bool
    display_type: Optional[str]
    total_features: int
    enabled_features: int
    total_pins: int
    assigned_pins: int
    total_settings: int
    eeprom_settings: int
    validation_errors: int = 0
    validation_warnings: int = 0


class ConfigurationManager:
    """
    Main configuration management interface

    Provides:
    - Loading configuration from files
    - Querying configuration state
    - Modifying configuration
    - Validating configuration
    - Exporting configuration
    """

    def __init__(self, paths: ConfigurationPaths, board_id: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            paths: Paths to configuration files
            board_id: Arduino board identifier (e.g., 'arduino_mega_2560')
                     If None, pin validation will be skipped
        """
        self.paths = paths
        self.board_id = board_id
        self.features_config: Optional[FeatureConfig] = None
        self.pins_config: Optional[PinConfig] = None
        self.settings_config: Optional[SettingsConfig] = None
        self.validator = DependencyValidator()
        self.board_db = BoardDatabase()
        self.pin_validator = PinValidator(self.board_db)
        self.value_validator = ValueValidator()
        self.template_engine = TemplateEngine()
        self._loaded = False
        self._last_validation: Optional[ValidationResult] = None

    def load(self) -> bool:
        """
        Load all configuration files

        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse features
            feature_parser = FeatureParser(str(self.paths.features_file))
            self.features_config = feature_parser.parse()

            # Parse pins
            pin_parser = PinParser(str(self.paths.pins_file))
            self.pins_config = pin_parser.parse()

            # Parse settings
            settings_parser = SettingsParser(str(self.paths.settings_file))
            self.settings_config = settings_parser.parse()

            self._loaded = True
            return True

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def is_loaded(self) -> bool:
        """Check if configuration has been loaded"""
        return self._loaded

    def get_summary(self) -> ConfigurationSummary:
        """
        Get configuration summary

        Returns:
            ConfigurationSummary with key configuration details
        """
        if not self._loaded:
            raise RuntimeError("Configuration not loaded. Call load() first.")

        # Determine protocol
        protocol = None
        for proto in ["FEATURE_YAESU_EMULATION", "FEATURE_EASYCOM_EMULATION", "FEATURE_DCU_1_EMULATION"]:
            if proto in self.features_config.active_features:
                protocol = proto
                break

        # Determine AZ sensor
        az_sensor = None
        for name in self.features_config.active_features:
            if name.startswith("FEATURE_AZ_POSITION_"):
                az_sensor = name
                break

        # Determine EL sensor
        el_sensor = None
        has_elevation = "FEATURE_ELEVATION_CONTROL" in self.features_config.active_features
        if has_elevation:
            for name in self.features_config.active_features:
                if name.startswith("FEATURE_EL_POSITION_"):
                    el_sensor = name
                    break

        # Determine display type
        display_type = None
        display_features = [
            "FEATURE_4_BIT_LCD_DISPLAY",
            "FEATURE_ADAFRUIT_I2C_LCD",
            "FEATURE_NEXTION_DISPLAY",
            "FEATURE_YWROBOT_I2C_DISPLAY",
        ]
        for disp in display_features:
            if disp in self.features_config.active_features:
                display_type = disp
                break

        # Count assigned pins
        assigned_pins = sum(
            1 for pin in self.pins_config.pins.values()
            if not pin.is_disabled
        )

        return ConfigurationSummary(
            protocol=protocol,
            az_sensor=az_sensor,
            el_sensor=el_sensor,
            has_elevation=has_elevation,
            display_type=display_type,
            total_features=len(self.features_config.features),
            enabled_features=len(self.features_config.active_features),
            total_pins=len(self.pins_config.pins),
            assigned_pins=assigned_pins,
            total_settings=len(self.settings_config.settings),
            eeprom_settings=len(self.settings_config.eeprom_settings)
        )

    # Feature methods
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        if not self._loaded:
            return False
        return feature_name in self.features_config.active_features

    def enable_feature(self, feature_name: str):
        """Enable a feature"""
        if not self._loaded:
            raise RuntimeError("Configuration not loaded")

        if feature_name in self.features_config.features:
            self.features_config.features[feature_name].is_active = True
            self.features_config.features[feature_name].is_commented = False
            self.features_config.active_features.add(feature_name)

    def disable_feature(self, feature_name: str):
        """Disable a feature"""
        if not self._loaded:
            raise RuntimeError("Configuration not loaded")

        if feature_name in self.features_config.features:
            self.features_config.features[feature_name].is_active = False
            self.features_config.features[feature_name].is_commented = True
            self.features_config.active_features.discard(feature_name)

    def get_features_by_category(self, category: str) -> List[str]:
        """Get all features in a category"""
        if not self._loaded:
            return []

        for cat in self.features_config.categories:
            if cat.name == category:
                return cat.features
        return []

    # Pin methods
    def get_pin_assignment(self, pin_name: str) -> Optional[str]:
        """Get pin assignment"""
        if not self._loaded or pin_name not in self.pins_config.pins:
            return None

        pin_def = self.pins_config.pins[pin_name]
        return pin_def.pin_string

    def set_pin_assignment(self, pin_name: str, pin_value: str):
        """Set pin assignment"""
        if not self._loaded:
            raise RuntimeError("Configuration not loaded")

        if pin_name in self.pins_config.pins:
            pin_def = self.pins_config.pins[pin_name]
            pin_def.pin_string = pin_value

            # Parse the new value
            if pin_value.startswith('A'):
                pin_def.is_analog = True
                pin_def.is_disabled = False
                pin_def.pin_number = None
            else:
                try:
                    pin_num = int(pin_value)
                    pin_def.pin_number = pin_num
                    pin_def.is_disabled = (pin_num == 0)
                    pin_def.is_remote = (pin_num > 99)
                    pin_def.is_analog = False
                except ValueError:
                    pin_def.is_disabled = True

    def get_pin_conflicts(self) -> List[str]:
        """Get list of pin conflicts"""
        if not self._loaded:
            return []
        return self.pins_config.conflicts

    # Settings methods
    def get_setting_value(self, setting_name: str) -> Any:
        """Get setting value"""
        if not self._loaded or setting_name not in self.settings_config.settings:
            return None

        return self.settings_config.settings[setting_name].value

    def set_setting_value(self, setting_name: str, value: Any):
        """Set setting value"""
        if not self._loaded:
            raise RuntimeError("Configuration not loaded")

        if setting_name in self.settings_config.settings:
            self.settings_config.settings[setting_name].value = value

    def get_settings_by_category(self, category: str) -> List[str]:
        """Get all settings in a category"""
        if not self._loaded:
            return []

        for cat in self.settings_config.categories:
            if cat.name == category:
                return cat.settings
        return []

    # Export methods
    def export_to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary"""
        if not self._loaded:
            raise RuntimeError("Configuration not loaded")

        return {
            "features": {
                name: {
                    "enabled": define.is_active,
                    "comment": define.comment
                }
                for name, define in self.features_config.features.items()
            },
            "options": {
                name: {
                    "enabled": define.is_active,
                    "comment": define.comment
                }
                for name, define in self.features_config.options.items()
            },
            "pins": {
                name: {
                    "value": pin.pin_string,
                    "comment": pin.comment
                }
                for name, pin in self.pins_config.pins.items()
            },
            "settings": {
                name: {
                    "value": setting.value,
                    "unit": setting.unit,
                    "comment": setting.comment
                }
                for name, setting in self.settings_config.settings.items()
            }
        }

    def export_to_json(self, file_path: str):
        """Export configuration to JSON file"""
        data = self.export_to_dict()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_from_dict(self, data: Dict[str, Any]):
        """Import configuration from dictionary"""
        if not self._loaded:
            raise RuntimeError("Configuration not loaded")

        # Import features
        if "features" in data:
            for name, config in data["features"].items():
                if name in self.features_config.features:
                    if config.get("enabled"):
                        self.enable_feature(name)
                    else:
                        self.disable_feature(name)

        # Import pins
        if "pins" in data:
            for name, config in data["pins"].items():
                self.set_pin_assignment(name, config.get("value", "0"))

        # Import settings
        if "settings" in data:
            for name, config in data["settings"].items():
                self.set_setting_value(name, config.get("value"))

    def import_from_json(self, file_path: str):
        """Import configuration from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.import_from_dict(data)

    # Validation methods
    def validate(self, board_id: Optional[str] = None) -> ValidationResult:
        """
        Validate current configuration

        Args:
            board_id: Arduino board identifier for pin validation
                     (overrides constructor board_id if provided)

        Returns:
            ValidationResult with errors, warnings, and auto-fix suggestions
        """
        if not self._loaded:
            raise RuntimeError("Configuration not loaded. Call load() first.")

        # Run dependency validation
        result = self.validator.validate(
            self.features_config.active_features,
            self.features_config.active_options
        )

        # Run pin validation if board is specified
        board = board_id or self.board_id
        if board:
            # Build pin assignments dict from pins_config
            pin_assignments = {
                name: pin.pin_string
                for name, pin in self.pins_config.pins.items()
            }

            pin_result = self.pin_validator.validate(
                board,
                pin_assignments,
                self.features_config.active_features
            )

            # Merge pin validation results into main result
            result.errors.extend(pin_result.errors)
            result.warnings.extend(pin_result.warnings)
            result.info.extend(pin_result.info)

            # Update passed status
            if not pin_result.passed:
                result.passed = False

        # Run value validation on settings
        settings_values = {
            name: setting.value
            for name, setting in self.settings_config.settings.items()
        }

        value_result = self.value_validator.validate(settings_values)

        # Merge value validation results into main result
        result.errors.extend(value_result.errors)
        result.warnings.extend(value_result.warnings)
        result.info.extend(value_result.info)

        # Update passed status
        if not value_result.passed:
            result.passed = False

        self._last_validation = result
        return result

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation summary

        Returns:
            Dict with validation statistics
        """
        if self._last_validation is None:
            self.validate()

        return {
            'passed': self._last_validation.passed,
            'error_count': len(self._last_validation.errors),
            'warning_count': len(self._last_validation.warnings),
            'info_count': len(self._last_validation.info),
            'auto_fixes_available': len(self._last_validation.auto_fixes)
        }

    def apply_auto_fixes(self) -> int:
        """
        Apply auto-fix suggestions from last validation

        Returns:
            Number of features auto-enabled
        """
        if self._last_validation is None:
            self.validate()

        count = 0
        for feature in self._last_validation.auto_fixes:
            if feature in self.features_config.features:
                self.enable_feature(feature)
                count += 1

        return count

    def explain_feature(self, feature_name: str) -> Dict[str, Any]:
        """
        Explain requirements and dependencies for a feature

        Args:
            feature_name: Feature to explain

        Returns:
            Dict with requirement information
        """
        return self.validator.explain_feature_requirements(feature_name)

    # Board management methods
    def set_board(self, board_id: str):
        """
        Set Arduino board for pin validation

        Args:
            board_id: Board identifier (e.g., 'arduino_mega_2560')
        """
        board = self.board_db.get_board(board_id)
        if not board:
            raise ValueError(f"Unknown board: {board_id}")
        self.board_id = board_id

    def get_board(self) -> Optional[str]:
        """
        Get currently selected board

        Returns:
            Board identifier or None
        """
        return self.board_id

    def list_boards(self) -> List[Dict[str, str]]:
        """
        List available Arduino boards

        Returns:
            List of board info dicts
        """
        return self.board_db.list_boards()

    def get_board_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get summary of currently selected board

        Returns:
            Board summary dict or None if no board selected
        """
        if not self.board_id:
            return None
        return self.board_db.get_board_summary(self.board_id)

    # Code generation methods
    def generate_files(self, output_dir: str, suffix: str = '') -> List[str]:
        """
        Generate configuration .h files

        Args:
            output_dir: Directory to write files to
            suffix: Optional suffix for filenames (e.g., '_custom' or '_backup')

        Returns:
            List of generated file paths
        """
        if not self._loaded:
            raise RuntimeError("Configuration not loaded. Call load() first.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate all files
        files = self.template_engine.generate_all(
            self.features_config,
            self.pins_config,
            self.settings_config
        )

        generated_paths = []
        for filename, content in files.items():
            # Add suffix if provided
            if suffix:
                base_name = filename.replace('.h', '')
                filename = f"{base_name}{suffix}.h"

            file_path = output_path / filename
            with open(file_path, 'w') as f:
                f.write(content)

            generated_paths.append(str(file_path))

        return generated_paths

    def generate_to_project(self, backup: bool = True) -> List[str]:
        """
        Generate configuration files back to the project directory

        Args:
            backup: If True, creates .bak backup files before overwriting

        Returns:
            List of generated file paths
        """
        if not self._loaded:
            raise RuntimeError("Configuration not loaded. Call load() first.")

        output_dir = self.paths.project_dir / "k3ng_rotator_controller"

        # Create backups if requested
        if backup:
            for original_file in [self.paths.features_file, self.paths.pins_file, self.paths.settings_file]:
                if original_file.exists():
                    backup_file = Path(str(original_file) + '.bak')
                    import shutil
                    shutil.copy2(original_file, backup_file)

        # Generate files
        return self.generate_files(str(output_dir), suffix='')

    def preview_generation(self) -> Dict[str, str]:
        """
        Preview generated configuration files without writing to disk

        Returns:
            Dict mapping filename -> content
        """
        if not self._loaded:
            raise RuntimeError("Configuration not loaded. Call load() first.")

        return self.template_engine.generate_all(
            self.features_config,
            self.pins_config,
            self.settings_config
        )


if __name__ == "__main__":
    # Test the configuration manager
    import sys

    if len(sys.argv) < 2:
        print("Usage: python config_manager.py <k3ng_project_dir>")
        sys.exit(1)

    # Load configuration
    paths = ConfigurationPaths.from_project_dir(sys.argv[1])
    manager = ConfigurationManager(paths)

    print("Loading configuration...")
    if manager.load():
        print("✓ Configuration loaded successfully")

        summary = manager.get_summary()
        print("\n=== Configuration Summary ===")
        print(f"Protocol: {summary.protocol or 'None'}")
        print(f"AZ Sensor: {summary.az_sensor or 'None'}")
        print(f"EL Sensor: {summary.el_sensor or 'None (elevation disabled)' if not summary.has_elevation else summary.el_sensor or 'None'}")
        print(f"Elevation Control: {'Yes' if summary.has_elevation else 'No'}")
        print(f"Display: {summary.display_type or 'None'}")
        print(f"\nFeatures: {summary.enabled_features}/{summary.total_features} enabled")
        print(f"Pins: {summary.assigned_pins}/{summary.total_pins} assigned")
        print(f"Settings: {summary.total_settings} total ({summary.eeprom_settings} EEPROM-persistent)")

        if manager.get_pin_conflicts():
            print(f"\n⚠️  {len(manager.get_pin_conflicts())} pin conflicts detected")
        else:
            print("\n✓ No pin conflicts")

        # Test export
        print("\nExporting to JSON...")
        manager.export_to_json("/tmp/k3ng_config_export.json")
        print("✓ Exported to /tmp/k3ng_config_export.json")

    else:
        print("✗ Failed to load configuration")
        sys.exit(1)
