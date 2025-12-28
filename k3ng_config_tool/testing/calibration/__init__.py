"""
K3NG Configuration Tool - Calibration Module
Calibration wizards and visualization
"""

from .magnetometer_cal import (
    MagnetometerCalibration,
    CalibrationMode,
    CalibrationStatus,
    CalibrationQuality,
    CalibrationResult as MagCalibrationResult
)

from .angular_cal import (
    AngularCorrection,
    CalibrationPoint,
    ReferenceType,
    CalibrationResult as AngularCalibrationResult
)

from .cal_visualization import CalibrationVisualizer

__all__ = [
    # Magnetometer calibration
    'MagnetometerCalibration',
    'CalibrationMode',
    'CalibrationStatus',
    'CalibrationQuality',
    'MagCalibrationResult',

    # Angular correction
    'AngularCorrection',
    'CalibrationPoint',
    'ReferenceType',
    'AngularCalibrationResult',

    # Visualization
    'CalibrationVisualizer',
]
