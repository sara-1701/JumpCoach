from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
import pyqtgraph as pg


class GUIJump(QWidget):
    def __init__(self, color_palette, jumps, metric_widget):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.plots = {}  # Store plots for each sensor
        self.curves = {}  # Store curves for each sensor
        self.vertical_lines = {}  # Store vertical lines for each plot
        self.curr_jump_idx = 0
        self.metrics_widget = metric_widget

        self.setStyleSheet(
            f"""
            background-color: {color_palette['block_bg']};
            font-size: 18px;
            font-family: 'Roboto', sans-serif;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            """
        )

        # Main layout
        self.layout = QVBoxLayout(self)

        # Grid layout for plots
        self.grid_layout = QGridLayout()  # Use grid layout for device plots
        self.layout.addLayout(self.grid_layout)

        # Create plots for the six relevant attributes
        self.create_device_plots("Lower Back", "lower_back_acc", "lower_back_gyro", 0)
        self.create_device_plots("Wrist", "wrist_acc", "wrist_gyro", 1)
        self.create_device_plots("Thigh", "thigh_acc", "thigh_gyro", 2)

        # Navigation buttons
        self.add_navigation_buttons()

    def create_device_plots(self, device_name, accel_attr, gyro_attr, row):
        """Helper to create plots for a device."""
        # Create accelerometer plot
        accel_plot = self.create_plot(f"{device_name} Accelerometer", -10, 10)
        self.grid_layout.addWidget(accel_plot, row * 2 + 1, 0)
        self.plots[accel_attr] = accel_plot
        self.curves[accel_attr] = {
            "x": accel_plot.plot(pen=pg.mkPen(color="r", width=2)),
            "y": accel_plot.plot(pen=pg.mkPen(color="g", width=2)),
            "z": accel_plot.plot(pen=pg.mkPen(color="b", width=2)),
        }

        # Create gyroscope plot
        gyro_plot = self.create_plot(f"{device_name} Gyroscope", -2000, 2000)
        self.grid_layout.addWidget(gyro_plot, row * 2 + 1, 1)
        self.plots[gyro_attr] = gyro_plot
        self.curves[gyro_attr] = {
            "x": gyro_plot.plot(pen=pg.mkPen(color="r", width=2)),
            "y": gyro_plot.plot(pen=pg.mkPen(color="g", width=2)),
            "z": gyro_plot.plot(pen=pg.mkPen(color="b", width=2)),
        }

        # Initialize vertical lines for each plot
        self.vertical_lines[accel_attr] = []
        self.vertical_lines[gyro_attr] = []

    def create_plot(self, title, y_min, y_max):
        plot = pg.PlotWidget(title=title)
        plot.setYRange(y_min, y_max)
        plot.setXRange(0, 200)  # Show 2 seconds of data (100 Hz sampling)
        plot.getAxis("left").setLabel("Value")
        plot.getAxis("bottom").setLabel("Time (samples)")
        return plot

    def add_navigation_buttons(self):
        """Add navigation buttons for moving between jumps."""
        button_layout = QHBoxLayout()

        # Previous button
        self.prev_button = QPushButton("Previous Jump")
        self.prev_button.setStyleSheet(
            """
            font-size: 16px;
            font-family: 'Roboto', sans-serif;
            padding: 10px;
            background-color: #4285F4;
            color: white;
            border-radius: 5px;
            """
        )
        self.prev_button.clicked.connect(self.prev_jump)
        button_layout.addWidget(self.prev_button)

        # Next button
        self.next_button = QPushButton("Next Jump")
        self.next_button.setStyleSheet(
            """
            font-size: 16px;
            font-family: 'Roboto', sans-serif;
            padding: 10px;
            background-color: #34A853;
            color: white;
            border-radius: 5px;
            """
        )
        self.next_button.clicked.connect(self.next_jump)
        button_layout.addWidget(self.next_button)

        # Add button layout to the main layout
        self.layout.addLayout(button_layout)

    def prev_jump(self):
        """Go to the previous jump."""
        if self.curr_jump_idx > 0:
            self.curr_jump_idx -= 1
            self.update_jump_plot(self.curr_jump_idx)
            self.metrics_widget.update_metrics_table(self.curr_jump_idx)

    def next_jump(self):
        """Go to the next jump."""
        if self.curr_jump_idx < len(self.jumps) - 1:
            self.curr_jump_idx += 1
            self.update_jump_plot(self.curr_jump_idx)
            self.metrics_widget.update_metrics_table(self.curr_jump_idx)

    def update_jump_plot(self, jump_idx):
        """Update plots with the data from the specified jump index."""
        self.metrics_widget.update_metrics_table(jump_idx)
        self.curr_jump_idx = jump_idx
        jump = self.jumps[jump_idx]

        # Update accelerometer and gyroscope data for each device
        for attr in ["lower_back_acc", "wrist_acc", "thigh_acc"]:
            accel_data = getattr(jump, attr, [])
            if not accel_data or not all(len(point) == 3 for point in accel_data):
                print(f"Skipping {attr} due to invalid data.")
                continue
            accel_curves = self.curves[attr]
            accel_curves["x"].setData([point[0] for point in accel_data])
            accel_curves["y"].setData([point[1] for point in accel_data])
            accel_curves["z"].setData([point[2] for point in accel_data])

        for attr in ["lower_back_gyro", "wrist_gyro", "thigh_gyro"]:
            gyro_data = getattr(jump, attr, [])
            if not gyro_data or not all(len(point) == 3 for point in gyro_data):
                print(f"Skipping {attr} due to invalid data.")
                continue
            gyro_curves = self.curves[attr]
            gyro_curves["x"].setData([point[0] for point in gyro_data])
            gyro_curves["y"].setData([point[1] for point in gyro_data])
            gyro_curves["z"].setData([point[2] for point in gyro_data])

        # Draw vertical lines for takeoff, peak, and landing indices
        self.update_vertical_lines(jump.partition)

    def update_vertical_lines(self, partition):
        """Update vertical lines for takeoff, peak, and landing indices."""
        takeoff_idx, peak_idx, landing_idx = partition

        # Define line colors for each event
        line_colors = {
            "takeoff": "yellow",
            "peak": "orange",
            "landing": "black",
        }

        # Iterate over all plots and add vertical lines
        for plot_key, plot in self.plots.items():
            # Clear existing lines
            for line in self.vertical_lines[plot_key]:
                plot.removeItem(line)
            self.vertical_lines[plot_key] = []  # Reset lines

            # Add new lines
            for idx, color in zip(
                [takeoff_idx, peak_idx, landing_idx], line_colors.values()
            ):
                vline = pg.InfiniteLine(
                    pos=idx, angle=90, pen=pg.mkPen(color=color, width=2)
                )
                plot.addItem(vline)
                self.vertical_lines[plot_key].append(vline)
