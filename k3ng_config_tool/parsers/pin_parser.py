"""
Pin Parser for K3NG Configuration Files

Extracts pin definitions from rotator_pins.h
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import re

try:
    from .preprocessor_parser import PreprocessorParser, DefineNode
except ImportError:
    from preprocessor_parser import PreprocessorParser, DefineNode


@dataclass
class PinDefinition:
    """Represents a pin assignment"""
    name: str
    pin_number: Optional[int] = None  # None for analog pins initially
    pin_string: str = ""  # Original string value (e.g., "A0", "13", "0")
    is_analog: bool = False
    is_disabled: bool = False  # Pin set to 0 (disabled)
    is_remote: bool = False  # Pin > 99 (remote unit pin)
    feature_dependency: Optional[str] = None  # Required FEATURE_* for this pin
    comment: Optional[str] = None
    line_number: int = 0

    def __repr__(self) -> str:
        pin_str = self.pin_string if self.pin_string else "UNSET"
        status = ""
        if self.is_disabled:
            status = " [DISABLED]"
        elif self.is_remote:
            status = f" [REMOTE:{self.pin_number - 100}]"
        elif self.is_analog:
            status = " [ANALOG]"
        return f"Pin({self.name} = {pin_str}{status})"


@dataclass
class PinGroup:
    """Groups related pins together"""
    name: str
    pins: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class PinConfig:
    """Complete pin configuration"""
    pins: Dict[str, PinDefinition]
    groups: List[PinGroup]
    digital_pins: Set[int]  # Used digital pin numbers
    analog_pins: Set[str]  # Used analog pins (A0, A1, etc.)
    conflicts: List[str]  # Pin conflict warnings


class PinParser:
    """
    Parses pin definitions from rotator_pins.h

    Handles:
    - Digital pins (0-99)
    - Analog pins (A0-A15)
    - Disabled pins (0)
    - Remote pins (>99)
    - Conditional pin definitions (#ifdef)
    """

    # Pin groups for organization
    PIN_GROUPS = {
        "Azimuth Motor Control": [
            "rotate_cw", "rotate_ccw",
            "rotate_cw_pwm", "rotate_ccw_pwm",
            "rotate_cw_freq", "rotate_ccw_freq",
            "brake_az", "azimuth_speed_voltage"
        ],
        "Elevation Motor Control": [
            "rotate_up", "rotate_down",
            "rotate_up_pwm", "rotate_down_pwm",
            "rotate_up_freq", "rotate_down_freq",
            "brake_el", "elevation_speed_voltage"
        ],
        "Position Sensors (Azimuth)": [
            "rotator_analog_az",
            "az_rotary_position_pin1", "az_rotary_position_pin2",
            "az_position_pulse_pin",
            "az_incremental_encoder_pin_a", "az_incremental_encoder_pin_b",
            "az_incremental_encoder_pin_z"
        ],
        "Position Sensors (Elevation)": [
            "rotator_analog_el",
            "el_rotary_position_pin1", "el_rotary_position_pin2",
            "el_position_pulse_pin",
            "el_incremental_encoder_pin_a", "el_incremental_encoder_pin_b",
            "el_incremental_encoder_pin_z"
        ],
        "Manual Control Buttons": [
            "button_cw", "button_ccw",
            "button_up", "button_down",
            "button_stop", "button_park",
            "moon_tracking_button", "sun_tracking_button",
            "satellite_tracking_button"
        ],
        "LCD Display (4-bit)": [
            "lcd_4_bit_rs_pin", "lcd_4_bit_enable_pin",
            "lcd_4_bit_d4_pin", "lcd_4_bit_d5_pin",
            "lcd_4_bit_d6_pin", "lcd_4_bit_d7_pin"
        ],
        "Status & Indicators": [
            "serial_led", "overlap_led", "status_led",
            "rotation_indication_pin", "audible_alert_pin",
            "brake_active_state", "brake_inactive_state"
        ],
        "Limit Switches": [
            "az_limit_sense_pin", "el_limit_sense_pin"
        ],
        "Speed & Preset Controls": [
            "az_speed_pot", "az_preset_pot",
            "el_speed_pot", "el_preset_pot",
            "preset_encoder_pin1", "preset_encoder_pin2"
        ],
        "Stepper Motor": [
            "az_stepper_motor_pulse", "az_stepper_motor_direction",
            "el_stepper_motor_pulse", "el_stepper_motor_direction"
        ],
    }

    # Analog pin pattern
    ANALOG_PIN_RE = re.compile(r'^A(\d+)$')

    def __init__(self, file_path: str):
        """Initialize with path to rotator_pins.h"""
        self.file_path = Path(file_path)
        self.parser = PreprocessorParser(str(file_path))
        self.pins: Dict[str, PinDefinition] = {}

    def parse(self) -> PinConfig:
        """
        Parse the pins file and extract all pin definitions

        Returns:
            PinConfig with all parsed pins
        """
        result = self.parser.parse()

        if not result.success:
            raise ValueError(f"Failed to parse {self.file_path}: {result.errors}")

        # Extract pin definitions
        for name, define in result.defines.items():
            if self._is_pin_define(name):
                pin_def = self._parse_pin_definition(define)
                self.pins[name] = pin_def

        # Build groups
        groups = self._build_groups()

        # Find used pins
        digital_pins = set()
        analog_pins = set()

        for pin_def in self.pins.values():
            if not pin_def.is_disabled and not pin_def.is_remote:
                if pin_def.is_analog:
                    analog_pins.add(pin_def.pin_string)
                elif pin_def.pin_number is not None:
                    digital_pins.add(pin_def.pin_number)

        # Detect conflicts
        conflicts = self._detect_conflicts()

        return PinConfig(
            pins=self.pins,
            groups=groups,
            digital_pins=digital_pins,
            analog_pins=analog_pins,
            conflicts=conflicts
        )

    def _is_pin_define(self, name: str) -> bool:
        """Check if a define is a pin definition"""
        # Common pin name patterns
        pin_keywords = [
            "pin", "button", "led", "brake", "lcd",
            "rotate", "analog", "preset", "limit",
            "stepper", "serial"
        ]
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in pin_keywords)

    def _parse_pin_definition(self, define: DefineNode) -> PinDefinition:
        """Parse a single pin definition"""
        value_str = (define.value or "0").strip()

        # Handle empty or missing values
        if not value_str:
            value_str = "0"

        # Check for analog pin (A0, A1, etc.)
        analog_match = self.ANALOG_PIN_RE.match(value_str)
        if analog_match:
            return PinDefinition(
                name=define.name,
                pin_number=None,
                pin_string=value_str,
                is_analog=True,
                is_disabled=False,
                is_remote=False,
                feature_dependency=define.conditional_scope,
                comment=define.comment,
                line_number=define.line_number
            )

        # Parse numeric pin value
        try:
            pin_num = int(value_str)
        except ValueError:
            # Non-numeric value, treat as disabled
            return PinDefinition(
                name=define.name,
                pin_number=None,
                pin_string=value_str,
                is_analog=False,
                is_disabled=True,
                is_remote=False,
                feature_dependency=define.conditional_scope,
                comment=define.comment,
                line_number=define.line_number
            )

        # Check if disabled (pin 0)
        is_disabled = (pin_num == 0)

        # Check if remote (pin > 99)
        is_remote = (pin_num > 99)

        return PinDefinition(
            name=define.name,
            pin_number=pin_num,
            pin_string=value_str,
            is_analog=False,
            is_disabled=is_disabled,
            is_remote=is_remote,
            feature_dependency=define.conditional_scope,
            comment=define.comment,
            line_number=define.line_number
        )

    def _build_groups(self) -> List[PinGroup]:
        """Build pin groups for UI organization"""
        groups = []

        for group_name, pin_names in self.PIN_GROUPS.items():
            # Only include pins that exist in the file
            existing_pins = [
                name for name in pin_names
                if name in self.pins
            ]

            if existing_pins:
                groups.append(PinGroup(
                    name=group_name,
                    pins=existing_pins,
                    description=None
                ))

        # Add ungrouped pins
        grouped = set()
        for group in groups:
            grouped.update(group.pins)

        ungrouped = [
            name for name in self.pins.keys()
            if name not in grouped
        ]

        if ungrouped:
            groups.append(PinGroup(
                name="Other Pins",
                pins=sorted(ungrouped),
                description="Additional pins not categorized"
            ))

        return groups

    def _detect_conflicts(self) -> List[str]:
        """Detect pin assignment conflicts"""
        conflicts = []

        # Build map of pin number to assigned pin names
        pin_usage: Dict[int, List[str]] = {}

        for name, pin_def in self.pins.items():
            if pin_def.is_disabled or pin_def.is_remote or pin_def.is_analog:
                continue

            if pin_def.pin_number is not None:
                if pin_def.pin_number not in pin_usage:
                    pin_usage[pin_def.pin_number] = []
                pin_usage[pin_def.pin_number].append(name)

        # Find conflicts (multiple pins assigned to same number)
        for pin_num, names in pin_usage.items():
            if len(names) > 1:
                conflicts.append(
                    f"Pin {pin_num} assigned to multiple functions: {', '.join(names)}"
                )

        return conflicts

    def get_pin(self, name: str) -> Optional[PinDefinition]:
        """Get a specific pin by name"""
        return self.pins.get(name)

    def get_pins_by_group(self, group_name: str) -> List[PinDefinition]:
        """Get all pins in a specific group"""
        for group in self.PIN_GROUPS:
            if group == group_name:
                return [
                    self.pins[name]
                    for name in self.PIN_GROUPS[group_name]
                    if name in self.pins
                ]
        return []


def parse_pins(file_path: str) -> PinConfig:
    """
    Convenience function to parse pins file

    Args:
        file_path: Path to rotator_pins.h

    Returns:
        PinConfig with all parsed data
    """
    parser = PinParser(file_path)
    return parser.parse()


if __name__ == "__main__":
    # Test the pin parser
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pin_parser.py <rotator_pins.h>")
        sys.exit(1)

    config = parse_pins(sys.argv[1])

    print(f"Parsed {len(config.pins)} pin definitions")
    print(f"Digital pins used: {len(config.digital_pins)}")
    print(f"Analog pins used: {len(config.analog_pins)}")

    print(f"\n{len(config.groups)} pin groups:")
    for group in config.groups:
        enabled_count = sum(
            1 for p in group.pins
            if p in config.pins and not config.pins[p].is_disabled
        )
        print(f"  {group.name}: {len(group.pins)} pins ({enabled_count} assigned)")

    if config.conflicts:
        print(f"\n⚠️  {len(config.conflicts)} pin conflicts detected:")
        for conflict in config.conflicts:
            print(f"  {conflict}")
    else:
        print("\n✓ No pin conflicts detected")

    # Show sample pins
    print("\nSample pin assignments:")
    for i, (name, pin_def) in enumerate(list(config.pins.items())[:10]):
        print(f"  {pin_def}")
