"""
Arduino Board Database

Manages board definitions and provides pin capability queries
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass


@dataclass
class BoardDefinition:
    """Board definition with pin capabilities"""
    board_name: str
    board_id: str
    mcu: str
    family: str
    description: str
    memory: Dict[str, float]
    pins: Dict[str, Any]
    capabilities: Dict[str, Any]
    validation_rules: Dict[str, Any]
    notes: List[str]
    recommended_for: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoardDefinition':
        """Create BoardDefinition from dictionary"""
        return cls(
            board_name=data['board_name'],
            board_id=data['board_id'],
            mcu=data['mcu'],
            family=data['family'],
            description=data['description'],
            memory=data['memory'],
            pins=data['pins'],
            capabilities=data['capabilities'],
            validation_rules=data['validation_rules'],
            notes=data['notes'],
            recommended_for=data['recommended_for']
        )


class BoardDatabase:
    """
    Arduino board database manager

    Provides:
    - Loading board definitions from JSON
    - Querying board capabilities
    - Pin validation
    """

    def __init__(self, definitions_dir: Optional[str] = None):
        """
        Initialize board database

        Args:
            definitions_dir: Path to board definitions directory
                            (defaults to data/board_definitions/)
        """
        if definitions_dir is None:
            # Default to data/board_definitions relative to this file
            definitions_dir = Path(__file__).parent.parent / "data" / "board_definitions"

        self.definitions_dir = Path(definitions_dir)
        self.boards: Dict[str, BoardDefinition] = {}
        self._load_boards()

    def _load_boards(self):
        """Load all board definitions from JSON files"""
        if not self.definitions_dir.exists():
            raise FileNotFoundError(f"Board definitions directory not found: {self.definitions_dir}")

        for json_file in self.definitions_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    board = BoardDefinition.from_dict(data)
                    self.boards[board.board_id] = board
            except Exception as e:
                print(f"Warning: Failed to load board definition {json_file}: {e}")

    def list_boards(self) -> List[Dict[str, str]]:
        """
        List all available boards

        Returns:
            List of dicts with board_id, board_name, description
        """
        return [
            {
                'board_id': board.board_id,
                'board_name': board.board_name,
                'description': board.description,
                'family': board.family,
                'mcu': board.mcu
            }
            for board in self.boards.values()
        ]

    def get_all_boards(self) -> List[BoardDefinition]:
        """
        Get all board definitions

        Returns:
            List of BoardDefinition objects
        """
        return list(self.boards.values())

    def get_board(self, board_id: str) -> Optional[BoardDefinition]:
        """
        Get board definition by ID

        Args:
            board_id: Board identifier (e.g., 'arduino_mega_2560')

        Returns:
            BoardDefinition or None if not found
        """
        return self.boards.get(board_id)

    def get_board_summary(self, board_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of board capabilities

        Args:
            board_id: Board identifier

        Returns:
            Dict with memory, pin counts, etc.
        """
        board = self.get_board(board_id)
        if not board:
            return None

        return {
            'board_name': board.board_name,
            'mcu': board.mcu,
            'family': board.family,
            'flash_kb': board.memory['flash_kb'],
            'sram_kb': board.memory['sram_kb'],
            'eeprom_kb': board.memory.get('eeprom_kb', 0),
            'digital_pins': board.pins['digital']['count'],
            'analog_pins': board.pins['analog']['count'],
            'pwm_pins': len(board.pins['pwm']),
            'interrupt_pins': len(board.pins['interrupt']),
            'uart_count': board.capabilities['uart_count'],
            'i2c_count': board.capabilities['i2c_count'],
            'voltage': board.capabilities.get('voltage', 5.0),
            'recommended_for': board.recommended_for
        }

    def is_pwm_pin(self, board_id: str, pin: int) -> bool:
        """
        Check if pin supports PWM

        Args:
            board_id: Board identifier
            pin: Pin number

        Returns:
            True if pin supports PWM
        """
        board = self.get_board(board_id)
        if not board:
            return False

        return pin in board.pins['pwm']

    def is_interrupt_pin(self, board_id: str, pin: int) -> bool:
        """
        Check if pin supports interrupts

        Args:
            board_id: Board identifier
            pin: Pin number

        Returns:
            True if pin supports interrupts
        """
        board = self.get_board(board_id)
        if not board:
            return False

        # Convert interrupt dict keys (which are strings) to integers
        interrupt_pins = [int(p) for p in board.pins['interrupt'].keys()]
        return pin in interrupt_pins

    def is_analog_pin(self, board_id: str, pin: str) -> bool:
        """
        Check if pin is an analog input

        Args:
            board_id: Board identifier
            pin: Pin name (e.g., 'A0')

        Returns:
            True if pin is analog input
        """
        board = self.get_board(board_id)
        if not board:
            return False

        return pin in board.pins['analog']['names']

    def get_pwm_pins(self, board_id: str) -> List[int]:
        """
        Get all PWM-capable pins

        Args:
            board_id: Board identifier

        Returns:
            List of PWM pin numbers
        """
        board = self.get_board(board_id)
        if not board:
            return []

        return board.pins['pwm']

    def get_interrupt_pins(self, board_id: str) -> List[int]:
        """
        Get all interrupt-capable pins

        Args:
            board_id: Board identifier

        Returns:
            List of interrupt pin numbers
        """
        board = self.get_board(board_id)
        if not board:
            return []

        # Convert interrupt dict keys (which are strings) to integers
        return [int(p) for p in board.pins['interrupt'].keys()]

    def get_reserved_pins(self, board_id: str, feature: str) -> List[Any]:
        """
        Get pins reserved for specific feature

        Args:
            board_id: Board identifier
            feature: Feature name (e.g., 'i2c', 'spi', 'serial')

        Returns:
            List of reserved pin numbers/names
        """
        board = self.get_board(board_id)
        if not board:
            return []

        rule_key = f"{feature}_reserved"
        return board.validation_rules.get(rule_key, [])

    def get_pin_capabilities(self, board_id: str, pin: int) -> Set[str]:
        """
        Get all capabilities for a pin

        Args:
            board_id: Board identifier
            pin: Pin number

        Returns:
            Set of capability strings ('digital', 'pwm', 'interrupt', etc.)
        """
        board = self.get_board(board_id)
        if not board:
            return set()

        capabilities = {'digital'}  # All pins are digital

        if self.is_pwm_pin(board_id, pin):
            capabilities.add('pwm')

        if self.is_interrupt_pin(board_id, pin):
            capabilities.add('interrupt')

        # Check if pin is in analog range
        if 'digital_equivalent' in board.pins['analog']:
            if pin in board.pins['analog']['digital_equivalent']:
                capabilities.add('analog_input')

        # Check I2C pins
        i2c = board.pins.get('i2c', {})
        if pin in i2c.values():
            capabilities.add('i2c')

        # Check SPI pins
        spi = board.pins.get('spi', {})
        if pin in spi.values():
            capabilities.add('spi')

        # Check serial pins
        for serial in board.pins.get('serial', []):
            if pin == serial.get('rx') or pin == serial.get('tx'):
                capabilities.add('uart')
                break

        return capabilities

    def validate_pin_assignment(self, board_id: str, pin_name: str, pin_value: Any,
                                required_capability: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Validate a pin assignment

        Args:
            board_id: Board identifier
            pin_name: Configuration pin name (e.g., 'azimuth_speed_voltage')
            pin_value: Assigned pin value (int or 'A0'-style string)
            required_capability: Required capability ('pwm', 'interrupt', etc.)

        Returns:
            Tuple of (is_valid, error_message)
        """
        board = self.get_board(board_id)
        if not board:
            return False, f"Unknown board: {board_id}"

        # Handle disabled pins
        if isinstance(pin_value, int) and pin_value == 0:
            return True, None

        # Handle analog pins
        if isinstance(pin_value, str) and pin_value.startswith('A'):
            if not self.is_analog_pin(board_id, pin_value):
                return False, f"Pin {pin_value} is not a valid analog pin for {board.board_name}"
            # Analog pins don't have PWM/interrupt validation
            return True, None

        # Handle digital pins
        if isinstance(pin_value, int):
            # Check if pin number is in valid range
            pin_range = board.pins['digital']['range']
            if isinstance(pin_range, list) and len(pin_range) == 2:
                # Range is [min, max]
                min_pin, max_pin = pin_range
                if pin_value < min_pin or pin_value > max_pin:
                    return False, f"Pin {pin_value} is out of range ({min_pin}-{max_pin}) for {board.board_name}"
            elif isinstance(pin_range, list):
                # Range is explicit list of valid pins
                if pin_value not in pin_range:
                    return False, f"Pin {pin_value} is not a valid digital pin for {board.board_name}"

            # Check required capability
            if required_capability:
                if required_capability == 'pwm' and not self.is_pwm_pin(board_id, pin_value):
                    pwm_pins = self.get_pwm_pins(board_id)
                    return False, f"Pin {pin_value} does not support PWM. PWM pins: {pwm_pins}"

                if required_capability == 'interrupt' and not self.is_interrupt_pin(board_id, pin_value):
                    int_pins = self.get_interrupt_pins(board_id)
                    return False, f"Pin {pin_value} does not support interrupts. Interrupt pins: {int_pins}"

        return True, None

    def detect_pin_conflicts(self, board_id: str, pin_assignments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect pin conflicts in configuration

        Args:
            board_id: Board identifier
            pin_assignments: Dict of pin_name -> pin_value

        Returns:
            List of conflict dicts with 'pin', 'assignments', 'message'
        """
        board = self.get_board(board_id)
        if not board:
            return []

        conflicts = []

        # Build usage map: pin_value -> [pin_names]
        usage_map: Dict[Any, List[str]] = {}
        for pin_name, pin_value in pin_assignments.items():
            # Skip disabled pins (0 or None)
            if pin_value == 0 or pin_value is None:
                continue

            if pin_value not in usage_map:
                usage_map[pin_value] = []
            usage_map[pin_value].append(pin_name)

        # Find conflicts (same pin used multiple times)
        for pin_value, pin_names in usage_map.items():
            if len(pin_names) > 1:
                conflicts.append({
                    'pin': pin_value,
                    'assignments': pin_names,
                    'message': f"Pin {pin_value} is assigned to multiple functions: {', '.join(pin_names)}"
                })

        return conflicts


if __name__ == "__main__":
    # Test the board database
    db = BoardDatabase()

    print("=== Board Database Test ===\n")

    print("Available boards:")
    for board_info in db.list_boards():
        print(f"  • {board_info['board_name']} ({board_info['board_id']})")
        print(f"    {board_info['description']}")
        print()

    # Test Arduino Mega
    print("\n=== Arduino Mega 2560 ===")
    summary = db.get_board_summary('arduino_mega_2560')
    if summary:
        print(f"MCU: {summary['mcu']}")
        print(f"Memory: {summary['flash_kb']}KB flash, {summary['sram_kb']}KB SRAM, {summary['eeprom_kb']}KB EEPROM")
        print(f"Pins: {summary['digital_pins']} digital, {summary['analog_pins']} analog")
        print(f"PWM: {summary['pwm_pins']} pins, Interrupts: {summary['interrupt_pins']} pins")
        print(f"Serial ports: {summary['uart_count']}")
        print(f"Recommended for: {summary['recommended_for']}")

    # Test pin validation
    print("\n=== Pin Validation ===")
    test_cases = [
        ('arduino_mega_2560', 'motor_pwm', 10, 'pwm'),
        ('arduino_mega_2560', 'encoder_pin', 2, 'interrupt'),
        ('arduino_mega_2560', 'led_pin', 99, None),  # Invalid pin
        ('arduino_uno', 'encoder_az_a', 2, 'interrupt'),
        ('arduino_uno', 'encoder_az_b', 10, 'interrupt'),  # Pin 10 not interrupt on Uno
    ]

    for board_id, pin_name, pin_value, capability in test_cases:
        valid, error = db.validate_pin_assignment(board_id, pin_name, pin_value, capability)
        status = "✓" if valid else "✗"
        message = "" if valid else f" - {error}"
        print(f"{status} {board_id}: {pin_name}={pin_value} (requires {capability}){message}")

    # Test conflict detection
    print("\n=== Conflict Detection ===")
    test_assignments = {
        'rotator_analog_az': 'A0',
        'azimuth_analog_input': 'A0',  # Conflict!
        'azimuth_speed_voltage': 10,
        'brake_az': 10,  # Conflict!
        'rotate_cw': 5,
        'rotate_ccw': 6,
    }

    conflicts = db.detect_pin_conflicts('arduino_mega_2560', test_assignments)
    if conflicts:
        print(f"Found {len(conflicts)} conflict(s):")
        for conflict in conflicts:
            print(f"  ⚠️  {conflict['message']}")
    else:
        print("No conflicts detected")
