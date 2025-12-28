"""
Template Engine for K3NG Configuration Files

Uses Jinja2 to generate .h files from configuration
"""

from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.feature_parser import FeatureConfig
from parsers.pin_parser import PinConfig
from parsers.settings_parser import SettingsConfig


class TemplateEngine:
    """
    Template engine for generating K3NG configuration files

    Uses Jinja2 templates to generate .h files from parsed configuration
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize template engine

        Args:
            templates_dir: Path to templates directory (default: generators/templates/)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = Path(templates_dir)

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

    def render_features(self, features_config: FeatureConfig) -> str:
        """
        Render rotator_features.h from configuration

        Args:
            features_config: Parsed feature configuration

        Returns:
            Generated file content as string
        """
        template = self.env.get_template('rotator_features.h.j2')

        # Organize features by category for template
        features_by_category = {}
        for category in features_config.categories:
            features_by_category[category.name] = category.features

        # Organize languages
        languages = {
            name: define
            for name, define in features_config.features.items()
            if name.startswith('LANGUAGE_')
        }

        # Organize options
        all_options = sorted(features_config.options.keys())

        context = {
            'features': features_config.features,
            'features_by_category': features_by_category,
            'languages': languages,
            'options': features_config.options,
            'all_options': all_options,
            'active_features': features_config.active_features
        }

        return template.render(**context)

    def render_pins(self, pins_config: PinConfig, active_features: set) -> str:
        """
        Render rotator_pins.h from configuration

        Args:
            pins_config: Parsed pin configuration
            active_features: Set of active feature names (for conditional blocks)

        Returns:
            Generated file content as string
        """
        template = self.env.get_template('rotator_pins.h.j2')

        # Organize pins by group for template
        pins_by_group = {}
        for group in pins_config.groups:
            pins_by_group[group.name] = group.pins

        context = {
            'pins': pins_config.pins,
            'pins_by_group': pins_by_group,
            'active_features': active_features
        }

        return template.render(**context)

    def render_settings(self, settings_config: SettingsConfig) -> str:
        """
        Render rotator_settings.h from configuration

        Args:
            settings_config: Parsed settings configuration

        Returns:
            Generated file content as string
        """
        template = self.env.get_template('rotator_settings.h.j2')

        # Organize settings by category for template
        settings_by_category = {}
        for category in settings_config.categories:
            settings_by_category[category.name] = category.settings

        context = {
            'settings': settings_config.settings,
            'settings_by_category': settings_by_category
        }

        return template.render(**context)

    def generate_all(self, features_config: FeatureConfig,
                    pins_config: PinConfig,
                    settings_config: SettingsConfig) -> Dict[str, str]:
        """
        Generate all configuration files

        Args:
            features_config: Parsed feature configuration
            pins_config: Parsed pin configuration
            settings_config: Parsed settings configuration

        Returns:
            Dict mapping filename -> content
        """
        return {
            'rotator_features.h': self.render_features(features_config),
            'rotator_pins.h': self.render_pins(pins_config, features_config.active_features),
            'rotator_settings.h': self.render_settings(settings_config)
        }

    def write_files(self, output_dir: str,
                   features_config: FeatureConfig,
                   pins_config: PinConfig,
                   settings_config: SettingsConfig,
                   suffix: str = ''):
        """
        Generate and write all configuration files

        Args:
            output_dir: Directory to write files to
            features_config: Parsed feature configuration
            pins_config: Parsed pin configuration
            settings_config: Parsed settings configuration
            suffix: Optional suffix for filenames (e.g., '_custom')
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files = self.generate_all(features_config, pins_config, settings_config)

        for filename, content in files.items():
            # Add suffix if provided
            if suffix:
                base_name = filename.replace('.h', '')
                filename = f"{base_name}{suffix}.h"

            file_path = output_path / filename
            with open(file_path, 'w') as f:
                f.write(content)

            print(f"✓ Generated: {file_path}")


if __name__ == "__main__":
    # Test the template engine
    from core.config_manager import ConfigurationManager, ConfigurationPaths

    print("=== Template Engine Test ===\n")

    # Load configuration
    paths = ConfigurationPaths.from_project_dir(".")
    manager = ConfigurationManager(paths)

    if not manager.load():
        print("✗ Failed to load configuration")
        sys.exit(1)

    print("✓ Configuration loaded\n")

    # Initialize template engine
    engine = TemplateEngine()

    print("Generating configuration files...\n")

    # Generate files to a test directory
    test_output_dir = Path("/tmp/k3ng_generated")
    engine.write_files(
        str(test_output_dir),
        manager.features_config,
        manager.pins_config,
        manager.settings_config,
        suffix='_test'
    )

    print(f"\n✓ Files generated to: {test_output_dir}")
    print("\nYou can compare these with the original files to verify generation.")
