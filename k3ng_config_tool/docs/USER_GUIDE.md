# K3NG Configuration Tool - User Guide

Complete guide for using the K3NG Configuration & Testing Utility.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Calibration](#calibration)
7. [Validation](#validation)
8. [Export](#export)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Introduction

The K3NG Configuration Tool is a comprehensive Python GUI application for configuring and testing the K3NG rotator controller. It provides:

- **Visual Configuration**: Point-and-click interface for all features and options
- **Hardware Validation**: Board-aware pin conflict detection
- **Dependency Checking**: Automatic validation of feature dependencies
- **Serial Testing**: Automated testing of deployed configurations
- **Calibration Wizards**: Step-by-step compass and angular calibration
- **Code Generation**: Export valid configuration files

### System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Hardware**: K3NG rotator controller with USB/serial connection (for testing features)

---

## Installation

### Step 1: Install Python

Download and install Python 3.10+ from [python.org](https://www.python.org/downloads/)

Verify installation:
```bash
python3 --version
```

### Step 2: Install Dependencies

Navigate to the tool directory:
```bash
cd k3ng_rotator_controller/k3ng_config_tool
```

Install required packages:
```bash
pip install -r requirements.txt
```

### Step 3: Launch the Application

#### GUI Mode (Recommended)
```bash
python3 gui_main.py
```

#### CLI Mode (Advanced)
```bash
python3 main.py --help
```

---

## Getting Started

### First Launch

1. **Start the application**: Run `python3 gui_main.py`
2. **Select project directory**: Click "File → Open Project" and navigate to your K3NG rotator controller directory
3. **The tool will automatically parse**:
   - `k3ng_rotator_controller/rotator_features.h`
   - `k3ng_rotator_controller/rotator_pins.h`
   - `k3ng_rotator_controller/rotator_settings.h`

### Main Window Layout

```
┌─────────────────────────────────────────────────┐
│ K3NG Configuration Tool         File Edit Help  │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ Features │   Configuration Panels               │
│ Pins     │                                      │
│ Settings │   (Feature selector, pin config,    │
│ Validate │    settings editor, etc.)            │
│ Test     │                                      │
│ Calibrate│                                      │
│          │                                      │
├──────────┴──────────────────────────────────────┤
│ Status Bar: Board: Mega | Port: COM3 | Ready    │
└─────────────────────────────────────────────────┘
```

### Navigation Tree

- **Features**: Enable/disable controller features
- **Pins**: Assign Arduino pins to functions
- **Settings**: Configure numeric parameters
- **Validate**: Check configuration for errors
- **Test**: Run automated hardware tests
- **Calibrate**: Compass and angular calibration wizards

---

## Configuration

### Selecting Features

1. **Click "Features" in navigation tree**
2. **Browse categories**:
   - Protocol Emulation (Yaesu, Easycom, DCU-1)
   - Position Sensors (Azimuth/Elevation)
   - Display Options
   - Tracking Features
   - Motor Control
   - And more...
3. **Check/uncheck features** to enable/disable
4. **Read tooltips** for feature descriptions

#### Example: Basic AZ-only Rotator

Enable these features:
- ✅ `FEATURE_YAESU_EMULATION`
- ✅ `FEATURE_AZ_POSITION_POTENTIOMETER`
- ✅ `FEATURE_4_BIT_LCD_DISPLAY`

### Pin Configuration

1. **Click "Pins" in navigation tree**
2. **Select pin function** from dropdown
3. **Assign Arduino pin number**
4. **Check for conflicts** (red highlighting)

#### Pin Types

- **Digital**: Any digital I/O pin
- **Analog**: A0-A15 (Mega), A0-A5 (Uno)
- **PWM**: Pins with ~ symbol (3, 5, 6, 9, 10, 11 on most boards)
- **Interrupt**: Pins 2, 3 (Uno), 2, 3, 18, 19, 20, 21 (Mega)

#### Example: Pin Assignments for Mega

```
rotator_analog_az          → A0
azimuth_speed_voltage      → A1
rotate_cw                  → 4
rotate_ccw                 → 5
brake_az                   → 6
```

### Settings Configuration

1. **Click "Settings" in navigation tree**
2. **Browse setting categories**
3. **Adjust values** using spinboxes/sliders
4. **Check units** (degrees, milliseconds, etc.)

#### Important Settings

- **AZIMUTH_STARTING_POINT**: Starting position (default: 0°)
- **AZIMUTH_ROTATION_CAPABILITY**: Full rotation (default: 360°)
- **AZIMUTH_DISPLAY_OFFSET**: Display offset (default: 0°)
- **SLOW_START_UP_TIME**: Motor ramp-up time (default: 1000 ms)
- **SLOW_DOWN_BEFORE_TARGET_AZ**: Slowdown distance (default: 10°)

---

## Testing

### Connecting to Controller

1. **Connect Arduino** via USB cable
2. **Select serial port**: Click status bar dropdown
3. **Click "Connect"**
4. **Verify connection**: Status bar shows "Connected"

### Running Tests

1. **Click "Test" in navigation tree**
2. **Select test categories**:
   - I/O Tests (digital/analog pin verification)
   - Motor Tests (CW/CCW rotation, speed control)
   - Sensor Tests (position queries, stability)
   - Calibration Tests (calibration verification)
3. **Click "Run Selected Tests"**
4. **Monitor progress** in real-time
5. **View results** in test results panel

### Test Results

- ✅ **Green (Passed)**: Test successful
- ⚠️ **Yellow (Skipped)**: Test not applicable
- ❌ **Red (Failed)**: Test failed, check details

### Generating Test Report

1. **After tests complete**, click "Generate HTML Report"
2. **Choose save location**
3. **Open report** in web browser for detailed analysis

---

## Calibration

### Magnetometer Calibration

For compass-based azimuth sensors (HMC5883L, QMC5883, LSM303):

#### Automatic Mode

1. **Click "Calibrate" → "Magnetometer"**
2. **Select "Automatic Mode"**
3. **Click "Start Calibration"**
4. **Controller rotates 360°** to gather data
5. **Wait for completion** (~60 seconds)
6. **Check quality**: GOOD / SUSPECT / POOR
7. **Save to EEPROM**

#### Manual Mode

1. **Click "Calibrate" → "Magnetometer"**
2. **Select "Manual Mode"**
3. **Click "Start Calibration"**
4. **Manually rotate antenna 360°** (slowly, full circle)
5. **Click "End Calibration"**
6. **Check quality assessment**
7. **Save to EEPROM**

#### Quality Guidelines

- **GOOD**: ✅ Calibration successful, ready to use
- **SUSPECT**: ⚠️ May work, consider recalibrating
- **POOR**: ❌ Recalibration required

### Angular Correction Calibration

For correcting azimuth/elevation errors across rotation range:

#### Procedure

1. **Click "Calibrate" → "Angular Correction"**
2. **Choose reference method**:
   - Manual (you specify true position)
   - Sun (requires sun tracking feature)
   - Moon (requires moon tracking feature)
3. **Collect calibration points**:
   - Point antenna at known position
   - Enter true azimuth/elevation
   - Click "Add Point"
   - Repeat for 3-8 positions (more = better accuracy)
4. **Generate correction table**
5. **Review statistics** (avg/max errors)
6. **View visualization** (error plots)
7. **Export to settings file**

#### Recommended Calibration Points

For best results, use points spread across full rotation:
- 0° (North)
- 90° (East)
- 180° (South)
- 270° (West)
- Plus intermediate points (45°, 135°, 225°, 315°)

#### Calibration Visualization

The tool generates three types of plots:
- **Error vs. Position**: Shows error curve across rotation
- **Error Distribution**: Histogram of measurement errors
- **Polar Plot**: Visual representation on compass rose

---

## Validation

### Running Validation

1. **Click "Validate" in navigation tree**
2. **Click "Validate Configuration"**
3. **Review results** in tabbed interface:
   - **Errors**: Must be fixed before deployment
   - **Warnings**: Should be reviewed
   - **Info**: Helpful suggestions

### Understanding Validation Issues

#### Mutual Exclusivity Errors

```
❌ Only one protocol emulation allowed
   Affects: FEATURE_YAESU_EMULATION, FEATURE_EASYCOM_EMULATION
   Suggestion: Disable one of the conflicting features
```

**Fix**: Disable all but one protocol emulation feature.

#### Missing Dependencies

```
❌ FEATURE_MOON_TRACKING requires FEATURE_ELEVATION_CONTROL
   Affects: FEATURE_MOON_TRACKING
   Suggestion: Enable FEATURE_ELEVATION_CONTROL
```

**Fix**: Enable the required dependency or disable the dependent feature.

#### Pin Conflicts

```
❌ Pin 6 assigned to multiple functions
   Affects: brake_az, rotate_cw_pwm
   Suggestion: Assign different pins
```

**Fix**: Change one of the pin assignments to an unused pin.

### Auto-Fix

1. **Issues marked with 🔧** can be automatically fixed
2. **Click "Auto-Fix Issues"** button
3. **Review proposed changes**
4. **Confirm to apply**

### Exporting Validation Report

1. **Click "Export Report"**
2. **Choose format**: Text (.txt) or Markdown (.md)
3. **Save for documentation**

---

## Export

### Exporting Configuration

1. **Validate configuration** first (no errors)
2. **Click "File → Export Configuration"**
3. **Choose export mode**:

#### Modify Existing Files

- Overwrites existing rotator_*.h files
- Creates backup with timestamp
- Preserves comments and structure

#### Create New Profile

- Generates new files: `rotator_features_custom.h`, etc.
- Leaves original files untouched
- Update `rotator_hardware.h` to use new profile

4. **Click "Export"**
5. **Verify success** message
6. **Compile in Arduino IDE**

### Backup Files

The tool automatically creates backups:
```
rotator_features.h → rotator_features.h.backup.20250128_143052
rotator_pins.h     → rotator_pins.h.backup.20250128_143052
rotator_settings.h → rotator_settings.h.backup.20250128_143052
```

---

## Troubleshooting

### Connection Issues

**Problem**: "Serial port not found"

**Solutions**:
- Check USB cable connection
- Install Arduino drivers
- Check Device Manager (Windows) or `ls /dev/tty*` (Linux/Mac)
- Close Arduino IDE (only one program can use serial port)

---

**Problem**: "Permission denied" (Linux/Mac)

**Solution**:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

---

### Parsing Errors

**Problem**: "Failed to parse rotator_features.h"

**Solutions**:
- Ensure file exists in correct location
- Check for syntax errors in .h file
- Verify file is not corrupted
- Try with a fresh K3NG download

---

### Validation Errors

**Problem**: "Configuration has errors, cannot export"

**Solution**:
1. Open Validation panel
2. Review all errors
3. Fix each error (use auto-fix if available)
4. Re-validate until clean

---

### Test Failures

**Problem**: Tests fail or skip

**Possible causes**:
- Serial port not connected
- Wrong baud rate (default: 9600)
- Controller not responding
- Feature not enabled in firmware

**Solution**:
- Verify serial connection
- Check Arduino serial monitor works
- Ensure firmware is uploaded
- Enable required features

---

## FAQ

### Q: Can I use this with other Arduino projects?

**A**: This tool is specifically designed for K3NG rotator controller. The parsing and validation rules are K3NG-specific.

---

### Q: Does this tool upload firmware to Arduino?

**A**: No, the tool generates configuration files. You must compile and upload using Arduino IDE.

---

### Q: Can I use this offline?

**A**: Yes, all functionality except web-based help works offline.

---

### Q: How do I add a custom board?

**A**: Edit `data/board_definitions/` and add a new JSON file with your board's pin capabilities.

---

### Q: What if I have multiple rotators?

**A**: Create separate configuration profiles for each rotator using "Create New Profile" export mode.

---

### Q: Can I import existing configurations?

**A**: Yes, use "File → Open Project" and point to any K3NG rotator directory. The tool will parse existing .h files.

---

### Q: How accurate is the calibration?

**A**: Angular correction calibration accuracy depends on reference accuracy. Use precise reference positions (GPS coordinates, sun/moon ephemeris) for best results.

---

### Q: Does this work with Raspberry Pi?

**A**: Yes, install Python 3.10+ and dependencies. GUI requires X server.

---

## Getting Help

### Resources

- **GitHub Issues**: https://github.com/k3ng/k3ng_rotator_controller/issues
- **K3NG Wiki**: https://github.com/k3ng/k3ng_rotator_controller/wiki
- **Configuration Tool Docs**: `k3ng_config_tool/docs/`

### Reporting Bugs

1. Check existing issues on GitHub
2. Provide:
   - Tool version
   - Operating system
   - Error message
   - Steps to reproduce
3. Include validation report if relevant

### Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines.

---

## Appendix A: Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open Project |
| Ctrl+S | Save Configuration |
| Ctrl+E | Export Configuration |
| Ctrl+V | Run Validation |
| Ctrl+T | Open Test Runner |
| Ctrl+Q | Quit |
| F1 | Help |
| F5 | Refresh |

---

## Appendix B: Default Pin Assignments

### Arduino Mega 2560

```
Function                    Pin
------------------------------------
rotator_analog_az          A0
rotator_analog_el          A1
azimuth_speed_voltage      A2
elevation_speed_voltage    A3
button_cw                  2
button_ccw                 3
button_up                  4
button_down                5
rotate_cw                  6
rotate_ccw                 7
rotate_up                  8
rotate_down                9
brake_az                   10
brake_el                   11
lcd_rs                     12
lcd_enable                 13
lcd_d4-d7                  22-25
```

### Arduino Uno

```
Function                    Pin
------------------------------------
rotator_analog_az          A0
rotator_analog_el          A1
button_cw                  2
button_ccw                 3
rotate_cw                  6
rotate_ccw                 7
brake_az                   8
lcd_rs                     12
lcd_enable                 13
lcd_d4-d7                  8-11
```

---

## Appendix C: Troubleshooting Checklist

Before requesting help, verify:

- [ ] Latest version of tool installed
- [ ] Latest K3NG firmware downloaded
- [ ] Python 3.10+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Project directory contains valid .h files
- [ ] No syntax errors in .h files
- [ ] Configuration validates without errors
- [ ] Backup files created before export
- [ ] Arduino IDE can compile exported files
- [ ] Serial port works in Arduino Serial Monitor

---

**End of User Guide**

*For additional documentation, see `DEVELOPER_GUIDE.md` and inline code documentation.*
