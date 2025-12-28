# K3NG Configuration & Testing Utility

Professional Python GUI application for configuring and testing the K3NG rotator controller.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

## Features

✨ **Visual Configuration** - Point-and-click interface for all 77 features and 60+ options
🔧 **Smart Validation** - Automatic dependency checking and conflict detection
📊 **Hardware Testing** - 29 automated tests for I/O, motors, sensors, and calibration
🧭 **Calibration Wizards** - Step-by-step compass and angular correction calibration
📱 **Board Support** - Arduino Uno, Mega, Leonardo, Teensy, Due
💾 **Code Generation** - Export validated configuration files
📈 **Data Visualization** - Matplotlib plots for calibration analysis

## Quick Start

### Easy Installation (Recommended)

**Linux / macOS:**
```bash
git clone https://github.com/X9X0/k3ng_rotator_controller.git
cd k3ng_rotator_controller/k3ng_config_tool
./launch.sh
```

**Windows:**
```cmd
# Clone or download repository, then:
cd k3ng_rotator_controller\k3ng_config_tool
launch.bat
```

The launcher automatically:
- ✅ Sets up virtual environment
- ✅ Installs dependencies
- ✅ Creates global commands (`k3ng-gui`, `k3ng-cli`)
- ✅ Offers desktop shortcut
- ✅ Launches the application

### Manual Installation

```bash
# Clone repository
git clone https://github.com/X9X0/k3ng_rotator_controller.git
cd k3ng_rotator_controller/k3ng_config_tool

# Install dependencies
pip install -r requirements.txt

# Launch GUI
python3 gui_main.py
```

### Basic Workflow

1. **Open Project**: File → Open Project → select K3NG directory
2. **Configure Features**: Enable/disable features in left panel
3. **Assign Pins**: Set pin numbers for your board
4. **Validate**: Check for errors and dependencies
5. **Export**: Generate configuration files
6. **Compile**: Upload to Arduino using Arduino IDE

## Screenshots

### Feature Configuration
```
┌─────────────────────────────────────────────────┐
│ Features                                        │
├─────────────────────────────────────────────────┤
│ ✅ Protocol Emulation                          │
│   ✅ FEATURE_YAESU_EMULATION                   │
│   ☐ FEATURE_EASYCOM_EMULATION                  │
│ ✅ Position Sensors (Azimuth)                  │
│   ✅ FEATURE_AZ_POSITION_POTENTIOMETER         │
│   ☐ FEATURE_AZ_POSITION_ROTARY_ENCODER         │
│ ✅ Display                                      │
│   ✅ FEATURE_4_BIT_LCD_DISPLAY                 │
└─────────────────────────────────────────────────┘
```

### Validation Panel
```
┌─────────────────────────────────────────────────┐
│ ✅ Validation Passed (2 suggestions)           │
├─────────────────────────────────────────────────┤
│ Errors (0) │ Warnings (1) │ Info (1)           │
├─────────────────────────────────────────────────┤
│ ⚠️  Consider enabling FEATURE_ELEVATION_CONTROL│
│     Suggestion: Adds EL support for tracking   │
└─────────────────────────────────────────────────┘
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and development
- **[Phase Completion Docs](docs/)** - Implementation milestones

## System Requirements

- **Python**: 3.10 or higher
- **OS**: Windows, macOS, or Linux
- **Hardware**: K3NG rotator controller (optional, for testing)

## Dependencies

- **PyQt6** - Modern GUI framework
- **pyserial** - Serial communication
- **Jinja2** - Template engine
- **matplotlib** - Calibration visualization
- **pyyaml** - Configuration files

See [requirements.txt](requirements.txt) for complete list.

## Architecture

```
k3ng_config_tool/
├── core/                   # Configuration management
├── parsers/                # C code parsing (features, pins, settings)
├── validators/             # Dependency validation engine
├── generators/             # Jinja2 template-based code generation
├── boards/                 # Arduino board definitions
├── k3ng_serial/            # Serial communication
├── testing/                # Test framework and calibration
│   ├── tests/              # Hardware test suites
│   └── calibration/        # Calibration wizards
└── gui/                    # PyQt6 user interface
    ├── widgets/            # Custom widgets
    └── dialogs/            # Dialog windows
```

## Implementation Status

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Foundation & Parsing | ✅ Complete |
| 2 | Validation Engine | ✅ Complete |
| 3 | Board Database | ✅ Complete |
| 4 | GUI Foundation | ✅ Complete |
| 5 | Code Generation | ✅ Complete |
| 6 | Serial Communication | ✅ Complete |
| 7 | Testing Framework | ✅ Complete |
| 8 | Calibration Wizards | ✅ Complete |
| 9 | Validation Panel | ✅ Complete |
| 10 | Documentation & Polish | ✅ Complete |

## Usage Examples

### CLI Mode

```bash
# Parse configuration
python3 main.py parse /path/to/k3ng_rotator_controller

# Validate configuration
python3 main.py validate /path/to/k3ng_rotator_controller

# Export configuration
python3 main.py export /path/to/k3ng_rotator_controller
```

### Python API

```python
from parsers.feature_parser import FeatureParser
from validators.dependency_validator import DependencyValidator
from generators.template_engine import TemplateEngine

# Parse features
parser = FeatureParser('rotator_features.h')
config = parser.parse()

# Validate
validator = DependencyValidator()
result = validator.validate(config.active_features, set())

# Generate code
engine = TemplateEngine()
output = engine.render_features(config)
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest testing/tests/motor_tests.py
```

### Hardware Testing

1. Connect Arduino via USB
2. Launch GUI: `python3 gui_main.py`
3. Navigate to Test panel
4. Select test categories
5. Click "Run Selected Tests"

## Calibration

### Magnetometer Calibration

```python
from testing.calibration import MagnetometerCalibration

mag_cal = MagnetometerCalibration(command_interface)
result = mag_cal.start_automatic_calibration()

if result.quality == CalibrationQuality.GOOD:
    print("✅ Calibration successful!")
```

### Angular Correction

```python
from testing.calibration import AngularCorrection

angular_cal = AngularCorrection(command_interface)

# Collect points at cardinal directions
for az in [0, 90, 180, 270]:
    angular_cal.add_calibration_point_manual(az, 45)

# Generate correction table
result = angular_cal.generate_correction_table()

# Export to settings file
code = angular_cal.export_to_settings()
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Troubleshooting

### Common Issues

**Q: Import error on PyQt6**
```bash
pip install --upgrade PyQt6
```

**Q: Serial port permission denied (Linux)**
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

**Q: Parsing fails**
- Verify rotator_*.h files exist
- Check for syntax errors in .h files
- Try with fresh K3NG download

See [USER_GUIDE.md](docs/USER_GUIDE.md#troubleshooting) for more solutions.

## License

GPL-3.0 License - see [LICENSE](../LICENSE) for details.

This tool is designed for use with the K3NG rotator controller:
https://github.com/k3ng/k3ng_rotator_controller

## Credits

**K3NG Rotator Controller** by Anthony Good, K3NG
**Configuration Tool** developed with Claude Code

### Technologies Used

- PyQt6 - GUI framework
- pyserial - Serial communication
- Jinja2 - Template engine
- matplotlib - Visualization
- pycparser - C code parsing

## Support

- **Issues**: https://github.com/k3ng/k3ng_rotator_controller/issues
- **Wiki**: https://github.com/k3ng/k3ng_rotator_controller/wiki
- **Email**: k3ng.rotator@gmail.com

## Roadmap

Future enhancements:

- [ ] Cloud profile sharing
- [ ] Firmware compilation integration
- [ ] Simulation mode (test without hardware)
- [ ] Data logging and analysis
- [ ] Web interface for remote access
- [ ] Mobile companion app

## Changelog

### Version 1.0.0 (2025-12-28)

- ✅ Complete feature configuration (77 features, 60+ options)
- ✅ Pin assignment with conflict detection (113 pins)
- ✅ Settings editor (111 parameters)
- ✅ Dependency validation engine
- ✅ Serial communication and testing (29 tests)
- ✅ Magnetometer calibration wizard
- ✅ Angular correction calibration
- ✅ Data visualization with matplotlib
- ✅ Validation panel with auto-fix
- ✅ Comprehensive documentation

---

**Made with ❤️ for the ham radio community**

🤖 *Generated with [Claude Code](https://claude.com/claude-code)*
