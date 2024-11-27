from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal
from GUI_Connecting import GUIConnecting
from GUI_LivePlots import GUILivePlots
from GUI_Jump import GUIJump
from GUI_Metrics import GUIMetrics


# Define Google color palette
COLORS = {
    "blue": "#4285F4",  # Google's blue
    "red": "#EA4335",  # Google's red
    "yellow": "#FBBC05",  # Google's yellow
    "green": "#34A853",  # Google's green
    "white": "#FFFFFF",  # White for backgrounds
    "grey": "#F4F4F4",  # Light grey for backgrounds
    "dark_grey": "#5F6368",  # Dark grey for text
    "black": "#000000",  # Black for text
    "plot_bg": "#FFFFFF",  # Background for plots
    "plot_fg": "#000000",  # Foreground for plots
    "plot_lines_x": "#4285F4",  # X-axis line color
    "plot_lines_y": "#EA4335",  # Y-axis line color
    "plot_lines_z": "#34A853",  # Z-axis line color
    "app_bg": "#e0e0e0",  # Light grey for app background
    "block_bg": "#f4f4f4",  # Light grey for plot blocks
}


class MainApp(QWidget):
    # Signal to indicate when the dashboard is ready to be shown
    dashboard_ready = pyqtSignal()

    def __init__(self, device_info, data, jumps):
        super().__init__()
        self.device_info = device_info
        self.data = data
        self.jumps = jumps
        self.color_palette = COLORS  # Store the color palette
        self.setWindowTitle("JumpCoach - Sara and Michael")

        # Open in maximized mode
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()  # Always open in maximized mode
        self.setStyleSheet(f"background-color: {COLORS['app_bg']};")  # App background

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.connecting_widget = GUIConnecting(self.device_info, self.color_palette)
        self.main_layout.addWidget(self.connecting_widget)

        # Initialize dashboard widgets but keep them hidden
        self.initialize_dashboard()

        # Connect the signal for when all devices are connected
        self.connecting_widget.all_connected.connect(self.show_dashboard)

    def initialize_dashboard(self):
        # Get the screen's actual width
        screen_width = QApplication.primaryScreen().size().width()
        panel_width = screen_width // 3  # Divide into thirds

        # Create the main horizontal layout for the dashboard
        self.dashboard_layout = QHBoxLayout()

        # Create metrics widget first
        self.metrics_widget = GUIMetrics(self.color_palette, self.jumps)

        # Create the jump widget, passing the metrics widget
        self.jump_widget = GUIJump(
            self.color_palette, self.device_info, self.jumps, self.metrics_widget
        )

        # Create live plots widget
        self.live_plots_widget = GUILivePlots(
            self.color_palette, self.device_info, self.data
        )

        # Right-side container for metrics and placeholder
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.placeholder_widget = self.create_placeholder("Panel Placeholder")

        # Add metrics and placeholder to the right layout
        right_layout.addWidget(self.metrics_widget)
        right_layout.addWidget(self.placeholder_widget)

        # Set fixed widths for the panels
        self.live_plots_widget.setFixedWidth(panel_width)
        self.jump_widget.setFixedWidth(panel_width)
        right_panel.setFixedWidth(panel_width)  # Right panel has the same width

        # Add widgets to the horizontal layout
        self.dashboard_layout.addWidget(self.live_plots_widget)
        self.dashboard_layout.addWidget(self.jump_widget)
        self.dashboard_layout.addWidget(right_panel)

        # Add the dashboard layout to the main layout
        self.main_layout.addLayout(self.dashboard_layout)

        # Hide the widgets initially
        self.live_plots_widget.hide()
        self.jump_widget.hide()
        self.metrics_widget.hide()
        self.placeholder_widget.hide()

    def create_placeholder(self, text):
        """Create a placeholder widget with the given text."""
        placeholder = QLabel(text)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(
            f"""
            background-color: {COLORS['grey']};
            color: {COLORS['dark_grey']};
            font-size: 16px;
            font-family: 'Roboto', sans-serif;
            border: 1px solid {COLORS['dark_grey']};
            border-radius: 10px;
            padding: 20px;
            """
        )
        return placeholder

    def add_navigation_buttons(self):
        button_layout = QHBoxLayout()
        prev_button = QPushButton("Previous Jump")
        next_button = QPushButton("Next Jump")
        prev_button.clicked.connect(lambda: self.change_jump(-1))
        next_button.clicked.connect(lambda: self.change_jump(1))
        button_layout.addWidget(prev_button)
        button_layout.addWidget(next_button)
        self.layout.addLayout(button_layout)

    def show_dashboard(self):
        # Remove the connecting widget
        self.main_layout.removeWidget(self.connecting_widget)
        self.connecting_widget.deleteLater()

        # Show the dashboard widgets
        self.live_plots_widget.show()
        self.jump_widget.show()
        self.metrics_widget.show()
        self.placeholder_widget.show()

        # Emit the dashboard ready signal if needed
        self.dashboard_ready.emit()
