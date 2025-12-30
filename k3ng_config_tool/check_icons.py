#!/usr/bin/env python3
"""
Check if application icons are properly configured
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon


def main():
    """Check icon files and configuration"""
    # Create QApplication (required for QIcon)
    app = QApplication(sys.argv)

    script_dir = Path(__file__).parent
    icons_dir = script_dir / "assets" / "icons"

    print("K3NG Configuration Tool - Icon Check")
    print("=" * 50)

    # Check if icons directory exists
    if not icons_dir.exists():
        print(f"✗ Icons directory not found: {icons_dir}")
        return 1

    print(f"✓ Icons directory found: {icons_dir}\n")

    # Check for expected icon files
    expected_sizes = [16, 32, 48, 64, 128, 256]
    print("Checking PNG icon files:")

    all_found = True
    for size in expected_sizes:
        icon_path = icons_dir / f"satellite-dish-{size}.png"
        if icon_path.exists():
            file_size = icon_path.stat().st_size
            print(f"  ✓ {size}x{size}: {icon_path.name} ({file_size:,} bytes)")
        else:
            print(f"  ✗ {size}x{size}: MISSING - {icon_path.name}")
            all_found = False

    # Check SVG
    svg_path = icons_dir / "satellite-dish.svg"
    if svg_path.exists():
        print(f"\n✓ SVG source found: {svg_path.name}")
    else:
        print(f"\n✗ SVG source missing: {svg_path.name}")

    # Check if QIcon can load the icons
    print("\nTesting QIcon loading:")
    test_icon = QIcon()
    loaded_count = 0

    for size in expected_sizes:
        icon_path = icons_dir / f"satellite-dish-{size}.png"
        if icon_path.exists():
            test_icon.addFile(str(icon_path))
            loaded_count += 1

    if test_icon.isNull():
        print(f"  ✗ QIcon failed to load any icons")
        all_found = False
    else:
        available_sizes = test_icon.availableSizes()
        print(f"  ✓ QIcon loaded successfully ({loaded_count} sizes)")
        print(f"  Available sizes: {[f'{s.width()}x{s.height()}' for s in available_sizes]}")

    # Summary
    print("\n" + "=" * 50)
    if all_found and not test_icon.isNull():
        print("✓ All icons are properly configured!")
        print("\nIf icons still don't appear in taskbar/title bar:")
        print("  1. Restart the application completely")
        print("  2. On Linux: Clear desktop cache with 'gtk-update-icon-cache'")
        print("  3. On Windows: Icons may be cached - restart explorer.exe")
        print("  4. Check that you're running via ./launcher.py")
        return 0
    else:
        print("✗ Some icons are missing or not loading properly")
        print("\nTo regenerate icons, run:")
        print("  ./venv/bin/python3 create_icon_pngs.py")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
