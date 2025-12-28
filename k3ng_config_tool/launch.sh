#!/bin/bash
# K3NG Configuration Tool - Easy Launcher (Linux/macOS)

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python launcher
python3 "$SCRIPT_DIR/launcher.py"
