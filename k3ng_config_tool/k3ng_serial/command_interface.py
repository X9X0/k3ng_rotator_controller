"""
K3NG Configuration Tool - Command Interface
Provides high-level interface for K3NG backslash commands
"""

from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from .serial_manager import SerialManager


class K3NGCommandInterface(QObject):
    """High-level interface for K3NG controller commands"""

    # Signals
    response_received = pyqtSignal(str, str)  # command, response
    command_sent = pyqtSignal(str)  # command

    def __init__(self, serial_manager: SerialManager):
        super().__init__()
        self.serial = serial_manager

        # Connect to serial manager signals
        self.serial.data_received.connect(self._on_data_received)

        # Response tracking
        self.last_command = None
        self.response_buffer = []

    def _on_data_received(self, data: str):
        """Handle data received from serial port"""
        self.response_buffer.append(data)
        if self.last_command:
            self.response_received.emit(self.last_command, data)

    def send_command(self, command: str):
        """Send a command and track it"""
        self.last_command = command
        self.response_buffer.clear()
        self.serial.send_command(command)
        self.command_sent.emit(command)

    # ===== Query Commands =====

    def query_azimuth(self):
        """Query current azimuth position"""
        self.send_command('\\?AZ')

    def query_elevation(self):
        """Query current elevation position"""
        self.send_command('\\?EL')

    def query_code_version(self):
        """Query code version"""
        self.send_command('\\?CV')

    def query_calibration_status(self):
        """Query comprehensive calibration status"""
        self.send_command('\\?CAL')

    def query_calibration_quality(self):
        """Query quick calibration quality check"""
        self.send_command('\\?CQ')

    # ===== I/O Commands =====

    def digital_output_init(self, pin: int):
        """Initialize pin as digital output"""
        self.send_command(f'\\?DO{pin:02d}')

    def digital_set_high(self, pin: int):
        """Set digital pin HIGH"""
        self.send_command(f'\\?DH{pin:02d}')

    def digital_set_low(self, pin: int):
        """Set digital pin LOW"""
        self.send_command(f'\\?DL{pin:02d}')

    def digital_read(self, pin: int):
        """Read digital pin"""
        self.send_command(f'\\?DR{pin:02d}')

    def analog_read(self, pin: int):
        """Read analog pin (0-1023)"""
        self.send_command(f'\\?AR{pin:02d}')

    def analog_write_pwm(self, pin: int, value: int):
        """Write PWM value to pin (0-255)"""
        self.send_command(f'\\?AW{pin:02d}{value:03d}')

    # ===== Calibration Commands =====

    def start_mag_calibration_auto(self):
        """Start automatic magnetometer calibration (360° rotation)"""
        self.send_command('\\XMG')

    def start_mag_calibration_manual(self):
        """Start manual magnetometer calibration"""
        self.send_command('\\XMGs')

    def end_mag_calibration_manual(self):
        """End manual magnetometer calibration and save"""
        self.send_command('\\XMGe')

    def show_mag_calibration_values(self):
        """Show current magnetometer calibration values"""
        self.send_command('\\XC')

    def show_calibration_tables(self):
        """Display all calibration tables"""
        self.send_command('\\X')

    def add_azimuth_calibration_point(self, measured: float, actual: float):
        """Add azimuth calibration point"""
        self.send_command(f'\\XAA{measured:.1f},{actual:.1f}')

    def add_elevation_calibration_point(self, measured: float, actual: float):
        """Add elevation calibration point"""
        self.send_command(f'\\XAE{measured:.1f},{actual:.1f}')

    def remove_azimuth_calibration_point(self, index: int):
        """Remove azimuth calibration point"""
        self.send_command(f'\\XRA{index}')

    def remove_elevation_calibration_point(self, index: int):
        """Remove elevation calibration point"""
        self.send_command(f'\\XRE{index}')

    def clear_azimuth_calibration(self):
        """Clear azimuth calibration table"""
        self.send_command('\\XCA')

    def clear_elevation_calibration(self):
        """Clear elevation calibration table"""
        self.send_command('\\XCE')

    def clear_all_calibration(self):
        """Clear all calibration tables"""
        self.send_command('\\X0')

    def calibrate_using_sun(self):
        """Add calibration point using sun position"""
        self.send_command('\\XS')

    def calibrate_using_moon(self):
        """Add calibration point using moon position"""
        self.send_command('\\XM')

    # ===== Movement Commands =====

    def rotate_azimuth(self, degrees: float):
        """Rotate to specific azimuth"""
        self.send_command(f'M{int(degrees)}')

    def rotate_elevation(self, degrees: float):
        """Rotate to specific elevation"""
        self.send_command(f'M000 {int(degrees)}')

    def rotate_azimuth_elevation(self, az_degrees: float, el_degrees: float):
        """Rotate to specific azimuth and elevation"""
        self.send_command(f'M{int(az_degrees):03d} {int(el_degrees):03d}')

    def stop_rotation(self):
        """Stop all rotation"""
        self.send_command('S')

    def rotate_cw(self):
        """Start rotating clockwise"""
        self.send_command('R')

    def rotate_ccw(self):
        """Start rotating counter-clockwise"""
        self.send_command('L')

    def rotate_up(self):
        """Start rotating up"""
        self.send_command('U')

    def rotate_down(self):
        """Start rotating down"""
        self.send_command('D')

    # ===== Speed Commands (Yaesu) =====

    def set_speed_x1(self):
        """Set speed to X1 (slowest)"""
        self.send_command('X1')

    def set_speed_x2(self):
        """Set speed to X2"""
        self.send_command('X2')

    def set_speed_x3(self):
        """Set speed to X3"""
        self.send_command('X3')

    def set_speed_x4(self):
        """Set speed to X4 (fastest)"""
        self.send_command('X4')

    # ===== System Commands =====

    def save_and_reboot(self):
        """Save to EEPROM and restart"""
        self.send_command('\\Q')

    def reboot(self):
        """Reboot controller"""
        self.send_command('\\?RB')

    def print_help(self):
        """Print help information"""
        self.send_command('H')

    # ===== Status Commands =====

    def get_azimuth_position(self):
        """Get azimuth position (Yaesu C command)"""
        self.send_command('C')

    def get_azimuth_elevation_position(self):
        """Get azimuth and elevation position (Yaesu C command)"""
        self.send_command('C2')

    # ===== Utility Methods =====

    def send_raw(self, command: str):
        """Send raw command string"""
        self.send_command(command)

    def clear_response_buffer(self):
        """Clear the response buffer"""
        self.response_buffer.clear()

    def get_last_responses(self, count: int = 10) -> list:
        """Get last N responses"""
        return self.response_buffer[-count:] if self.response_buffer else []
