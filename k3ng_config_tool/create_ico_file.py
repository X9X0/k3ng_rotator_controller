#!/usr/bin/env python3
"""
Create .ico file from PNG icons for better Windows/Linux compatibility
"""

from pathlib import Path
from PIL import Image


def create_ico():
    """Create multi-resolution .ico file"""
    script_dir = Path(__file__).parent
    icons_dir = script_dir / "assets" / "icons"

    # Load PNG images
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    print("Creating .ico file from PNG images...")

    for size in sizes:
        png_path = icons_dir / f"satellite-dish-{size}.png"
        if png_path.exists():
            img = Image.open(png_path)
            images.append(img)
            print(f"  ✓ Loaded {size}x{size}")
        else:
            print(f"  ✗ Missing {size}x{size}")

    if images:
        ico_path = icons_dir / "satellite-dish.ico"
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        print(f"\n✓ Created {ico_path}")
        print(f"  Contains {len(images)} sizes: {[img.size for img in images]}")
        return 0
    else:
        print("\n✗ No images found to create .ico file")
        return 1


if __name__ == "__main__":
    import sys
    try:
        sys.exit(create_ico())
    except ImportError:
        print("Error: Pillow (PIL) not installed")
        print("Install with: pip install Pillow")
        sys.exit(1)
