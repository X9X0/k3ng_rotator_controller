"""
K3NG Configuration Tool - Magnetometer Calibration
Magnetometer calibration wizard for compass-based position sensors
"""

import time
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass


class CalibrationMode(Enum):
    """Calibration mode selection"""
    AUTOMATIC = "automatic"  # Controller rotates 360° automatically
    MANUAL = "manual"        # User manually rotates antenna


class CalibrationStatus(Enum):
    """Calibration status"""
    IDLE = "idle"
    CHECKING = "checking"
    CALIBRATING = "calibrating"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"


class CalibrationQuality(Enum):
    """Calibration quality assessment"""
    GOOD = "good"
    SUSPECT = "suspect"
    POOR = "poor"
    UNKNOWN = "unknown"


@dataclass
class CalibrationResult:
    """Result of calibration operation"""
    success: bool
    quality: CalibrationQuality
    message: str
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class MagnetometerCalibration:
    """
    Magnetometer calibration wizard

    Guides user through calibration of compass-based azimuth sensors
    including HMC5883L, QMC5883, LSM303, etc.
    """

    def __init__(self, command_interface=None):
        """
        Initialize magnetometer calibration

        Args:
            command_interface: K3NGCommandInterface for serial communication
        """
        self.command_interface = command_interface
        self.status = CalibrationStatus.IDLE
        self.mode = None
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        self.result: Optional[CalibrationResult] = None

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """
        Set callback for progress updates

        Args:
            callback: Function(message: str, progress: int) called during calibration
                     progress is 0-100
        """
        self.progress_callback = callback

    def _update_progress(self, message: str, progress: int):
        """Update progress and call callback if set"""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def check_sensor(self) -> bool:
        """
        Check if magnetometer sensor is present and responding

        Returns:
            True if sensor is detected, False otherwise
        """
        if not self.command_interface:
            return False

        if not self.command_interface.serial.is_connected:
            return False

        self.status = CalibrationStatus.CHECKING
        self._update_progress("Checking magnetometer sensor...", 10)

        try:
            # Query calibration status to check sensor presence
            self.command_interface.query_calibration_status()
            time.sleep(0.5)

            # Check for response
            responses = self.command_interface.get_last_responses(3)

            # Look for calibration-related keywords
            for response in responses:
                if any(keyword in response.lower() for keyword in
                       ['cal', 'mag', 'compass', 'azimuth']):
                    self._update_progress("Magnetometer sensor detected", 20)
                    return True

            self._update_progress("No magnetometer detected", 0)
            return False

        except Exception as e:
            self._update_progress(f"Error checking sensor: {str(e)}", 0)
            return False

    def start_automatic_calibration(self) -> CalibrationResult:
        """
        Start automatic magnetometer calibration

        Controller will rotate 360° to gather calibration data

        Returns:
            CalibrationResult with success status and quality
        """
        if not self.command_interface or not self.command_interface.serial.is_connected:
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message="Serial port not connected"
            )

        self.mode = CalibrationMode.AUTOMATIC
        self.status = CalibrationStatus.CALIBRATING
        self._update_progress("Starting automatic magnetometer calibration...", 30)

        try:
            # Send automatic calibration command
            self.command_interface.calibrate_magnetometer_auto()
            self._update_progress("Rotating 360° to gather data...", 40)

            # Wait for rotation to complete (estimate ~60 seconds for full rotation)
            # Poll status during rotation
            for i in range(60):
                time.sleep(1)
                progress = 40 + int((i / 60) * 40)  # 40-80%
                self._update_progress(f"Calibrating... ({i+1}/60 sec)", progress)

                # Could poll status here if there's a status command

            self._update_progress("Rotation complete, processing data...", 85)
            time.sleep(2)

            # Verify calibration quality
            return self._verify_calibration()

        except Exception as e:
            self.status = CalibrationStatus.ERROR
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message=f"Calibration failed: {str(e)}"
            )

    def start_manual_calibration(self) -> CalibrationResult:
        """
        Start manual magnetometer calibration

        User manually rotates antenna 360° while calibration data is gathered

        Returns:
            CalibrationResult with success status and quality
        """
        if not self.command_interface or not self.command_interface.serial.is_connected:
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message="Serial port not connected"
            )

        self.mode = CalibrationMode.MANUAL
        self.status = CalibrationStatus.CALIBRATING
        self._update_progress("Starting manual magnetometer calibration...", 30)

        try:
            # Send manual calibration start command
            self.command_interface.calibrate_magnetometer_start()
            self._update_progress("Calibration started - rotate antenna 360°", 40)
            time.sleep(0.5)

            return CalibrationResult(
                success=True,
                quality=CalibrationQuality.UNKNOWN,
                message="Manual calibration started - rotate antenna 360° and call end_manual_calibration()",
                details={"manual_mode": True}
            )

        except Exception as e:
            self.status = CalibrationStatus.ERROR
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message=f"Failed to start calibration: {str(e)}"
            )

    def end_manual_calibration(self) -> CalibrationResult:
        """
        End manual magnetometer calibration

        Call this after user has rotated antenna 360°

        Returns:
            CalibrationResult with success status and quality
        """
        if not self.command_interface or not self.command_interface.serial.is_connected:
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message="Serial port not connected"
            )

        self._update_progress("Ending manual calibration...", 85)

        try:
            # Send manual calibration end command
            self.command_interface.calibrate_magnetometer_end()
            time.sleep(0.5)

            self._update_progress("Processing calibration data...", 90)
            time.sleep(1)

            # Verify calibration quality
            return self._verify_calibration()

        except Exception as e:
            self.status = CalibrationStatus.ERROR
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message=f"Failed to end calibration: {str(e)}"
            )

    def _verify_calibration(self) -> CalibrationResult:
        """
        Verify calibration quality

        Returns:
            CalibrationResult with quality assessment
        """
        self.status = CalibrationStatus.VERIFYING
        self._update_progress("Verifying calibration quality...", 90)

        try:
            # Query calibration quality
            self.command_interface.query_calibration_quality()
            time.sleep(0.5)

            # Check responses
            responses = self.command_interface.get_last_responses(3)

            quality = CalibrationQuality.UNKNOWN
            message = "Calibration complete"
            details = {}

            # Parse quality response
            for response in responses:
                response_lower = response.lower()

                if 'good' in response_lower:
                    quality = CalibrationQuality.GOOD
                    message = "Calibration successful - quality is GOOD"
                elif 'suspect' in response_lower:
                    quality = CalibrationQuality.SUSPECT
                    message = "Calibration complete - quality is SUSPECT, consider recalibrating"
                elif 'poor' in response_lower:
                    quality = CalibrationQuality.POOR
                    message = "Calibration complete - quality is POOR, recalibration recommended"

                # Extract calibration values if present
                if 'min' in response_lower or 'max' in response_lower:
                    details['raw_response'] = response

            self._update_progress(message, 95)

            # Save to EEPROM
            self._update_progress("Saving calibration to EEPROM...", 98)
            self.save_calibration()

            self.status = CalibrationStatus.COMPLETE
            self._update_progress("Calibration complete!", 100)

            self.result = CalibrationResult(
                success=True,
                quality=quality,
                message=message,
                details=details
            )
            return self.result

        except Exception as e:
            self.status = CalibrationStatus.ERROR
            return CalibrationResult(
                success=False,
                quality=CalibrationQuality.UNKNOWN,
                message=f"Quality verification failed: {str(e)}"
            )

    def save_calibration(self):
        """Save calibration data to EEPROM"""
        if not self.command_interface or not self.command_interface.serial.is_connected:
            return

        try:
            # Save to EEPROM and restart
            self.command_interface.save_and_restart()
            time.sleep(0.5)
        except Exception:
            # Non-critical error
            pass

    def get_calibration_status(self) -> Dict[str, Any]:
        """
        Get current calibration status from controller

        Returns:
            Dictionary with calibration status information
        """
        if not self.command_interface or not self.command_interface.serial.is_connected:
            return {"error": "Not connected"}

        try:
            self.command_interface.query_calibration_status()
            time.sleep(0.5)

            responses = self.command_interface.get_last_responses(5)

            return {
                "status": self.status.value,
                "mode": self.mode.value if self.mode else None,
                "responses": responses
            }

        except Exception as e:
            return {"error": str(e)}
