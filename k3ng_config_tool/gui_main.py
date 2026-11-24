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
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow
import platform


def main():
    """Main entry point for GUI application"""
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("K3NG Configuration Tool")
    app.setOrganizationName("K3NG")
    app.setApplicationVersion("0.4.0")
    app.setDesktopFileName("k3ng-config-tool.desktop")  # For Linux desktop integration

    # Set X11 window class name (important for GNOME icon matching)
    if platform.system() == "Linux":
        app.setProperty("_q_xcb_wm_class", "k3ng-config-tool")

    # Set application icon (for taskbar and window decorations)
    # Add multiple sizes for better platform support
    icons_dir = Path(__file__).parent / "assets" / "icons"
    app_icon = QIcon()

    # Try .ico file first (better multi-platform support)
    ico_path = icons_dir / "satellite-dish.ico"
    if ico_path.exists():
        app_icon = QIcon(str(ico_path))
        print(f"Loaded icon from .ico file: {ico_path}")
    else:
        # Fallback to loading individual PNGs
        for size in [16, 32, 48, 64, 128, 256]:
            icon_path = icons_dir / f"satellite-dish-{size}.png"
            if icon_path.exists():
                app_icon.addFile(str(icon_path))

    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
        print(f"Application icon set: {len(app_icon.availableSizes())} sizes available")
    else:
        print("Warning: Could not load application icon")

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
