import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QGridLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget
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
        # Set light mode for pyqtgraph globally
        pg.setConfigOption("background", self.color_palette["plot_bg"])
        pg.setConfigOption("foreground", self.color_palette["plot_fg"])

        # Main layout for the widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Outer frame for rounded background
        outer_frame = QFrame(self)
        outer_frame.setStyleSheet(
            f"""
            background-color: {self.color_palette['grey']};
            border-radius: 10px;
            """
        )
        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.addWidget(outer_frame)

        # Title for live plots
        plot_title = QLabel("Live Data", self)
        plot_title.setAlignment(Qt.AlignCenter)
        plot_title.setStyleSheet(
            """
            font-size: 24px;
            font-family: 'Roboto', sans-serif;
            margin: 10px;
            """
        )
        outer_layout.addWidget(plot_title)

        # Styled container for plots
        plots_container = QFrame(self)
        plots_container.setStyleSheet(
            """
            background-color: #f4f4f4;
            """
        )
        plots_layout = QGridLayout(plots_container)
        plots_layout.setContentsMargins(10, 10, 10, 10)
        plots_layout.setHorizontalSpacing(20)
        plots_layout.setVerticalSpacing(20)
        outer_layout.addWidget(plots_container)

        # Create grid layout for plots
        for idx, (address, name) in enumerate(self.device_info.items()):
            accel_plot = self.create_plot_widget(f"{name} Accelerometer", -10, 10)
            plots_layout.addWidget(accel_plot, idx, 0)

            gyro_plot = self.create_plot_widget(f"{name} Gyroscope", -1000, 1000)
            plots_layout.addWidget(gyro_plot, idx, 1)

            # Store plots for updates
            self.plots[address] = {
                "accel_x": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2),
                    name="Accel X",
                ),
                "accel_y": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2),
                    name="Accel Y",
                ),
                "accel_z": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2),
                    name="Accel Z",
                ),
                "gyro_x": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2),
                    name="Gyro X",
                ),
                "gyro_y": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2),
                    name="Gyro Y",
                ),
                "gyro_z": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2),
                    name="Gyro Z",
                ),
            }

    def create_plot_widget(self, title, y_min, y_max):
        """Creates a single plot widget with the specified title and Y-axis range."""
        plot_item = pg.PlotWidget(title=title)
        plot_item.setYRange(y_min, y_max)
        plot_item.setXRange(-2, 0)  # Last 2 seconds
        plot_item.addLegend(offset=(10, 10))
        plot_item.getAxis("left").setLabel("Value")
        plot_item.getAxis("bottom").setLabel("Time (s)")

        return plot_item

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)

    def update_plots(self):
        """Fetch the latest 2 seconds of data and update plots."""
        current_time = time()
        for address, plot_data in self.plots.items():
            if address in self.data:
                accel_data = self.data[address]["accel"]
                gyro_data = self.data[address]["gyro"]

                # Filter data for the last 2 seconds
                recent_accel = accel_data[accel_data[:, 0] >= current_time - 2]
                recent_gyro = gyro_data[gyro_data[:, 0] >= current_time - 2]

                # Generate timestamps relative to the current time
                accel_time = recent_accel[:, 0] - current_time
                gyro_time = recent_gyro[:, 0] - current_time

                # Update accelerometer plots
                if recent_accel.size > 0:
                    plot_data["accel_x"].setData(accel_time, recent_accel[:, 1])
                    plot_data["accel_y"].setData(accel_time, recent_accel[:, 2])
                    plot_data["accel_z"].setData(accel_time, recent_accel[:, 3])

                # Update gyroscope plots
                if recent_gyro.size > 0:
                    plot_data["gyro_x"].setData(gyro_time, recent_gyro[:, 1])
                    plot_data["gyro_y"].setData(gyro_time, recent_gyro[:, 2])
                    plot_data["gyro_z"].setData(gyro_time, recent_gyro[:, 3])
