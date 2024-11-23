import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QGridLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class GUILivePlots(QWidget):
    def __init__(self, device_info, color_palette):
        super().__init__()
        self.device_info = device_info
        self.color_palette = color_palette
        self.plots = {}

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
        outer_layout.setContentsMargins(20, 20, 20, 20)  # Space inside the frame
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
        plots_layout.setContentsMargins(10, 10, 10, 10)  # Margins for plots container
        plots_layout.setHorizontalSpacing(20)  # Horizontal spacing between plots
        plots_layout.setVerticalSpacing(20)  # Vertical spacing between plots
        outer_layout.addWidget(plots_container)

        # Create grid layout for plots
        for idx, (address, name) in enumerate(self.device_info.items()):
            accel_plot = self.create_plot_widget(
                f"{name} Accelerometer", -10, 10, self.color_palette
            )
            plots_layout.addWidget(accel_plot, idx, 0)

            gyro_plot = self.create_plot_widget(
                f"{name} Gyroscope", -1000, 1000, self.color_palette
            )
            plots_layout.addWidget(gyro_plot, idx, 1)

            # Store plots for updates
            self.plots[address] = {
                "accel_x": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2), name="X"
                ),
                "accel_y": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2), name="Y"
                ),
                "accel_z": accel_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2), name="Z"
                ),
                "gyro_x": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_x"], width=2), name="X"
                ),
                "gyro_y": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_y"], width=2), name="Y"
                ),
                "gyro_z": gyro_plot.plot(
                    pen=pg.mkPen(self.color_palette["plot_lines_z"], width=2), name="Z"
                ),
            }

    def create_plot_widget(self, title, y_min, y_max, color_palette):
        """Creates a single plot widget with the specified title and Y-axis range."""
        plot_item = pg.PlotWidget(title=title)
        plot_item.setYRange(y_min, y_max)
        plot_item.setXRange(0, 200)  # Set X-axis range immediately
        plot_item.addLegend(offset=(10, 10))
        plot_item.getAxis("left").setLabel("Value")
        plot_item.getAxis("bottom").setLabel("Time")

        # Add extra margins inside the plot
        plot_item.getPlotItem().layout.setContentsMargins(
            10, 10, 10, 10
        )  # Margins inside plot
        return plot_item

    def update_plot(self, address, accel_data, gyro_data):
        """Updates the accelerometer and gyroscope plots with new data."""
        if address in self.plots:
            plots = self.plots[address]
            if accel_data:
                plots["accel_x"].setData([d[0] for d in accel_data])
                plots["accel_y"].setData([d[1] for d in accel_data])
                plots["accel_z"].setData([d[2] for d in accel_data])
            if gyro_data:
                plots["gyro_x"].setData([d[0] for d in gyro_data])
                plots["gyro_y"].setData([d[1] for d in gyro_data])
                plots["gyro_z"].setData([d[2] for d in gyro_data])
