"""
K3NG Configuration Tool - Calibration Data Visualization
Matplotlib-based visualization for calibration data
"""

import matplotlib.pyplot as plt
import matplotlib.figure
from typing import List, Optional, Tuple
import numpy as np

from .angular_cal import CalibrationPoint, AngularCorrection


class CalibrationVisualizer:
    """
    Visualization tools for calibration data

    Creates plots showing calibration points, error distributions,
    and correction curves.
    """

    def __init__(self):
        """Initialize visualizer"""
        self.figure: Optional[matplotlib.figure.Figure] = None

    def plot_angular_correction(
        self,
        calibration: AngularCorrection,
        show_azimuth: bool = True,
        show_elevation: bool = True
    ) -> matplotlib.figure.Figure:
        """
        Plot angular correction calibration data

        Args:
            calibration: AngularCorrection with collected points
            show_azimuth: Include azimuth correction plot
            show_elevation: Include elevation correction plot

        Returns:
            Matplotlib Figure object
        """
        if not calibration.calibration_points:
            raise ValueError("No calibration points to plot")

        # Determine subplot layout
        num_plots = sum([show_azimuth, show_elevation])
        if num_plots == 0:
            raise ValueError("Must show at least one plot")

        fig, axes = plt.subplots(num_plots, 1, figsize=(10, 5 * num_plots))
        if num_plots == 1:
            axes = [axes]

        fig.suptitle('Angular Correction Calibration', fontsize=14, fontweight='bold')

        plot_idx = 0

        # Azimuth correction plot
        if show_azimuth:
            ax = axes[plot_idx]
            self._plot_azimuth_correction(ax, calibration.calibration_points)
            plot_idx += 1

        # Elevation correction plot
        if show_elevation:
            ax = axes[plot_idx]
            self._plot_elevation_correction(ax, calibration.calibration_points)

        plt.tight_layout()
        self.figure = fig
        return fig

    def _plot_azimuth_correction(self, ax, points: List[CalibrationPoint]):
        """Plot azimuth correction data"""
        # Extract data
        ref_azimuths = [p.reference_azimuth for p in points]
        errors = [p.azimuth_error for p in points]

        # Sort by azimuth for curve plotting
        sorted_indices = np.argsort(ref_azimuths)
        sorted_az = np.array(ref_azimuths)[sorted_indices]
        sorted_err = np.array(errors)[sorted_indices]

        # Plot error points
        ax.scatter(ref_azimuths, errors, s=100, c='red',
                  marker='o', label='Measured Error', zorder=3)

        # Plot error curve
        if len(points) > 1:
            ax.plot(sorted_az, sorted_err, 'b--', alpha=0.5,
                   label='Correction Curve', zorder=2)

        # Zero error line
        ax.axhline(y=0, color='green', linestyle='-', linewidth=1,
                  alpha=0.3, label='Zero Error')

        # Grid
        ax.grid(True, alpha=0.3)

        # Labels
        ax.set_xlabel('Reference Azimuth (degrees)', fontsize=11)
        ax.set_ylabel('Error (degrees)', fontsize=11)
        ax.set_title('Azimuth Correction', fontsize=12, fontweight='bold')
        ax.legend(loc='best')

        # Annotate points
        for i, (az, err) in enumerate(zip(ref_azimuths, errors)):
            ax.annotate(f'P{i+1}\n{err:+.1f}°',
                       xy=(az, err),
                       xytext=(10, 10),
                       textcoords='offset points',
                       fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    def _plot_elevation_correction(self, ax, points: List[CalibrationPoint]):
        """Plot elevation correction data"""
        # Extract data
        ref_elevations = [p.reference_elevation for p in points]
        errors = [p.elevation_error for p in points]

        # Sort by elevation for curve plotting
        sorted_indices = np.argsort(ref_elevations)
        sorted_el = np.array(ref_elevations)[sorted_indices]
        sorted_err = np.array(errors)[sorted_indices]

        # Plot error points
        ax.scatter(ref_elevations, errors, s=100, c='red',
                  marker='s', label='Measured Error', zorder=3)

        # Plot error curve
        if len(points) > 1:
            ax.plot(sorted_el, sorted_err, 'b--', alpha=0.5,
                   label='Correction Curve', zorder=2)

        # Zero error line
        ax.axhline(y=0, color='green', linestyle='-', linewidth=1,
                  alpha=0.3, label='Zero Error')

        # Grid
        ax.grid(True, alpha=0.3)

        # Labels
        ax.set_xlabel('Reference Elevation (degrees)', fontsize=11)
        ax.set_ylabel('Error (degrees)', fontsize=11)
        ax.set_title('Elevation Correction', fontsize=12, fontweight='bold')
        ax.legend(loc='best')

        # Annotate points
        for i, (el, err) in enumerate(zip(ref_elevations, errors)):
            ax.annotate(f'P{i+1}\n{err:+.1f}°',
                       xy=(el, err),
                       xytext=(10, 10),
                       textcoords='offset points',
                       fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    def plot_error_distribution(
        self,
        points: List[CalibrationPoint]
    ) -> matplotlib.figure.Figure:
        """
        Plot error distribution histogram

        Args:
            points: List of calibration points

        Returns:
            Matplotlib Figure object
        """
        if not points:
            raise ValueError("No calibration points to plot")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Calibration Error Distribution', fontsize=14, fontweight='bold')

        # Azimuth error histogram
        az_errors = [p.azimuth_error for p in points]
        ax1.hist(az_errors, bins=20, color='blue', alpha=0.7, edgecolor='black')
        ax1.axvline(x=0, color='green', linestyle='--', linewidth=2, label='Zero Error')
        ax1.axvline(x=np.mean(az_errors), color='red', linestyle='--',
                   linewidth=2, label=f'Mean: {np.mean(az_errors):.2f}°')
        ax1.set_xlabel('Azimuth Error (degrees)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Azimuth Error Distribution', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Elevation error histogram
        el_errors = [p.elevation_error for p in points]
        ax2.hist(el_errors, bins=20, color='orange', alpha=0.7, edgecolor='black')
        ax2.axvline(x=0, color='green', linestyle='--', linewidth=2, label='Zero Error')
        ax2.axvline(x=np.mean(el_errors), color='red', linestyle='--',
                   linewidth=2, label=f'Mean: {np.mean(el_errors):.2f}°')
        ax2.set_xlabel('Elevation Error (degrees)', fontsize=11)
        ax2.set_ylabel('Frequency', fontsize=11)
        ax2.set_title('Elevation Error Distribution', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        self.figure = fig
        return fig

    def plot_polar_azimuth(
        self,
        points: List[CalibrationPoint]
    ) -> matplotlib.figure.Figure:
        """
        Plot azimuth calibration on polar plot

        Args:
            points: List of calibration points

        Returns:
            Matplotlib Figure object
        """
        if not points:
            raise ValueError("No calibration points to plot")

        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='polar')

        # Convert azimuth to radians (0° = North = top of plot)
        # Matplotlib polar: 0 is East, rotates counter-clockwise
        # Azimuth: 0 is North, rotates clockwise
        # Conversion: theta = (90 - azimuth) * pi/180
        ref_theta = np.radians(90 - np.array([p.reference_azimuth for p in points]))
        meas_theta = np.radians(90 - np.array([p.measured_azimuth for p in points]))

        # Plot reference points
        ax.scatter(ref_theta, [1] * len(points), s=200, c='green',
                  marker='o', label='Reference Position', zorder=3, alpha=0.7)

        # Plot measured points
        ax.scatter(meas_theta, [1] * len(points), s=200, c='red',
                  marker='x', label='Measured Position', zorder=3)

        # Draw error vectors
        for i, (ref, meas) in enumerate(zip(ref_theta, meas_theta)):
            ax.plot([ref, meas], [1, 1], 'b-', alpha=0.5, linewidth=2)
            # Annotate point number
            ax.text(ref, 1.1, f'P{i+1}', ha='center', va='center',
                   bbox=dict(boxstyle='circle', facecolor='yellow', alpha=0.7))

        # Configure plot
        ax.set_theta_zero_location('N')  # 0° at top (North)
        ax.set_theta_direction(-1)       # Clockwise
        ax.set_ylim(0, 1.3)
        ax.set_yticks([])                # Hide radial ticks
        ax.set_title('Azimuth Calibration (Polar View)\n' +
                    'Green=Reference, Red=Measured, Blue=Error',
                    fontsize=12, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()
        self.figure = fig
        return fig

    def save_figure(self, filename: str, dpi: int = 300):
        """
        Save current figure to file

        Args:
            filename: Output filename (e.g., 'calibration.png')
            dpi: Resolution in dots per inch
        """
        if not self.figure:
            raise ValueError("No figure to save - create a plot first")

        self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')

    def close(self):
        """Close all figures"""
        if self.figure:
            plt.close(self.figure)
            self.figure = None
