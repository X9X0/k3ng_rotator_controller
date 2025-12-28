#!/bin/bash
# K3NG Configuration Tool - Setup Script
# This script sets up a Python virtual environment and installs all dependencies

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  K3NG Configuration Tool - Setup                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if venv module is available
if ! python3 -c "import venv" &> /dev/null; then
    echo "❌ Error: python3-venv is not installed"
    echo "   Install it with: sudo apt install python3-venv"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install the package in development mode
echo "Installing k3ng-config-tool and dependencies..."
pip install -e . --quiet

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ Setup Complete!                                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "To use the tool:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the CLI tool:"
echo "     python3 main.py <command>"
echo ""
echo "  3. Run the GUI tool:"
echo "     python3 gui_main.py [project_directory]"
echo ""
echo "  4. Or use the installed commands (after activation):"
echo "     k3ng-config <command>"
echo "     k3ng-config-gui [project_directory]"
echo ""
echo "Examples:"
echo "  python3 main.py load /path/to/k3ng_rotator_controller"
echo "  python3 main.py validate /path/to/k3ng_rotator_controller"
echo "  python3 gui_main.py /path/to/k3ng_rotator_controller"
echo ""
