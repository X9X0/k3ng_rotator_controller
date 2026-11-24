#!/usr/bin/env python3
"""
Create PNG icons from SVG for K3NG Configuration Tool
"""

from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import QSize
from pathlib import Path


def create_png_from_svg(svg_path: str, png_path: str, size: int):
    """Convert SVG to PNG at specified size"""

    # Create SVG renderer
    renderer = QSvgRenderer(svg_path)

    # Create image
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(0)  # Transparent background

    # Render SVG to image
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    # Save as PNG
    image.save(png_path)
    print(f"✓ Created {png_path} ({size}x{size})")


def main():
    """Create all icon sizes"""
    script_dir = Path(__file__).parent
    svg_path = script_dir / "assets" / "icons" / "satellite-dish.svg"
    icons_dir = script_dir / "assets" / "icons"

    if not svg_path.exists():
        print(f"Error: SVG file not found at {svg_path}")
        return 1

    # Create PNG versions in various sizes
    sizes = {
        16: "satellite-dish-16.png",
        32: "satellite-dish-32.png",
        48: "satellite-dish-48.png",
        64: "satellite-dish-64.png",
        128: "satellite-dish-128.png",
        256: "satellite-dish-256.png",
    }

    print("Creating PNG icons from SVG...")
    for size, filename in sizes.items():
        png_path = str(icons_dir / filename)
        create_png_from_svg(str(svg_path), png_path, size)

    print(f"\n✓ All icon files created in {icons_dir}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
