import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QFrame,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QFont, QColor, QPixmap
from time import time


class GUILivePlots(QWidget):
    def __init__(self, color_palette, device_info, data):
        super().__init__()
        self.color_palette = color_palette
        self.device_info = device_info
        self.data = data
        self.plots = {}
        self.init_live_plots()
        self.setup_timer()

    def init_live_plots(self):
        pg.setConfigOption("background", self.color_palette["plot_bg"])
        pg.setConfigOption("foreground", self.color_palette["plot_fg"])

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        outer_frame = QFrame(self)
        outer_frame.setStyleSheet(
            "background-color: {}; border-radius: 10px;".format(
                self.color_palette["grey"]
            )
        )
        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(outer_frame)

        # Header layout for title and legend
        plot_title = QLabel("Live Data", self)
        plot_title.setAlignment(Qt.AlignCenter)
        plot_title.setStyleSheet(
            "font-size: 28px; font-family: 'Roboto'; margin-right: 30px;"
        )

        # Container for title and legend
        header_layout = QHBoxLayout()
        outer_layout.addLayout(header_layout)
        header_layout.addWidget(plot_title, alignment=Qt.AlignCenter)

        # Create a sub-layout for legends
        legend_layout = QHBoxLayout()
        self.add_legend_icon(legend_layout, "X", self.color_palette["plot_lines_x"])
        self.add_legend_icon(legend_layout, "Y", self.color_palette["plot_lines_y"])
        self.add_legend_icon(legend_layout, "Z", self.color_palette["plot_lines_z"])
        legend_layout.setSpacing(10)  # Adjust space between icons
        legend_layout.setContentsMargins(0, 0, 0, 0)  # Remove any extra padding

        # Add the legend layout to the header
        header_layout.addLayout(legend_layout)
        header_layout.setAlignment(Qt.AlignCenter)  # Center the header content

        # Continue
        plots_container = QFrame(self)
        plots_layout = QGridLayout(plots_container)
        plots_layout.setContentsMargins(5, 5, 5, 5)
        plots_layout.setHorizontalSpacing(10)
        plots_layout.setVerticalSpacing(10)
        outer_layout.addWidget(plots_container)

        for idx, (address, name) in enumerate(self.device_info.items()):
            accel_plot = self.create_plot_widget(
                f"{name} Accelerometer", -10, 10, "Acceleration (m/s²)"
            )
            plots_layout.addWidget(accel_plot, idx, 0)
            gyro_plot = self.create_plot_widget(
                f"{name} Gyroscope", -1000, 1000, "Angular Velocity (°/s)"
            )
            plots_layout.addWidget(gyro_plot, idx, 1)

            self.plots[address] = {"accel": accel_plot, "gyro": gyro_plot}

    def add_legend_label(self, layout, text, color):
        label = QLabel(f"{text}:")
        label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 16px; font-family: 'Roboto';"
        )
        layout.addWidget(label)

    def create_plot_widget(self, title, y_min, y_max, unit):
        plot_item = pg.PlotWidget(title=title)
        plot_item.setYRange(y_min, y_max)
        plot_item.setXRange(-2, 0)  # Display the last 2 seconds of data
        plot_item.getAxis("left").setLabel(unit)  # Set label for y-axis
        plot_item.getAxis("bottom").setLabel("Time (s)")  # Set label for x-axis
        plot_item.getPlotItem().getAxis("left").setStyle(
            tickFont=pg.QtGui.QFont("Roboto", 10)
        )
        plot_item.getPlotItem().getAxis("bottom").setStyle(
            tickFont=pg.QtGui.QFont("Roboto", 10)
        )
        return plot_item

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)  # Update the plots every 50 milliseconds

    def update_plots(self):
        current_time = time()
        for address, plots in self.plots.items():
            if address in self.data:
                for sensor_type in ["accel", "gyro"]:
                    data = self.data[address][sensor_type]
                    recent_data = data[data[:, 0] >= current_time - 2]
                    time_data = recent_data[:, 0] - current_time
                    if recent_data.size > 0:
                        frequency = len(recent_data) / 2  # Hz calculation
                        plots[sensor_type].clear()
                        title_suffix = (
                            f" ({frequency:.0f} Hz)"  # Frequency to be displayed
                        )
                        sensor_name = "Accel" if sensor_type == "accel" else "Gyro"
                        for i in range(1, 4):  # X, Y, Z data columns
                            plots[sensor_type].plot(
                                time_data,
                                recent_data[:, i],
                                pen=None,
                                symbol="o",
                                symbolSize=6,
                                symbolBrush=self.color_palette[
                                    f"plot_lines_{chr(119+i)}"
                                ],
                            )
                        # Update the plot title with the new frequency
                        plots[sensor_type].setTitle(
                            f"{self.device_info[address]} {sensor_name} {title_suffix}"
                        )

    def add_legend_icon(self, layout, label, color):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color))
        icon = QLabel()
        icon.setPixmap(pixmap)
        icon.setToolTip(f"{label} axis")  # Optional: tooltip on hover
        layout.addWidget(icon, alignment=Qt.AlignCenter)

        text = QLabel(label)
        text.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 16px; font-family: 'Roboto';"
        )
        layout.addWidget(text, alignment=Qt.AlignCenter)
