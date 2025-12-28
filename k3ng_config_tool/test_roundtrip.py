#!/usr/bin/env python3
"""
Test Round-trip Export/Parse

Tests that exporting configuration and re-parsing produces the same result
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigurationManager, ConfigurationPaths
from core.export_manager import ExportManager, ExportMode
from parsers.feature_parser import FeatureParser
from parsers.pin_parser import PinParser
from parsers.settings_parser import SettingsParser


def main():
    print("="*70)
    print("K3NG Configuration Tool - Round-trip Test")
    print("="*70)
    print()

    # Step 1: Load original configuration
    print("Step 1: Loading original configuration...")
    print("-"*70)

    project_dir = Path("..").resolve()
    paths = ConfigurationPaths.from_project_dir(str(project_dir))

    print(f"Project directory: {project_dir}")
    print(f"  Features file: {paths.features_file}")
    print(f"  Pins file: {paths.pins_file}")
    print(f"  Settings file: {paths.settings_file}")
    print()

    config_manager = ConfigurationManager(paths)

    if not config_manager.load():
        print("✗ Failed to load configuration")
        return 1

    print("✓ Original configuration loaded successfully")
    print(f"  Features: {len(config_manager.features_config.features)} items")
    print(f"  Pins: {len(config_manager.pins_config.pins)} items")
    print(f"  Settings: {len(config_manager.settings_config.settings)} items")
    print()

    # Step 2: Export to temporary directory
    print("Step 2: Exporting configuration to temporary directory...")
    print("-"*70)

    temp_dir = Path(tempfile.mkdtemp(prefix="k3ng_roundtrip_"))
    print(f"Temporary directory: {temp_dir}")
    print()

    export_manager = ExportManager()
    result = export_manager.export(
        temp_dir,
        config_manager.features_config,
        config_manager.pins_config,
        config_manager.settings_config,
        mode=ExportMode.MODIFY_EXISTING,
        create_backup=False
    )

    if not result.success:
        print("✗ Export failed")
        print(str(result))
        shutil.rmtree(temp_dir)
        return 1

    print("✓ Export successful")
    for file_path in result.files_written:
        print(f"  Generated: {file_path.name}")
    print()

    # Step 3: Re-parse exported files
    print("Step 3: Re-parsing exported configuration...")
    print("-"*70)

    exported_paths = ConfigurationPaths(
        project_dir=temp_dir,
        features_file=temp_dir / "rotator_features.h",
        pins_file=temp_dir / "rotator_pins.h",
        settings_file=temp_dir / "rotator_settings.h"
    )

    try:
        features_parser = FeatureParser(str(exported_paths.features_file))
        pins_parser = PinParser(str(exported_paths.pins_file))
        settings_parser = SettingsParser(str(exported_paths.settings_file))

        features_config_2 = features_parser.parse()
        pins_config_2 = pins_parser.parse()
        settings_config_2 = settings_parser.parse()

        print("✓ Re-parsed exported files successfully")
        print(f"  Features: {len(features_config_2.features)} items")
        print(f"  Pins: {len(pins_config_2.pins)} items")
        print(f"  Settings: {len(settings_config_2.settings)} items")
        print()
    except Exception as e:
        print(f"✗ Failed to re-parse exported files: {str(e)}")
        shutil.rmtree(temp_dir)
        return 1

    # Step 4: Compare results
    print("Step 4: Comparing original vs. exported/re-parsed...")
    print("-"*70)

    errors = []
    warnings = []

    # Compare features count
    if len(config_manager.features_config.features) != len(features_config_2.features):
        errors.append(
            f"Feature count mismatch: "
            f"{len(config_manager.features_config.features)} vs {len(features_config_2.features)}"
        )

    # Compare active features
    original_active = set(config_manager.features_config.active_features)
    exported_active = set(features_config_2.active_features)

    if original_active != exported_active:
        missing = original_active - exported_active
        extra = exported_active - original_active

        if missing:
            errors.append(f"Missing active features in export: {missing}")
        if extra:
            errors.append(f"Extra active features in export: {extra}")

    # Compare pins count
    if len(config_manager.pins_config.pins) != len(pins_config_2.pins):
        warnings.append(
            f"Pin count mismatch: "
            f"{len(config_manager.pins_config.pins)} vs {len(pins_config_2.pins)}"
        )

    # Compare settings count
    if len(config_manager.settings_config.settings) != len(settings_config_2.settings):
        warnings.append(
            f"Settings count mismatch: "
            f"{len(config_manager.settings_config.settings)} vs {len(settings_config_2.settings)}"
        )

    # Display results
    if errors:
        print("✗ Round-trip test FAILED")
        print()
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    elif warnings:
        print("⚠ Round-trip test PASSED with warnings")
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ Round-trip test PASSED")
        print()
        print("Configuration exported and re-parsed successfully with no discrepancies!")

    print()

    # Cleanup (commented out for inspection)
    print(f"Temporary files retained at: {temp_dir}")
    print("(For debugging - please remove manually when done)")
    # shutil.rmtree(temp_dir)
    # print(f"✓ Removed: {temp_dir}")
    print()

    print("="*70)
    print("Round-trip test complete")
    print("="*70)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
