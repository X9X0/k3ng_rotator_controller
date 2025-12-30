#!/usr/bin/env python3
"""
Test icon display in window and taskbar
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


def main():
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Icon Test")
    app.setDesktopFileName("icon-test.desktop")

    icons_dir = Path(__file__).parent / "assets" / "icons"

    # Test 1: Load icon with multiple sizes
    print("Test 1: Loading multi-size icon...")
    app_icon = QIcon()
    for size in [16, 32, 48, 64, 128, 256]:
        icon_path = icons_dir / f"satellite-dish-{size}.png"
        if icon_path.exists():
            app_icon.addFile(str(icon_path))
            print(f"  Added {size}x{size}: {icon_path}")

    print(f"  Icon null? {app_icon.isNull()}")
    print(f"  Available sizes: {app_icon.availableSizes()}")

    # Set at application level
    app.setWindowIcon(app_icon)
    print(f"  Set at QApplication level")

    # Create window
    window = QMainWindow()
    window.setWindowTitle("K3NG Icon Test - Check Taskbar & Title Bar")
    window.setGeometry(100, 100, 600, 400)

    # Also set on window
    window.setWindowIcon(app_icon)
    print(f"  Set at QMainWindow level")

    # Create content
    widget = QWidget()
    layout = QVBoxLayout()

    label = QLabel(
        "Icon Test Window\n\n"
        "Check if the satellite dish icon appears in:\n"
        "• Window title bar (top left)\n"
        "• Taskbar\n"
        "• Alt+Tab switcher\n\n"
        f"Icon loaded: {'Yes' if not app_icon.isNull() else 'No'}\n"
        f"Available sizes: {len(app_icon.availableSizes())}\n\n"
        "If icons still don't show, this is a Qt/GNOME issue."
    )
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 14px; padding: 20px;")

    layout.addWidget(label)
    widget.setLayout(layout)
    window.setCentralWidget(widget)

    window.show()

    print("\n=== Icon Test Window Shown ===")
    print("Check the window title bar and taskbar for the satellite dish icon.")
    print("Press Ctrl+C to exit.\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
