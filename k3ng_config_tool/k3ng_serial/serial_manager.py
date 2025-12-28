"""
K3NG Configuration Tool - Serial Manager
Handles serial communication with K3NG rotator controllers
"""

import serial
import serial.tools.list_ports
from typing import List, Optional, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import threading
import queue
import time


@dataclass
class SerialPort:
    """Represents a serial port"""
    device: str
    description: str
    hwid: str

    def __str__(self):
        return f"{self.device} - {self.description}"


class SerialManager(QObject):
    """Manages serial communication with Arduino"""

    # Signals
    connected = pyqtSignal(str)  # port
    disconnected = pyqtSignal()
    data_received = pyqtSignal(str)  # data
    error_occurred = pyqtSignal(str)  # error message

    def __init__(self):
        super().__init__()

        self.serial_port: Optional[serial.Serial] = None
        self.port_name: Optional[str] = None
        self.is_connected = False

        # Read thread
        self.read_thread: Optional[threading.Thread] = None
        self.stop_reading = threading.Event()

        # Write queue for thread-safe writing
        self.write_queue = queue.Queue()

        # Default settings for K3NG controllers
        self.baud_rate = 9600
        self.timeout = 1.0
        self.write_timeout = 1.0

    def list_ports(self) -> List[SerialPort]:
        """List available serial ports"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(SerialPort(
                device=port.device,
                description=port.description,
                hwid=port.hwid
            ))
        return ports

    def connect(self, port: str, baud_rate: int = 9600) -> bool:
        """Connect to a serial port"""
        if self.is_connected:
            self.disconnect()

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=self.write_timeout
            )

            self.port_name = port
            self.baud_rate = baud_rate
            self.is_connected = True

            # Start read thread
            self.stop_reading.clear()
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            # Emit connected signal
            self.connected.emit(port)

            return True

        except serial.SerialException as e:
            self.error_occurred.emit(f"Failed to connect: {str(e)}")
            return False
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from serial port"""
        if not self.is_connected:
            return

        # Stop read thread
        self.stop_reading.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)

        # Close serial port
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception as e:
                self.error_occurred.emit(f"Error closing port: {str(e)}")

        self.serial_port = None
        self.port_name = None
        self.is_connected = False

        # Emit disconnected signal
        self.disconnected.emit()

    def send_command(self, command: str):
        """Send a command to the controller"""
        if not self.is_connected or not self.serial_port:
            self.error_occurred.emit("Not connected to serial port")
            return

        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'

            # Write to serial port
            self.serial_port.write(command.encode('utf-8'))
            self.serial_port.flush()

        except serial.SerialException as e:
            self.error_occurred.emit(f"Failed to send command: {str(e)}")
            self.disconnect()
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error sending command: {str(e)}")

    def _read_loop(self):
        """Read loop running in separate thread"""
        buffer = ""

        while not self.stop_reading.is_set() and self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    # Read available data
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    decoded = data.decode('utf-8', errors='replace')
                    buffer += decoded

                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.rstrip('\r')
                        if line:  # Skip empty lines
                            self.data_received.emit(line)

                else:
                    # Small sleep to avoid busy waiting
                    time.sleep(0.01)

            except serial.SerialException as e:
                self.error_occurred.emit(f"Serial read error: {str(e)}")
                self.disconnect()
                break
            except Exception as e:
                self.error_occurred.emit(f"Unexpected read error: {str(e)}")
                break

    def get_connection_info(self) -> dict:
        """Get current connection information"""
        if not self.is_connected:
            return {
                'connected': False,
                'port': None,
                'baud_rate': None
            }

        return {
            'connected': True,
            'port': self.port_name,
            'baud_rate': self.baud_rate
        }

    def is_port_available(self, port: str) -> bool:
        """Check if a specific port is available"""
        available_ports = self.list_ports()
        return any(p.device == port for p in available_ports)

    def auto_detect_k3ng(self) -> Optional[str]:
        """Try to auto-detect K3NG controller by checking common ports"""
        # Common Arduino ports
        common_ports = ['/dev/ttyACM0', '/dev/ttyUSB0', 'COM3', 'COM4', 'COM5']

        for port_info in self.list_ports():
            # Check if it's in common ports
            if port_info.device in common_ports:
                return port_info.device

            # Check for Arduino in description
            if 'Arduino' in port_info.description or 'USB Serial' in port_info.description:
                return port_info.device

        return None

    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()
