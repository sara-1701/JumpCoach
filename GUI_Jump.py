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
                padding: 10px;
                border-radius: 10px;
            }}
            """
        )
        self.layout = QVBoxLayout(self)

        grid_layout = QGridLayout()
        self.layout.addLayout(grid_layout)

        # Create a header with a legend that is centered above the plots
        header = self.create_header()
        grid_layout.addWidget(header, 0, 0, 1, 2)  # Span two columns

        row = 1
        for device_key in ["lower_back", "wrist", "thigh"]:
            for sensor_type in ["acc", "gyro"]:
                plot = self.create_plot(
                    f"{device_key.capitalize()} {sensor_type.capitalize()} Data",
                    -10 if sensor_type == "acc" else -1000,
                    10 if sensor_type == "acc" else 1000,
                    (
                        f"Acceleration (m/s²)"
                        if sensor_type == "acc"
                        else "Angular Velocity (°/s)"
                    ),
                )
                grid_layout.addWidget(plot, row, 0 if sensor_type == "acc" else 1)
                self.plots[f"{device_key}_{sensor_type}"] = plot
                self.curves[f"{device_key}_{sensor_type}"] = {
                    "x": plot.plot(
                        pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2)
                    ),
                    "y": plot.plot(
                        pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2)
                    ),
                    "z": plot.plot(
                        pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2)
                    ),
                }
            row += 1

    def create_plot(self, title, y_min, y_max, unit):
        plot = pg.PlotWidget(title=title)
        plot.setYRange(y_min, y_max)
        plot.setXRange(0, 2)  # Display 2 seconds of data
        plot.getAxis("left").setLabel(unit)
        plot.getAxis("bottom").setLabel("Time (s)")
        plot.setFixedWidth(400)  # Match the width of the live plots
        return plot

    def create_header(self):
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignCenter)

        # Add the legend similar to live plots
        self.add_legend_icon(header_layout, "X", self.color_palette["plot_lines_x"])
        self.add_legend_icon(header_layout, "Y", self.color_palette["plot_lines_y"])
        self.add_legend_icon(header_layout, "Z", self.color_palette["plot_lines_z"])

        return header

    def add_legend_icon(self, layout, label, color):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color))
        icon = QLabel()
        icon.setPixmap(pixmap)
        icon.setToolTip(f"{label} axis")  # Tooltip on hover
        layout.addWidget(icon, alignment=Qt.AlignCenter)

        text = QLabel(label)
        text.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 16px; font-family: 'Roboto';"
        )
        layout.addWidget(text, alignment=Qt.AlignCenter)

    def update_jump_plot(self, jump_idx):
        if not (0 <= jump_idx < len(self.jumps)):
            return
        print(f"Updating plot for jump at index {jump_idx}")
        jump = self.jumps[jump_idx]
        # Assume timestamps are in the first column and channels start from the second column
        for device_key in ["lower_back", "wrist", "thigh"]:
            for sensor_type in ["acc", "gyro"]:
                key = f"{device_key}_{sensor_type}"
                curves = self.curves[key]
                sensor_data = getattr(jump, key)
                if sensor_data.size > 0:  # Ensure there is data to plot
                    # Set the time range to cover the jump duration based on the first and last timestamp
                    start_time = sensor_data[0, 0]
                    end_time = sensor_data[-1, 0]
                    self.plots[key].setXRange(start_time, end_time)
                    curves["x"].setData(sensor_data[:, 0], sensor_data[:, 1])
                    curves["y"].setData(sensor_data[:, 0], sensor_data[:, 2])
                    curves["z"].setData(sensor_data[:, 0], sensor_data[:, 3])
                else:
                    print(f"No data available for {key}")

        self.update_vertical_lines(jump.partition)

    def change_jump(self, direction):
        self.curr_jump_idx = max(
            0, min(len(self.jumps) - 1, self.curr_jump_idx + direction)
        )
        self.update_jump_plot(self.curr_jump_idx)

    def update_vertical_lines(self, partition):
        for plot_key, plot in self.plots.items():
            if plot_key in self.vertical_lines:
                for line in self.vertical_lines[plot_key]:
                    plot.removeItem(line)
                self.vertical_lines[plot_key] = []
                for idx, color_key in zip(partition, ["takeoff", "peak", "landing"]):
                    color = self.color_palette[f"line_{color_key}"]
                    vline = pg.InfiniteLine(
                        pos=idx, angle=90, pen=pg.mkPen(color=color, width=2)
                    )
                    plot.addItem(vline)
                    self.vertical_lines[plot_key].append(vline)
