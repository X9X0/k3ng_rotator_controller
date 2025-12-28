# K3NG Rotator Configuration & Testing Utility

A comprehensive Python application for configuring and testing the K3NG rotator controller.

## Features

- **Configuration Management**: Parse, validate, and generate K3NG configuration files
- **Hardware Board Support**: Arduino Uno, Mega, Leonardo, Teensy, Due with pin validation
- **Dependency Validation**: Automatic checking of feature dependencies and conflicts
- **Serial Testing**: Comprehensive I/O testing via serial commands
- **Calibration Wizards**: Guided magnetometer and angular calibration workflows
- **GUI Interface**: Modern PyQt6-based graphical interface

## Project Status

**Phase 1 (Foundation) - COMPLETED** ✅

- ✅ Project structure created
- ✅ Core preprocessor parser (handles #define, #ifdef, commented defines)
- ✅ Feature parser (FEATURE_*, OPTION_*, LANGUAGE_*)
- ✅ Pin parser (digital, analog, remote pins with conflict detection)
- ✅ Settings parser (numeric parameters, arrays, EEPROM settings)
- ✅ Configuration manager (unified API)
- ✅ Successfully tested on real K3NG configuration files

## Installation

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command-Line Testing

```bash
# Test configuration manager
python3 -m k3ng_config_tool.core.config_manager /path/to/k3ng_project

# Test individual parsers
python3 -m k3ng_config_tool.parsers.feature_parser rotator_features.h
python3 -m k3ng_config_tool.parsers.pin_parser rotator_pins.h
python3 -m k3ng_config_tool.parsers.settings_parser rotator_settings.h
```

### Python API

```python
from k3ng_config_tool.core.config_manager import ConfigurationManager, ConfigurationPaths

# Load configuration
paths = ConfigurationPaths.from_project_dir("/path/to/k3ng_project")
manager = ConfigurationManager(paths)
manager.load()

# Get summary
summary = manager.get_summary()
print(f"Protocol: {summary.protocol}")
print(f"Features enabled: {summary.enabled_features}/{summary.total_features}")

# Modify configuration
manager.enable_feature("FEATURE_ELEVATION_CONTROL")
manager.set_pin_assignment("rotate_cw", "6")
manager.set_setting_value("AZIMUTH_TOLERANCE", 2.0)

# Export configuration
manager.export_to_json("my_config.json")
```

## Current Parsing Capabilities

### Successfully Parses:

**rotator_features.h**:
- 77 FEATURE_* defines
- 74 OPTION_* defines
- 9 LANGUAGE_* defines
- Correctly identifies enabled vs. disabled (commented) features

**rotator_pins.h**:
- 113 pin definitions
- Digital pins (0-99)
- Analog pins (A0-A15)
- Remote pins (>99)
- Disabled pins (0)
- Detects 10+ pin conflicts (due to conditional compilation)

**rotator_settings.h**:
- 111 numeric settings
- 6 EEPROM-persistent settings
- 9 categories (Speed, Timing, Calibration, etc.)
- Arrays (calibration tables)
- Automatic unit detection (degrees, ms, Hz, etc.)

### Test Results:

```
Configuration loaded successfully ✓
Protocol: FEATURE_YAESU_EMULATION
AZ Sensor: FEATURE_AZ_POSITION_POTENTIOMETER
Features: 2/77 enabled
Pins: 47/113 assigned
Settings: 111 total (6 EEPROM-persistent)
```

## Architecture

```
k3ng_config_tool/
├── core/                    # Core application logic
│   ├── config_manager.py    # Main configuration API
│   ├── project_manager.py   # [TODO] File operations
│   └── export_manager.py    # [TODO] Export coordinator
├── parsers/                 # C code parsing ✅
│   ├── preprocessor_parser.py  # #define/#ifdef parser
│   ├── feature_parser.py       # FEATURE_* extraction
│   ├── pin_parser.py          # Pin definitions
│   └── settings_parser.py     # Numeric settings
├── validators/              # [TODO] Validation engine
├── generators/              # [TODO] Code generation
├── boards/                  # [TODO] Arduino board database
├── serial/                  # [TODO] Serial communication
├── testing/                 # [TODO] Test framework
└── gui/                     # [TODO] PyQt6 interface
```

## Next Steps (Phase 2 - Validation)

1. Implement dependency validator
2. Create validation_rules.yaml from rotator_dependencies.h
3. Implement pin validator with board awareness
4. Add value range validation
5. Unit tests for all validators

## Data Model

### DefineNode
Represents a #define statement with:
- name, value
- comment, line_number
- is_active, is_commented
- conditional_scope

### PinDefinition
Represents a pin assignment with:
- name, pin_number, pin_string
- is_analog, is_disabled, is_remote
- feature_dependency, comment

### SettingDefinition
Represents a numeric setting with:
- name, value, value_type
- unit, min_value, max_value
- category, is_eeprom_persistent

## Dependencies

- **PyQt6**: GUI framework
- **pyserial**: Serial communication
- **Jinja2**: Template engine for code generation
- **matplotlib**: Calibration data visualization
- **pytest**: Unit testing

See `requirements.txt` for complete list.

## Contributing

This is a work in progress. Phase 1 (Foundation) is complete.

## License

Compatible with K3NG rotator controller project license.

## Author

Created with Claude Code for the K3NG rotator controller community.
