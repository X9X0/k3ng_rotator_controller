#!/usr/bin/env python3
"""
K3NG Rotator Configuration & Testing Utility
GUI Entry Point
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main entry point for GUI application"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("K3NG Configuration Tool")
    app.setOrganizationName("K3NG")
    app.setApplicationVersion("0.4.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # If a project directory was passed as argument, load it
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
        if project_dir.exists() and project_dir.is_dir():
            window.load_project(project_dir)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
