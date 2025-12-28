#!/usr/bin/env python3
"""
K3NG Rotator Configuration & Testing Utility
Main Entry Point
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigurationManager, ConfigurationPaths


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║  K3NG Rotator Configuration & Testing Utility             ║
║  Phase 1 (Foundation) - Command Line Interface            ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def cmd_load(args):
    """Load and display configuration"""
    print(f"Loading configuration from: {args.project_dir}\n")

    paths = ConfigurationPaths.from_project_dir(args.project_dir)
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("❌ Failed to load configuration")
        return 1

    print("✅ Configuration loaded successfully\n")

    summary = manager.get_summary()

    print("=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"\n📡 Protocol: {summary.protocol or 'None'}")
    print(f"🧭 AZ Sensor: {summary.az_sensor or 'None'}")

    if summary.has_elevation:
        print(f"📐 EL Sensor: {summary.el_sensor or 'None configured'}")
        print(f"↕️  Elevation Control: Enabled")
    else:
        print(f"↕️  Elevation Control: Disabled")

    print(f"🖥️  Display: {summary.display_type or 'None'}")

    print(f"\n{'=' * 60}")
    print("STATISTICS")
    print("=" * 60)
    print(f"Features: {summary.enabled_features}/{summary.total_features} enabled")
    print(f"Options: {len(manager.features_config.active_options)}/{len(manager.features_config.options)} enabled")
    print(f"Pins: {summary.assigned_pins}/{summary.total_pins} assigned")
    print(f"Settings: {summary.total_settings} total")
    print(f"EEPROM Settings: {summary.eeprom_settings}")

    conflicts = manager.get_pin_conflicts()
    if conflicts:
        print(f"\n⚠️  Pin Conflicts: {len(conflicts)}")
        if args.verbose:
            for conflict in conflicts[:5]:  # Show first 5
                print(f"  • {conflict}")
            if len(conflicts) > 5:
                print(f"  ... and {len(conflicts) - 5} more")
    else:
        print(f"\n✅ No pin conflicts detected")

    # Show active features by category
    if args.verbose:
        print(f"\n{'=' * 60}")
        print("ENABLED FEATURES BY CATEGORY")
        print("=" * 60)
        for category in manager.features_config.categories:
            enabled = [
                f for f in category.features
                if f in manager.features_config.active_features
            ]
            if enabled:
                print(f"\n{category.name}:")
                for feature in enabled:
                    print(f"  ✓ {feature}")

    return 0


def cmd_export(args):
    """Export configuration to JSON"""
    print(f"Loading configuration from: {args.project_dir}")

    paths = ConfigurationPaths.from_project_dir(args.project_dir)
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("❌ Failed to load configuration")
        return 1

    print(f"Exporting to: {args.output}")
    manager.export_to_json(args.output)
    print("✅ Export complete")

    return 0


def cmd_features(args):
    """List features"""
    paths = ConfigurationPaths.from_project_dir(args.project_dir)
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("❌ Failed to load configuration")
        return 1

    print("=" * 60)
    print("FEATURES")
    print("=" * 60)

    for category in manager.features_config.categories:
        print(f"\n{category.name}:")
        for feature in category.features:
            status = "✓" if feature in manager.features_config.active_features else "○"
            feature_def = manager.features_config.features[feature]
            comment = f" // {feature_def.comment}" if feature_def.comment else ""
            print(f"  {status} {feature}{comment}")

    return 0


def cmd_pins(args):
    """List pins"""
    paths = ConfigurationPaths.from_project_dir(args.project_dir)
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("❌ Failed to load configuration")
        return 1

    print("=" * 60)
    print("PIN ASSIGNMENTS")
    print("=" * 60)

    for group in manager.pins_config.groups:
        print(f"\n{group.name}:")
        for pin_name in group.pins:
            pin_def = manager.pins_config.pins[pin_name]
            if not pin_def.is_disabled or args.all:
                status = "✓" if not pin_def.is_disabled else "○"
                value = pin_def.pin_string if not pin_def.is_disabled else "disabled"
                print(f"  {status} {pin_name:40} = {value}")

    return 0


def cmd_settings(args):
    """List settings"""
    paths = ConfigurationPaths.from_project_dir(args.project_dir)
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("❌ Failed to load configuration")
        return 1

    print("=" * 60)
    print("SETTINGS")
    print("=" * 60)

    for category in manager.settings_config.categories:
        print(f"\n{category.name}:")
        for setting_name in category.settings:
            setting_def = manager.settings_config.settings[setting_name]
            value_str = str(setting_def.value)
            if len(value_str) > 40:
                value_str = value_str[:37] + "..."
            unit = f" {setting_def.unit}" if setting_def.unit else ""
            eeprom = " [EEPROM]" if setting_def.is_eeprom_persistent else ""
            print(f"  {setting_name:45} = {value_str}{unit}{eeprom}")

    return 0


def cmd_validate(args):
    """Validate configuration"""
    print(f"Validating configuration from: {args.project_dir}\n")

    paths = ConfigurationPaths.from_project_dir(args.project_dir)
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("❌ Failed to load configuration")
        return 1

    # Run validation
    result = manager.validate()

    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    if result.passed:
        print("\n✅ Configuration is valid!\n")
    else:
        print(f"\n❌ Configuration has {len(result.errors)} error(s)\n")

    # Show errors
    if result.errors:
        print("ERRORS:")
        for i, error in enumerate(result.errors, 1):
            print(f"\n{i}. {error.message}")
            print(f"   Affected: {', '.join(error.affected_features)}")
            if error.suggestion:
                print(f"   💡 Suggestion: {error.suggestion}")

    # Show warnings
    if result.warnings:
        print("\n" + "=" * 60)
        print("WARNINGS:")
        for i, warning in enumerate(result.warnings, 1):
            print(f"\n{i}. {warning.message}")
            print(f"   Affected: {', '.join(warning.affected_features)}")
            if warning.suggestion:
                print(f"   💡 Suggestion: {warning.suggestion}")

    # Show info/suggestions
    if result.info:
        print("\n" + "=" * 60)
        print("SUGGESTIONS:")
        for i, info in enumerate(result.info, 1):
            print(f"\n{i}. {info.message}")
            if info.affected_features:
                print(f"   Features: {', '.join(info.affected_features)}")

    # Show auto-fix summary
    if result.auto_fixes:
        print("\n" + "=" * 60)
        print(f"AUTO-FIX AVAILABLE:")
        print(f"The following features can be automatically enabled:")
        for feature in sorted(result.auto_fixes):
            print(f"  • {feature}")

        if args.apply_fixes:
            print("\nApplying auto-fixes...")
            count = manager.apply_auto_fixes()
            print(f"✅ Enabled {count} features")

            # Re-validate
            result = manager.validate()
            if result.passed:
                print("✅ Configuration is now valid!")
            else:
                print(f"⚠️  Still has {len(result.errors)} error(s) that need manual fixing")

    print("\n" + "=" * 60)
    summary = manager.get_validation_summary()
    print(f"Summary: {summary['error_count']} errors, {summary['warning_count']} warnings, {summary['info_count']} suggestions")

    return 0 if result.passed else 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="K3NG Rotator Configuration & Testing Utility"
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Load command
    parser_load = subparsers.add_parser('load', help='Load and display configuration')
    parser_load.add_argument('project_dir', help='Path to K3NG project directory')
    parser_load.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # Export command
    parser_export = subparsers.add_parser('export', help='Export configuration to JSON')
    parser_export.add_argument('project_dir', help='Path to K3NG project directory')
    parser_export.add_argument('-o', '--output', required=True, help='Output JSON file')

    # Features command
    parser_features = subparsers.add_parser('features', help='List features')
    parser_features.add_argument('project_dir', help='Path to K3NG project directory')

    # Pins command
    parser_pins = subparsers.add_parser('pins', help='List pin assignments')
    parser_pins.add_argument('project_dir', help='Path to K3NG project directory')
    parser_pins.add_argument('-a', '--all', action='store_true', help='Show disabled pins')

    # Settings command
    parser_settings = subparsers.add_parser('settings', help='List settings')
    parser_settings.add_argument('project_dir', help='Path to K3NG project directory')

    # Validate command
    parser_validate = subparsers.add_parser('validate', help='Validate configuration')
    parser_validate.add_argument('project_dir', help='Path to K3NG project directory')
    parser_validate.add_argument('--apply-fixes', action='store_true', help='Apply auto-fixes automatically')

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Dispatch command
    if args.command == 'load':
        return cmd_load(args)
    elif args.command == 'export':
        return cmd_export(args)
    elif args.command == 'features':
        return cmd_features(args)
    elif args.command == 'pins':
        return cmd_pins(args)
    elif args.command == 'settings':
        return cmd_settings(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
