import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QButtonGroup,
    QRadioButton,
    QComboBox,
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
        self.accel_type = "accel"
        self.gyro_type = "gyro"

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
            QComboBox {{
                padding-left: 15px;  /* Increase left padding */
                color: {self.color_palette['black']};
                background-color: {self.color_palette['yellow']};
                border: 1px solid {self.color_palette['dark_grey']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left-width: 1px;
                border-left-color: {self.color_palette['dark_grey']};
                border-left-style: solid; /* just a single line on the right */
                border-top-right-radius: 3px; /* same radius as the QComboBox */
                border-bottom-right-radius: 3px;
            }}
            QComboBox::down-arrow {{
                width: 10px;
                height: 10px;
                color: {self.color_palette['dark_grey']};
                text-align: center;
                content: "▼"; /* Unicode character for down arrow */
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
        header_title = QLabel("Jump Plots", self)
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

        # Create dropdowns for plot selection
        accel_dropdown = QComboBox(self)
        accel_dropdown.addItems(["Accel", "Vel", "Disp"])
        accel_dropdown.currentTextChanged.connect(self.set_accel_data_type)
        gyro_dropdown = QComboBox(self)
        gyro_dropdown.addItems(["Ang Vel", "Ang Disp"])
        gyro_dropdown.currentTextChanged.connect(self.set_gyro_data_type)

        # Add dropdowns to the header layout
        # header_layout.addWidget(QLabel(""))
        header_layout.addWidget(accel_dropdown)
        # header_layout.addWidget(QLabel(""))
        header_layout.addWidget(gyro_dropdown)

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
                f"{device_name} Accelerometer", -100, 100, "Acceleration (m/s²)"
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

    def set_accel_data_type(self, data_type):
        print(f"Selected accel data type: {data_type}")  # Debug line
        mapping = {"Accel": "accel", "Vel": "vel", "Disp": "disp"}
        self.accel_type = mapping.get(
            data_type, "accel"
        )  # Fixed typo: self.data_type -> self.accel_type
        self.update_jump_plot(self.curr_jump_idx)

    def set_gyro_data_type(self, data_type):
        print(f"Selected gyro data type: {data_type}")  # Debug line
        mapping = {"Ang Vel": "gyro", "Ang Disp": "ang_disp"}
        self.gyro_type = mapping.get(data_type, "gyro")
        self.update_jump_plot(self.curr_jump_idx)

    def create_plot(self, title, y_min, y_max, unit):
        plot = pg.PlotWidget(title=title)
        plot.setYRange(y_min, y_max)
        plot.setXRange(0, 2)  # Display the last 2 seconds of data initially
        plot.setMouseEnabled(True, True)  # Enable zooming and panning
        plot.getAxis("left").setLabel(unit)  # Y-axis label
        plot.getAxis("bottom").setLabel("Time (s)")  # X-axis label
        plot.getPlotItem().getAxis("left").setStyle(
            tickFont=pg.QtGui.QFont("Roboto", 10)
        )
        plot.getPlotItem().getAxis("bottom").setStyle(
            tickFont=pg.QtGui.QFont("Roboto", 10)
        )
        return plot

    def reset_zoom(self, plot):
        plot.enableAutoRange()

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
        self.curr_jump_idx = jump_idx
        if not (0 <= jump_idx < len(self.jumps)):
            return
        jump = self.jumps[jump_idx]
        self.update_sensor_plots(jump, "accel", self.accel_type)
        self.update_sensor_plots(jump, "gyro", self.gyro_type)
        self.update_vertical_lines(jump.partition)

    def update_sensor_plots(self, jump, sensor_type, data_type):
        """Update plots for a specific sensor type (accel or gyro)."""
        # Define human-readable titles and axis ranges for data types
        title_mapping = {
            "accel": "Accel. (m/s²)",
            "vel": "Vel. (m/s)",
            "disp": "Disp. (m)",
            "gyro": "Ang. Vel. (°/s)",
            "ang_disp": "Ang. Disp. (°)",
        }
        axis_ranges = {
            "accel": (-50, 50),  # Acceleration in m/s²
            "vel": (-5, 5),  # Velocity in m/s
            "disp": (-3, 3),  # Displacement in meters
            "gyro": (-1000, 1000),  # Angular velocity in °/s
            "ang_disp": (-180, 180),  # Angular displacement in degrees
        }
        axis_units = {
            "accel": "Acceleration (m/s²)",
            "vel": "Velocity (m/s)",
            "disp": "Displacement (m)",
            "gyro": "Angular Velocity (°/s)",
            "ang_disp": "Angular Displacement (°)",
        }

        for device_key, device_name in self.device_info.items():
            plot_key = f"{device_key}_{sensor_type}"
            sensor_data = getattr(
                jump, f"{device_name.lower().replace(' ', '_')}_{data_type}", None
            )

            if sensor_data is not None and sensor_data.size > 0:
                plot = self.plots[device_key][sensor_type]
                curves = self.curves[plot_key]
                adjusted_time = sensor_data[:, 0] - (jump.detected_time - 0.5)
                curves["x"].setData(adjusted_time, sensor_data[:, 1])
                curves["y"].setData(adjusted_time, sensor_data[:, 2])
                curves["z"].setData(adjusted_time, sensor_data[:, 3])

                # Update axis ranges
                y_min, y_max = axis_ranges.get(data_type, (-100, 100))
                plot.setYRange(y_min, y_max)

                # Update the plot title
                plot_title = f"{device_name} {title_mapping.get(data_type, '')}"
                plot.setTitle(plot_title)

                # Update axis labels
                plot.getAxis("left").setLabel(axis_units.get(data_type, ""))
                plot.getAxis("bottom").setLabel("Time (s)")

                plot.setXRange(0, 2)
            else:
                print(f"No data available for {plot_key}")

    def update_vertical_lines(self, partition):
        """Update dashed vertical lines for takeoff, peak, and landing times."""
        takeoff_time, peak_time, landing_time = partition
        time_adjustment = self.jumps[self.curr_jump_idx].detected_time - 0.5

        # Use colors from the palette
        line_colors = {
            "takeoff": self.color_palette["line_takeoff"],
            "peak": self.color_palette["line_peak"],
            "landing": self.color_palette["line_landing"],
        }

        for device_key, device_name in self.device_info.items():
            for sensor_type in ["accel", "gyro"]:
                plot_key = f"{device_key}_{sensor_type}"

                # Ensure vertical lines array is initialized
                if plot_key not in self.vertical_lines:
                    print(f"Warning: Vertical lines not initialized for {plot_key}")
                    continue

                # Clear existing lines
                for line in self.vertical_lines[plot_key]:
                    self.plots[device_key][sensor_type].removeItem(line)
                self.vertical_lines[plot_key] = []  # Reset lines

                # Adjust times for plotting
                adjusted_times = [
                    takeoff_time - time_adjustment,
                    peak_time - time_adjustment,
                    landing_time - time_adjustment,
                ]

                # Add dashed vertical lines at the adjusted times
                for time, (key, color) in zip(adjusted_times, line_colors.items()):
                    if 0 <= time <= 2:  # Ensure the line is within the visible range
                        vline = pg.InfiniteLine(
                            pos=time,
                            angle=90,
                            pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
                        )
                        self.plots[device_key][sensor_type].addItem(vline)
                        self.vertical_lines[plot_key].append(vline)
