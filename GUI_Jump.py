import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from PyQt5.QtCore import Qt


import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QHBoxLayout,
    QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor


class GUIJump(QWidget):
    def __init__(self, color_palette, device_info, jumps, metrics_widget):
        super().__init__()
        self.color_palette = color_palette
        self.device_info = device_info
        self.jumps = jumps
        self.metrics_widget = metrics_widget
        self.plots = {}
        self.curves = {}
        self.vertical_lines = {}
        self.curr_jump_idx = 0

        self.init_plots()

    def init_plots(self):
        # Set light mode for pyqtgraph globally
        pg.setConfigOption("background", self.color_palette["plot_bg"])
        pg.setConfigOption("foreground", self.color_palette["plot_fg"])

        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {self.color_palette['block_bg']};
                font-size: 18px;
                font-family: 'Roboto', sans-serif;
                border-radius: 10px;
            }}
            """
        )
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Outer frame for styling consistency
        outer_frame = QFrame(self)
        outer_frame.setStyleSheet(
            f"""
            background-color: {self.color_palette['grey']};
            border-radius: 5px;
            """
        )
        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(5, 5, 5, 5)
        self.layout.addWidget(outer_frame)

        # Header layout for title and legend
        header_title = QLabel("Jump Data", self)
        header_title.setAlignment(Qt.AlignCenter)
        header_title.setStyleSheet(
            f"""
            font-size: 28px;
            font-family: 'Roboto';
            margin-right: 30px;
            color: {self.color_palette['plot_fg']};
            """
        )

        # Header layout for alignment
        header_layout = QHBoxLayout()
        outer_layout.addLayout(header_layout)
        header_layout.addWidget(header_title, alignment=Qt.AlignCenter)

        # Create a legend layout to match live data
        legend_layout = QHBoxLayout()
        self.add_legend_icon(legend_layout, "X", self.color_palette["plot_lines_x"])
        self.add_legend_icon(legend_layout, "Y", self.color_palette["plot_lines_y"])
        self.add_legend_icon(legend_layout, "Z", self.color_palette["plot_lines_z"])
        legend_layout.setSpacing(10)  # Match live data legend spacing
        legend_layout.setContentsMargins(0, 0, 0, 0)  # Match live data padding

        # Add legend to the header layout
        header_layout.addLayout(legend_layout)
        header_layout.setAlignment(Qt.AlignCenter)

        # Plot container layout
        plots_container = QFrame(self)
        plots_layout = QGridLayout(plots_container)
        plots_layout.setContentsMargins(5, 5, 5, 5)
        plots_layout.setHorizontalSpacing(10)
        plots_layout.setVerticalSpacing(10)
        outer_layout.addWidget(plots_container)

        # Create plots with identical titles and formatting to live data
        for idx, (device_key, device_name) in enumerate(self.device_info.items()):
            accel_plot = self.create_plot(
                f"{device_name} Accelerometer", -10, 10, "Acceleration (m/s²)"
            )
            plots_layout.addWidget(accel_plot, idx, 0)
            gyro_plot = self.create_plot(
                f"{device_name} Gyroscope", -1000, 1000, "Angular Velocity (°/s)"
            )
            plots_layout.addWidget(gyro_plot, idx, 1)

            # Initialize plots and curves
            self.plots[device_key] = {"accel": accel_plot, "gyro": gyro_plot}
            self.curves[f"{device_key}_accel"] = {
                "x": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2)
                ),
                "y": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2)
                ),
                "z": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2)
                ),
            }
            self.curves[f"{device_key}_gyro"] = {
                "x": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2)
                ),
                "y": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2)
                ),
                "z": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2)
                ),
            }

            # Initialize the vertical lines for this device's plots
            self.vertical_lines[f"{device_key}_accel"] = []
            self.vertical_lines[f"{device_key}_gyro"] = []

    def create_plot(self, title, y_min, y_max, unit):
        plot = pg.PlotWidget(title=title)
        plot.setYRange(y_min, y_max)
        plot.setXRange(0, 2)  # Display the last 2 seconds of data
        plot.setMouseEnabled(False, False)  # Disable zooming and panning
        plot.getAxis("left").setLabel(unit)  # Y-axis label
        plot.getAxis("bottom").setLabel("Time (s)")  # X-axis label
        plot.getPlotItem().getAxis("left").setStyle(
            tickFont=pg.QtGui.QFont("Roboto", 10)
        )
        plot.getPlotItem().getAxis("bottom").setStyle(
            tickFont=pg.QtGui.QFont("Roboto", 10)
        )
        return plot

    def add_legend_icon(self, layout, label, color):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color))
        icon = QLabel()
        icon.setPixmap(pixmap)
        layout.addWidget(icon, alignment=Qt.AlignCenter)

        text = QLabel(label)
        text.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 16px; font-family: 'Roboto';"
        )
        layout.addWidget(text, alignment=Qt.AlignCenter)

    def update_jump_plot(self, jump_idx):
        if not (0 <= jump_idx < len(self.jumps)):
            return

        jump = self.jumps[jump_idx]

        # Iterate over the devices and sensor types
        for device_key, device_name in self.device_info.items():
            for sensor_type in ["accel", "gyro"]:
                plot_key = f"{device_key}_{sensor_type}"
                sensor_data = getattr(
                    jump, f"{device_name.lower().replace(' ', '_')}_{sensor_type}", None
                )

                if (
                    sensor_data is not None and sensor_data.size > 0
                ):  # Ensure data is available
                    # Retrieve the plot and curves
                    plot = self.plots[device_key][sensor_type]
                    curves = self.curves[plot_key]

                    # Subtract detected_time from timestamps
                    adjusted_time = sensor_data[:, 0] - (jump.detected_time - 0.5)

                    # Plot the adjusted data
                    curves["x"].setData(adjusted_time, sensor_data[:, 1])
                    curves["y"].setData(adjusted_time, sensor_data[:, 2])
                    curves["z"].setData(adjusted_time, sensor_data[:, 3])

                    # Keep X-axis fixed to 0-2 seconds
                    plot.setXRange(0, 2)
                else:
                    print(f"No data available for {plot_key}")

        # Update vertical lines for the current jump
        self.update_vertical_lines(jump.partition)

    def change_jump(self, direction):
        self.curr_jump_idx = max(
            0, min(len(self.jumps) - 1, self.curr_jump_idx + direction)
        )
        self.update_jump_plot(self.curr_jump_idx)

    def update_vertical_lines(self, partition):
        """Update vertical lines for takeoff, peak, and landing indices."""
        takeoff_idx, peak_idx, landing_idx = partition
        line_colors = {"takeoff": "yellow", "peak": "orange", "landing": "black"}

        for device_key, device_name in self.device_info.items():
            for sensor_type in ["accel", "gyro"]:
                plot_key = f"{device_key}_{sensor_type}"

                # Check if vertical lines were initialized for this plot
                if plot_key not in self.vertical_lines:
                    print(f"Warning: Vertical lines not initialized for {plot_key}")
                    continue

                # Clear existing lines
                for line in self.vertical_lines[plot_key]:
                    self.plots[device_key][sensor_type].removeItem(line)
                self.vertical_lines[plot_key] = []  # Reset lines

                # Add new lines
                for idx, color in zip(
                    [takeoff_idx, peak_idx, landing_idx], line_colors.values()
                ):
                    vline = pg.InfiniteLine(
                        pos=idx, angle=90, pen=pg.mkPen(color=color, width=2)
                    )
                    self.plots[device_key][sensor_type].addItem(vline)
                    self.vertical_lines[plot_key].append(vline)
