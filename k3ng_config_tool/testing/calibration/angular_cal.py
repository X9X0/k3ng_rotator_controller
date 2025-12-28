"""
K3NG Configuration Tool - Angular Correction Calibration
Multi-point angular correction calibration wizard
"""

import time
from typing import List, Optional, Callable, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field


class ReferenceType(Enum):
    """Reference point type for calibration"""
    SUN = "sun"
    MOON = "moon"
    MANUAL = "manual"  # User-specified azimuth/elevation


class CalibrationStatus(Enum):
    """Calibration status"""
    IDLE = "idle"
    COLLECTING = "collecting"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class CalibrationPoint:
    """Single calibration point"""
    reference_azimuth: float       # True azimuth (from calculation or user input)
    reference_elevation: float     # True elevation (from calculation or user input)
    measured_azimuth: float        # Measured azimuth from rotator
    measured_elevation: float      # Measured elevation from rotator
    reference_type: ReferenceType  # Type of reference used
    timestamp: float = field(default_factory=time.time)

    @property
    def azimuth_error(self) -> float:
        """Calculate azimuth error"""
        return self.measured_azimuth - self.reference_azimuth

    @property
    def elevation_error(self) -> float:
        """Calculate elevation error"""
        return self.measured_elevation - self.reference_elevation


@dataclass
class CalibrationResult:
    """Result of angular calibration"""
    success: bool
    message: str
    points: List[CalibrationPoint] = field(default_factory=list)
    azimuth_correction_table: List[Tuple[float, float]] = field(default_factory=list)
    elevation_correction_table: List[Tuple[float, float]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class AngularCorrection:
    """
    Angular correction calibration wizard

    Builds multi-point calibration table to correct azimuth/elevation errors
    across the full rotation range. Supports up to 8 calibration points.
    """

    MAX_CALIBRATION_POINTS = 8

    def __init__(self, command_interface=None):
        """
        Initialize angular correction calibration

        Args:
            command_interface: K3NGCommandInterface for serial communication
        """
        self.command_interface = command_interface
        self.status = CalibrationStatus.IDLE
        self.calibration_points: List[CalibrationPoint] = []
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

    def clear_calibration_points(self):
        """Clear all calibration points"""
        self.calibration_points.clear()
        self.result = None
        self.status = CalibrationStatus.IDLE

    def add_calibration_point_manual(
        self,
        reference_azimuth: float,
        reference_elevation: float
    ) -> CalibrationPoint:
        """
        Add calibration point with manual reference values

        User specifies the true azimuth/elevation, and the function
        queries the rotator for measured values.

        Args:
            reference_azimuth: True azimuth in degrees (0-360)
            reference_elevation: True elevation in degrees (0-180)

        Returns:
            CalibrationPoint with measured values

        Raises:
            ValueError: If max calibration points exceeded
        """
        if len(self.calibration_points) >= self.MAX_CALIBRATION_POINTS:
            raise ValueError(f"Maximum {self.MAX_CALIBRATION_POINTS} calibration points allowed")

        if not self.command_interface or not self.command_interface.serial.is_connected:
            raise RuntimeError("Serial port not connected")

        self.status = CalibrationStatus.COLLECTING
        point_num = len(self.calibration_points) + 1
        self._update_progress(f"Collecting calibration point {point_num}...",
                            (point_num - 1) * 100 // self.MAX_CALIBRATION_POINTS)

        try:
            # Query current azimuth
            self.command_interface.query_azimuth()
            time.sleep(0.3)
            az_responses = self.command_interface.get_last_responses(1)

            # Query current elevation
            self.command_interface.query_elevation()
            time.sleep(0.3)
            el_responses = self.command_interface.get_last_responses(1)

            # Parse measured values
            measured_azimuth = self._parse_azimuth_response(az_responses)
            measured_elevation = self._parse_elevation_response(el_responses)

            # Create calibration point
            point = CalibrationPoint(
                reference_azimuth=reference_azimuth,
                reference_elevation=reference_elevation,
                measured_azimuth=measured_azimuth,
                measured_elevation=measured_elevation,
                reference_type=ReferenceType.MANUAL
            )

            self.calibration_points.append(point)

            self._update_progress(
                f"Point {point_num} added: Az error={point.azimuth_error:.1f}°, "
                f"El error={point.elevation_error:.1f}°",
                point_num * 100 // self.MAX_CALIBRATION_POINTS
            )

            return point

        except Exception as e:
            self.status = CalibrationStatus.ERROR
            raise RuntimeError(f"Failed to collect calibration point: {str(e)}")

    def add_calibration_point_sun(self) -> CalibrationPoint:
        """
        Add calibration point using sun as reference

        Requires FEATURE_SUN_TRACKING to be enabled on controller

        Returns:
            CalibrationPoint with sun as reference

        Raises:
            ValueError: If max calibration points exceeded
            RuntimeError: If sun tracking not available
        """
        if len(self.calibration_points) >= self.MAX_CALIBRATION_POINTS:
            raise ValueError(f"Maximum {self.MAX_CALIBRATION_POINTS} calibration points allowed")

        if not self.command_interface or not self.command_interface.serial.is_connected:
            raise RuntimeError("Serial port not connected")

        # This would require implementation of sun tracking query commands
        # For now, raise not implemented
        raise NotImplementedError("Sun reference calibration requires controller support")

    def add_calibration_point_moon(self) -> CalibrationPoint:
        """
        Add calibration point using moon as reference

        Requires FEATURE_MOON_TRACKING to be enabled on controller

        Returns:
            CalibrationPoint with moon as reference

        Raises:
            ValueError: If max calibration points exceeded
            RuntimeError: If moon tracking not available
        """
        if len(self.calibration_points) >= self.MAX_CALIBRATION_POINTS:
            raise ValueError(f"Maximum {self.MAX_CALIBRATION_POINTS} calibration points allowed")

        if not self.command_interface or not self.command_interface.serial.is_connected:
            raise RuntimeError("Serial port not connected")

        # This would require implementation of moon tracking query commands
        # For now, raise not implemented
        raise NotImplementedError("Moon reference calibration requires controller support")

    def _parse_azimuth_response(self, responses: List[str]) -> float:
        """
        Parse azimuth from controller response

        Args:
            responses: List of response strings

        Returns:
            Azimuth in degrees

        Raises:
            ValueError: If unable to parse response
        """
        if not responses:
            raise ValueError("No azimuth response received")

        # Expected formats vary: "AZ=123", "123", etc.
        # This is a simple parser - may need refinement based on actual responses
        response = responses[0].strip()

        # Try to extract numeric value
        import re
        match = re.search(r'(\d+\.?\d*)', response)
        if match:
            return float(match.group(1))

        raise ValueError(f"Unable to parse azimuth from: {response}")

    def _parse_elevation_response(self, responses: List[str]) -> float:
        """
        Parse elevation from controller response

        Args:
            responses: List of response strings

        Returns:
            Elevation in degrees

        Raises:
            ValueError: If unable to parse response
        """
        if not responses:
            raise ValueError("No elevation response received")

        # Expected formats vary: "EL=45", "45", etc.
        response = responses[0].strip()

        # Try to extract numeric value
        import re
        match = re.search(r'(\d+\.?\d*)', response)
        if match:
            return float(match.group(1))

        raise ValueError(f"Unable to parse elevation from: {response}")

    def generate_correction_table(self) -> CalibrationResult:
        """
        Generate correction table from calibration points

        Sorts points by azimuth/elevation and creates lookup tables
        for interpolation.

        Returns:
            CalibrationResult with correction tables

        Raises:
            ValueError: If insufficient calibration points
        """
        if len(self.calibration_points) < 2:
            raise ValueError("At least 2 calibration points required")

        self.status = CalibrationStatus.PROCESSING
        self._update_progress("Generating correction tables...", 90)

        try:
            # Sort points by reference azimuth
            sorted_points = sorted(self.calibration_points,
                                 key=lambda p: p.reference_azimuth)

            # Build azimuth correction table
            azimuth_table = [
                (point.reference_azimuth, point.azimuth_error)
                for point in sorted_points
            ]

            # Build elevation correction table
            elevation_table = [
                (point.reference_elevation, point.elevation_error)
                for point in sorted_points
            ]

            # Calculate statistics
            avg_az_error = sum(abs(p.azimuth_error) for p in self.calibration_points) / len(self.calibration_points)
            avg_el_error = sum(abs(p.elevation_error) for p in self.calibration_points) / len(self.calibration_points)
            max_az_error = max(abs(p.azimuth_error) for p in self.calibration_points)
            max_el_error = max(abs(p.elevation_error) for p in self.calibration_points)

            details = {
                'point_count': len(self.calibration_points),
                'avg_azimuth_error': avg_az_error,
                'avg_elevation_error': avg_el_error,
                'max_azimuth_error': max_az_error,
                'max_elevation_error': max_el_error
            }

            self.status = CalibrationStatus.COMPLETE
            self._update_progress("Correction table generated", 100)

            self.result = CalibrationResult(
                success=True,
                message=f"Generated correction table with {len(self.calibration_points)} points",
                points=self.calibration_points.copy(),
                azimuth_correction_table=azimuth_table,
                elevation_correction_table=elevation_table,
                details=details
            )

            return self.result

        except Exception as e:
            self.status = CalibrationStatus.ERROR
            raise RuntimeError(f"Failed to generate correction table: {str(e)}")

    def export_to_settings(self) -> str:
        """
        Export correction table to rotator_settings.h format

        Returns:
            String containing C code for correction tables

        Raises:
            ValueError: If correction table not generated
        """
        if not self.result or not self.result.success:
            raise ValueError("No correction table available - generate first")

        output = []
        output.append("// Angular correction calibration tables")
        output.append("// Generated by K3NG Configuration Tool")
        output.append("")

        # Azimuth correction table
        output.append(f"#define AZIMUTH_CORRECTION_SIZE {len(self.result.azimuth_correction_table)}")
        output.append("float azimuth_calibration_from[] = {")
        azimuths = [f"  {az:.1f}" for az, _ in self.result.azimuth_correction_table]
        output.append(",\n".join(azimuths))
        output.append("};")
        output.append("")

        output.append("float azimuth_calibration_to[] = {")
        corrections = [f"  {az + err:.1f}" for az, err in self.result.azimuth_correction_table]
        output.append(",\n".join(corrections))
        output.append("};")
        output.append("")

        # Elevation correction table
        output.append(f"#define ELEVATION_CORRECTION_SIZE {len(self.result.elevation_correction_table)}")
        output.append("float elevation_calibration_from[] = {")
        elevations = [f"  {el:.1f}" for el, _ in self.result.elevation_correction_table]
        output.append(",\n".join(elevations))
        output.append("};")
        output.append("")

        output.append("float elevation_calibration_to[] = {")
        corrections = [f"  {el + err:.1f}" for el, err in self.result.elevation_correction_table]
        output.append(",\n".join(corrections))
        output.append("};")

        return "\n".join(output)

    def get_calibration_summary(self) -> str:
        """
        Get human-readable summary of calibration

        Returns:
            Summary string
        """
        if not self.calibration_points:
            return "No calibration points collected"

        lines = []
        lines.append(f"Angular Correction Calibration Summary")
        lines.append(f"=" * 50)
        lines.append(f"Points collected: {len(self.calibration_points)}/{self.MAX_CALIBRATION_POINTS}")
        lines.append("")

        for i, point in enumerate(self.calibration_points, 1):
            lines.append(f"Point {i} ({point.reference_type.value}):")
            lines.append(f"  Reference:  Az={point.reference_azimuth:6.2f}°  El={point.reference_elevation:6.2f}°")
            lines.append(f"  Measured:   Az={point.measured_azimuth:6.2f}°  El={point.measured_elevation:6.2f}°")
            lines.append(f"  Error:      Az={point.azimuth_error:+6.2f}°  El={point.elevation_error:+6.2f}°")
            lines.append("")

        if self.result and self.result.success:
            lines.append("Statistics:")
            lines.append(f"  Avg Az Error: {self.result.details['avg_azimuth_error']:.2f}°")
            lines.append(f"  Avg El Error: {self.result.details['avg_elevation_error']:.2f}°")
            lines.append(f"  Max Az Error: {self.result.details['max_azimuth_error']:.2f}°")
            lines.append(f"  Max El Error: {self.result.details['max_elevation_error']:.2f}°")

        return "\n".join(lines)
