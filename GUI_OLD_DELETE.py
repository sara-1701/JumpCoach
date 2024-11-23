import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer

# Set light mode globally
pg.setConfigOption("background", "w")  # Set plot background to white
pg.setConfigOption("foreground", "k")  # Set text and axes to black

COLORS = {
    "app_bg": "#e0e0e0",  # Light grey for app background
    "block_bg": "#f4f4f4",  # Light grey for plot blocks
    "connecting": "#cccccc",
    "connected": "#90ee90",
    "failed": "#ffcccb",
    "plot_lines_x": "#FF5722",  # Red for X-axis
    "plot_lines_y": "#4CAF50",  # Green for Y-axis
    "plot_lines_z": "#2196F3",  # Blue for Z-axis
}


class MainApp(QMainWindow):
    def __init__(self, imu_info):
        super().__init__()
        self.imu_info = imu_info
        self.setWindowTitle("JumpCoach - Sara and Michael")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()  # Always open in maximized mode
        self.setStyleSheet(f"background-color: {COLORS['app_bg']};")  # App background

        self.status_boxes = {}
        self.plots = {}
        self.main_dashboard_shown = False
        self.connected_count = 0

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        # Centered IMU connection status layout
        self.add_centered_imu_status_layout()

        # Add connection title below the spacer and above the IMU boxes
        self.connection_title = QLabel("Let's first connect to the IMUs", self)
        self.connection_title.setAlignment(Qt.AlignCenter)
        self.connection_title.setStyleSheet(
            """
            font-size: 24px;
            font-family: 'Roboto', sans-serif;
            margin-top: 20px;
            """
        )
        self.main_layout.insertWidget(1, self.connection_title)

        self.setCentralWidget(self.main_widget)

    def add_centered_imu_status_layout(self):
        """Centers the IMU connection boxes in the middle of the screen."""
        # Add vertical spacers above and below the IMU connection boxes
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Create horizontal layout for IMU connection boxes
        self.status_layout = QHBoxLayout()
        self.status_layout.setAlignment(Qt.AlignHCenter)
        for address, name in self.imu_info.items():
            self.add_status_box(address, name)
        self.main_layout.addLayout(self.status_layout)

        # Add vertical spacer below the boxes
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

    def add_status_box(self, address, name):
        label = QLabel(f"{name}\n{address}\nConnecting...", self)
        label.setStyleSheet(
            f"""
            background-color: {COLORS['connecting']};
            padding: 20px;
            font-size: 20px;
            font-family: 'Roboto', sans-serif;
            border-radius: 10px;
            border: 1px solid #ddd;
        """
        )
        label.setFixedSize(250, 120)  # Adjusted size for larger font
        label.setAlignment(Qt.AlignCenter)
        self.status_boxes[address] = label
        self.status_layout.addWidget(label)

    def update_status(self, address, connected):
        label = self.status_boxes[address]
        if connected:
            label.setText(f"{self.imu_info[address]}\n{address}\nConnected")
            label.setStyleSheet(
                f"""
                background-color: {COLORS['connected']};
                padding: 20px;
                font-size: 20px;
                font-family: 'Roboto', sans-serif;
                border-radius: 10px;
                border: 1px solid #ddd;
            """
            )
            self.connected_count += 1
        else:
            label.setText(f"{self.imu_info[address]}\n{address}\nFailed")
            label.setStyleSheet(
                f"""
                background-color: {COLORS['failed']};
                padding: 20px;
                font-size: 20px;
                font-family: 'Roboto', sans-serif;
                border-radius: 10px;
                border: 1px solid #ddd;
            """
            )

        # If all IMUs are connected, delay and show the dashboard
        if self.connected_count == len(self.imu_info):
            QTimer.singleShot(1000, self.show_dashboard)  # 1-second delay

    def show_dashboard(self):
        """Show the main dashboard with plots and jump detection placeholder."""
        if self.main_dashboard_shown:
            return

        # Clear status layout and title
        self.connection_title.hide()
        for i in reversed(range(self.status_layout.count())):
            item = self.status_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
            elif item:
                self.status_layout.removeItem(item)

        # Create dashboard layout
        dashboard_layout = QHBoxLayout()

        # Create a styled background box for all plots
        plots_background_frame = QFrame()
        plots_background_frame.setStyleSheet(
            f"""
            background-color: {COLORS['block_bg']};
            border: 1px solid #ddd;
            border-radius: 10px;
            """
        )
        plots_background_frame_layout = QVBoxLayout(plots_background_frame)
        plots_background_frame_layout.setContentsMargins(10, 10, 10, 10)

        # Add title for plots
        plot_title = QLabel("Live IMU Data", self)
        plot_title.setAlignment(Qt.AlignCenter)
        plot_title.setStyleSheet(
            """
            font-size: 24px;
            font-family: 'Roboto', sans-serif;
            margin: 10px;
            border: 0px;
            border-radius: 0px;
            """
        )
        plots_background_frame_layout.addWidget(plot_title)

        # Add plots for all IMUs inside the styled box
        plot_grid = QGridLayout()
        for idx, (address, name) in enumerate(self.imu_info.items()):
            # Create accelerometer plot
            accel_plot = self.create_plot_widget(f"{name} Accelerometer", -10, 10)
            plot_grid.addWidget(accel_plot, idx, 0)

            # Create gyroscope plot
            gyro_plot = self.create_plot_widget(f"{name} Gyroscope", -1000, 1000)
            plot_grid.addWidget(gyro_plot, idx, 1)

            # Store plot references
            self.plots[address] = {
                "accel_x": accel_plot.plot(
                    pen=pg.mkPen(COLORS["plot_lines_x"], width=2), name="X"
                ),
                "accel_y": accel_plot.plot(
                    pen=pg.mkPen(COLORS["plot_lines_y"], width=2), name="Y"
                ),
                "accel_z": accel_plot.plot(
                    pen=pg.mkPen(COLORS["plot_lines_z"], width=2), name="Z"
                ),
                "gyro_x": gyro_plot.plot(
                    pen=pg.mkPen(COLORS["plot_lines_x"], width=2), name="X"
                ),
                "gyro_y": gyro_plot.plot(
                    pen=pg.mkPen(COLORS["plot_lines_y"], width=2), name="Y"
                ),
                "gyro_z": gyro_plot.plot(
                    pen=pg.mkPen(COLORS["plot_lines_z"], width=2), name="Z"
                ),
            }

        # Add the grid of plots to the styled box layout
        plots_background_frame_layout.addLayout(plot_grid)

        # Add the styled box to the dashboard
        dashboard_layout.addWidget(plots_background_frame, stretch=3)

        # Add the jump detection placeholder to the right
        jump_placeholder = QLabel("Waiting to Detect Jump", self)
        jump_placeholder.setAlignment(Qt.AlignCenter)
        jump_placeholder.setStyleSheet(
            f"""
            background-color: {COLORS['block_bg']};
            font-size: 24px;
            font-family: 'Roboto', sans-serif;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            """
        )
        dashboard_layout.addWidget(jump_placeholder, stretch=2)

        # Add the dashboard to the main layout
        self.main_layout.addLayout(dashboard_layout)
        self.main_dashboard_shown = True

    def create_plot_widget(self, title, y_min, y_max):
        plot_item = pg.PlotWidget(title=title)
        plot_item.setYRange(y_min, y_max)
        plot_item.addLegend(offset=(10, 10))
        plot_item.getAxis("left").setLabel("Value")
        plot_item.getAxis("bottom").setLabel("Time")
        plot_item.setStyleSheet(
            """
            border: 1px solid #ddd;
            """
        )
        return plot_item

    def update_plot(self, address, acc_data, gyro_data):
        if address in self.plots:
            plots = self.plots[address]
            if acc_data:
                plots["accel_x"].setData([d[0] for d in acc_data])
                plots["accel_y"].setData([d[1] for d in acc_data])
                plots["accel_z"].setData([d[2] for d in acc_data])
            if gyro_data:
                plots["gyro_x"].setData([d[0] for d in gyro_data])
                plots["gyro_y"].setData([d[1] for d in gyro_data])
                plots["gyro_z"].setData([d[2] for d in gyro_data])
