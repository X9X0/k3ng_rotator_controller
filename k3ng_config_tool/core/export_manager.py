"""
K3NG Configuration Tool - Export Manager
Coordinates export of configuration to .h files
"""

from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum
import shutil
from datetime import datetime

from parsers.feature_parser import FeatureConfig
from parsers.pin_parser import PinConfig
from parsers.settings_parser import SettingsConfig
from generators.template_engine import TemplateEngine


class ExportMode(Enum):
    """Export mode options"""
    MODIFY_EXISTING = "modify_existing"  # Overwrite existing files
    NEW_PROFILE = "new_profile"          # Create new profile with suffix


class ExportResult:
    """Result of export operation"""

    def __init__(self):
        self.success = False
        self.files_written: List[Path] = []
        self.backups_created: List[Path] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_file(self, path: Path):
        """Record a file that was written"""
        self.files_written.append(path)

    def add_backup(self, path: Path):
        """Record a backup that was created"""
        self.backups_created.append(path)

    def add_error(self, message: str):
        """Record an error"""
        self.errors.append(message)
        self.success = False

    def add_warning(self, message: str):
        """Record a warning"""
        self.warnings.append(message)

    def __str__(self):
        lines = []
        if self.success:
            lines.append("✓ Export successful")
            lines.append(f"  Files written: {len(self.files_written)}")
            for f in self.files_written:
                lines.append(f"    - {f}")
            if self.backups_created:
                lines.append(f"  Backups created: {len(self.backups_created)}")
                for b in self.backups_created:
                    lines.append(f"    - {b}")
        else:
            lines.append("✗ Export failed")

        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings:
                lines.append(f"    - {w}")

        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors:
                lines.append(f"    - {e}")

        return "\n".join(lines)


class ExportManager:
    """
    Manages export of configuration to .h files

    Supports two modes:
    1. Modify existing files in place (with backup)
    2. Create new profile with custom suffix
    """

    def __init__(self, template_engine: Optional[TemplateEngine] = None):
        """
        Initialize export manager

        Args:
            template_engine: Template engine instance (creates new if None)
        """
        self.template_engine = template_engine or TemplateEngine()

    def export(self,
               output_dir: Path,
               features_config: FeatureConfig,
               pins_config: PinConfig,
               settings_config: SettingsConfig,
               mode: ExportMode = ExportMode.MODIFY_EXISTING,
               profile_suffix: str = "",
               create_backup: bool = True) -> ExportResult:
        """
        Export configuration to .h files

        Args:
            output_dir: Directory to write files to
            features_config: Feature configuration
            pins_config: Pin configuration
            settings_config: Settings configuration
            mode: Export mode (modify existing or new profile)
            profile_suffix: Suffix for new profile (e.g., "_custom")
            create_backup: Whether to create backups of existing files

        Returns:
            ExportResult with status and details
        """
        result = ExportResult()

        # Validate output directory
        if not output_dir.exists():
            result.add_error(f"Output directory does not exist: {output_dir}")
            return result

        # Validate profile suffix for new profile mode
        if mode == ExportMode.NEW_PROFILE and not profile_suffix:
            result.add_warning("No profile suffix provided for new profile mode, using '_custom'")
            profile_suffix = "_custom"

        # Generate file contents
        try:
            file_contents = self.template_engine.generate_all(
                features_config,
                pins_config,
                settings_config
            )
        except Exception as e:
            result.add_error(f"Failed to generate file contents: {str(e)}")
            return result

        # Determine output filenames
        filenames = {}
        for base_filename in file_contents.keys():
            if mode == ExportMode.NEW_PROFILE:
                # Add suffix before .h extension
                name_without_ext = base_filename.replace('.h', '')
                output_filename = f"{name_without_ext}{profile_suffix}.h"
            else:
                output_filename = base_filename

            filenames[base_filename] = output_filename

        # Create backups if needed
        if create_backup and mode == ExportMode.MODIFY_EXISTING:
            backup_result = self._create_backups(output_dir, list(filenames.values()))
            result.backups_created.extend(backup_result)

        # Write files
        for base_filename, content in file_contents.items():
            output_filename = filenames[base_filename]
            output_path = output_dir / output_filename

            try:
                # Add generation metadata comment
                header = self._generate_header(mode, profile_suffix)
                full_content = header + "\n" + content

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)

                result.add_file(output_path)
            except Exception as e:
                result.add_error(f"Failed to write {output_filename}: {str(e)}")
                return result

        result.success = True
        return result

    def _create_backups(self, directory: Path, filenames: List[str]) -> List[Path]:
        """
        Create backup copies of existing files

        Args:
            directory: Directory containing files
            filenames: List of filenames to backup

        Returns:
            List of backup file paths created
        """
        backups = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for filename in filenames:
            source_path = directory / filename
            if source_path.exists():
                backup_filename = f"{filename}.backup_{timestamp}"
                backup_path = directory / backup_filename

                try:
                    shutil.copy2(source_path, backup_path)
                    backups.append(backup_path)
                except Exception as e:
                    # Continue even if backup fails
                    print(f"Warning: Failed to create backup of {filename}: {str(e)}")

        return backups

    def _generate_header(self, mode: ExportMode, profile_suffix: str = "") -> str:
        """
        Generate header comment for exported files

        Args:
            mode: Export mode
            profile_suffix: Profile suffix if applicable

        Returns:
            Header comment string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = f"""/*
 * Generated by K3NG Configuration Tool
 * Timestamp: {timestamp}
 * Mode: {mode.value}"""

        if mode == ExportMode.NEW_PROFILE:
            header += f"\n * Profile: {profile_suffix}"

        header += "\n */"

        return header

    def export_to_project(self,
                         project_dir: Path,
                         features_config: FeatureConfig,
                         pins_config: PinConfig,
                         settings_config: SettingsConfig,
                         profile_name: Optional[str] = None,
                         create_backup: bool = True) -> ExportResult:
        """
        Export configuration to K3NG rotator controller project directory

        Args:
            project_dir: K3NG rotator controller project directory
            features_config: Feature configuration
            pins_config: Pin configuration
            settings_config: Settings configuration
            profile_name: Optional profile name (e.g., "my_config" for rotator_features_my_config.h)
            create_backup: Whether to create backups

        Returns:
            ExportResult with status and details
        """
        # Determine mode and suffix
        if profile_name:
            mode = ExportMode.NEW_PROFILE
            suffix = f"_{profile_name}"
        else:
            mode = ExportMode.MODIFY_EXISTING
            suffix = ""

        return self.export(
            project_dir,
            features_config,
            pins_config,
            settings_config,
            mode=mode,
            profile_suffix=suffix,
            create_backup=create_backup
        )

    def validate_export(self,
                       output_dir: Path,
                       filenames: List[str]) -> Dict[str, bool]:
        """
        Validate that exported files exist and are readable

        Args:
            output_dir: Directory containing exported files
            filenames: List of filenames to validate

        Returns:
            Dict mapping filename -> validation status
        """
        results = {}

        for filename in filenames:
            file_path = output_dir / filename

            if not file_path.exists():
                results[filename] = False
                continue

            try:
                # Try to read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Basic validation: file should have some content
                results[filename] = len(content) > 0
            except Exception:
                results[filename] = False

        return results
