# K3NG Configuration Tool - Setup Guide

## Quick Start

### Automatic Setup (Recommended)

The easiest way to set up the tool is to use the provided setup script:

```bash
cd k3ng_config_tool
./setup.sh
```

This script will:
1. Check your Python version (3.8+ required)
2. Create a Python virtual environment in `venv/`
3. Install all dependencies
4. Install the tool in development mode

### Manual Setup

If you prefer manual setup or the script doesn't work:

```bash
cd k3ng_config_tool

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# OR
venv\Scripts\activate     # On Windows

# Upgrade pip
pip install --upgrade pip

# Install the package
pip install -e .
```

## System Requirements

### Required

- **Python**: 3.8 or higher
- **python3-venv**: Python virtual environment module
- **Operating System**: Linux, macOS, or Windows

### Installing Prerequisites

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

#### Fedora/RHEL

```bash
sudo dnf install python3 python3-pip
```

#### macOS

```bash
brew install python3
```

#### Windows

Download and install Python from [python.org](https://www.python.org/downloads/)

## Dependencies

The tool will automatically install these dependencies:

### Core Dependencies

- **PyQt6** (>=6.6.0) - GUI framework
- **pyserial** (>=3.5) - Serial communication
- **Jinja2** (>=3.1.2) - Template engine for code generation
- **PyYAML** (>=6.0.1) - YAML configuration file support
- **jsonschema** (>=4.17.0) - Data validation

### Data Visualization

- **matplotlib** (>=3.8.0) - Plotting for calibration data
- **numpy** (>=1.26.0) - Numerical computations

### Development Tools (Optional)

- **pytest** (>=7.4.0) - Testing framework
- **pytest-qt** (>=4.2.0) - PyQt testing support
- **pytest-cov** (>=4.1.0) - Code coverage
- **mypy** (>=1.7.0) - Type checking

To install development dependencies:

```bash
pip install -e ".[dev]"
```

## Running the Tool

### Activate Virtual Environment

Before using the tool, always activate the virtual environment:

```bash
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

### Command Line Interface (CLI)

```bash
# Load and display configuration
python3 main.py load /path/to/k3ng_rotator_controller

# Validate configuration
python3 main.py validate /path/to/k3ng_rotator_controller

# List features
python3 main.py features /path/to/k3ng_rotator_controller

# Generate configuration files
python3 main.py generate /path/to/k3ng_rotator_controller
```

### Graphical User Interface (GUI)

```bash
# Launch GUI
python3 gui_main.py

# Launch GUI with a project pre-loaded
python3 gui_main.py /path/to/k3ng_rotator_controller
```

### Using Installed Commands

After installation, you can use the convenience commands:

```bash
# CLI
k3ng-config load /path/to/project

# GUI
k3ng-config-gui /path/to/project
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'PyQt6'"

**Solution**: Make sure you've activated the virtual environment:

```bash
source venv/bin/activate
```

### "python3-venv is not installed"

**Ubuntu/Debian**:
```bash
sudo apt install python3-venv
```

**Fedora/RHEL**:
```bash
sudo dnf install python3
```

### "externally-managed-environment" error

This means you're trying to install packages system-wide on a managed Python environment. Always use the virtual environment:

```bash
./setup.sh  # Creates and uses venv automatically
```

### PyQt6 GUI doesn't start on headless system

If you're running on a headless server (no display), you'll need to:

1. Use the CLI version instead of GUI
2. Or set up X11 forwarding for remote display
3. Or use Xvfb for virtual display

### Permission denied when running setup.sh

Make the script executable:

```bash
chmod +x setup.sh
```

## Deactivating Virtual Environment

When you're done using the tool:

```bash
deactivate
```

## Uninstalling

To remove the tool and virtual environment:

```bash
# Deactivate if active
deactivate

# Remove virtual environment
rm -rf venv/

# Remove Python cache files (optional)
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Updating

To update to the latest version:

```bash
# Activate virtual environment
source venv/bin/activate

# Pull latest code
git pull

# Reinstall in case dependencies changed
pip install -e .
```

## Development Setup

For development work:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Type checking
mypy .
```

## Getting Help

If you encounter issues:

1. Check this setup guide
2. Review the main README.md
3. Check the GitHub issues
4. Run with `--help` flag for command usage:
   ```bash
   python3 main.py --help
   python3 main.py load --help
   ```

## Platform-Specific Notes

### Linux

Most distributions work out of the box. Make sure you have `python3-venv` installed.

### macOS

Works well with Homebrew Python. May need XCode Command Line Tools:

```bash
xcode-select --install
```

### Windows

- Use PowerShell or Command Prompt
- Virtual environment activation: `venv\Scripts\activate`
- Paths use backslashes: `C:\path\to\project`

## Next Steps

After successful setup:

1. Read the main [README.md](README.md) for usage documentation
2. Try the CLI commands to familiarize yourself
3. Launch the GUI and explore the interface
4. Load an existing K3NG project to test the tool

Happy configuring! 📡
