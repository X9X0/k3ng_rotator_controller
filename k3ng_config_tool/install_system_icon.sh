#!/bin/bash
# Install application icon to system directories for GNOME/KDE integration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICONS_SOURCE="$SCRIPT_DIR/assets/icons"
ICONS_DEST="$HOME/.local/share/icons/hicolor"

echo "Installing K3NG Configuration Tool icons..."

# Create icon directories if they don't exist
for size in 16 32 48 64 128 256; do
    DIR="$ICONS_DEST/${size}x${size}/apps"
    mkdir -p "$DIR"

    if [ -f "$ICONS_SOURCE/satellite-dish-${size}.png" ]; then
        cp "$ICONS_SOURCE/satellite-dish-${size}.png" "$DIR/k3ng-config-tool.png"
        echo "  ✓ Installed ${size}x${size} icon"
    else
        echo "  ✗ Missing ${size}x${size} icon"
    fi
done

# Also install SVG if available
SVG_DIR="$ICONS_DEST/scalable/apps"
mkdir -p "$SVG_DIR"
if [ -f "$ICONS_SOURCE/satellite-dish.svg" ]; then
    cp "$ICONS_SOURCE/satellite-dish.svg" "$SVG_DIR/k3ng-config-tool.svg"
    echo "  ✓ Installed SVG icon"
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    echo "Updating icon cache..."
    gtk-update-icon-cache -f -t "$ICONS_DEST" 2>/dev/null || true
    echo "  ✓ Icon cache updated"
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    DESKTOP_DIR="$HOME/.local/share/applications"
    if [ -d "$DESKTOP_DIR" ]; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
        echo "  ✓ Desktop database updated"
    fi
fi

echo ""
echo "✓ Icon installation complete!"
echo ""
echo "The icon should now appear in:"
echo "  • Window title bar"
echo "  • Taskbar"
echo "  • Alt+Tab switcher"
echo "  • Application menu (if .desktop file is installed)"
echo ""
echo "If icons still don't appear, try:"
echo "  1. Restart the application"
echo "  2. Log out and log back in"
echo "  3. Run: killall gnome-shell (on GNOME)"
