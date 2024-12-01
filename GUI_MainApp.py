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
from GUI_Selector import *


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


from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QLabel, QWidget, QHBoxLayout


class JumpAnalyzer(QWidget):
    """Component to encapsulate JumpGUI, GUIMetrics, Dynamic Jump Selector, and Feedback."""

    def __init__(
        self, color_palette, jumps, jump_widget, metrics_widget, feedback_widget
    ):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.jump_widget = jump_widget
        self.metrics_widget = metrics_widget
        self.feedback_widget = feedback_widget

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Container for the entire JumpAnalyzer box
        container = QWidget()
        container.setStyleSheet(
            f"""
            background-color: {color_palette['block_bg']};
            border-radius: 10px;
            padding: 0px;
            """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # JumpGUI (on the left side, larger)
        main_layout = QHBoxLayout()
        main_layout.addWidget(jump_widget, stretch=2)

        # Right panel (selector, metrics, and feedback)
        right_panel = QVBoxLayout()

        # GUISelector component (manages the dynamic selection of jumps)
        self.selector_widget = GUISelector(
            self.color_palette,
            self.jumps,
            jump_widget,
            metrics_widget,
        )
        right_panel.addWidget(
            self.selector_widget, stretch=1
        )  # Ensure it takes appropriate space

        # Add metrics widget below the selector area
        right_panel.addWidget(metrics_widget, stretch=1)

        # Feedback component (below metrics)
        self.feedback_widget = self.create_feedback_widget()
        right_panel.addWidget(self.feedback_widget)

        # Add JumpGUI and right panel to container
        main_layout.addLayout(right_panel)
        container_layout.addLayout(main_layout)

        # Add the container to the main layout
        self.layout.addWidget(container)

    def create_feedback_widget(self):
        """Create the feedback widget (initially empty)."""
        feedback = QLabel("Feedback: (To be implemented)")
        feedback.setAlignment(Qt.AlignCenter)
        feedback.setStyleSheet(
            f"""
            background-color: {self.color_palette['grey']};
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
            color: {self.color_palette['dark_grey']};
            """
        )
        return feedback


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
        self.main_layout = QHBoxLayout(self)
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

        # Create live plots widget
        self.live_plots_widget = GUILivePlots(
            self.color_palette, self.device_info, self.data
        )
        self.live_plots_widget.setFixedWidth(panel_width)

        # Create metrics widget
        self.metrics_widget = GUIMetrics(self.color_palette, self.jumps)
        self.metrics_widget.setFixedWidth(panel_width - 50)

        # Create the Jump Plot widget
        self.jump_widget = GUIJump(
            self.color_palette, self.device_info, self.jumps, self.metrics_widget
        )
        self.jump_widget.setFixedWidth(panel_width)

        # Create the Feedback widget
        self.feedback_widget = self.create_placeholder("Panel Placeholder")
        self.feedback_widget.setFixedWidth(panel_width - 50)

        # Create the JumpAnalyzer component
        self.jump_analyzer = JumpAnalyzer(
            self.color_palette,
            self.jumps,
            self.jump_widget,
            self.metrics_widget,
            self.feedback_widget,
        )

        # Add widgets to the main layout
        self.main_layout.addWidget(self.live_plots_widget, stretch=1)
        self.main_layout.addWidget(self.jump_analyzer, stretch=2)

        # Hide widgets initially
        self.live_plots_widget.hide()
        self.jump_analyzer.hide()

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

    def show_dashboard(self):
        # Remove the connecting widget
        self.main_layout.removeWidget(self.connecting_widget)
        self.connecting_widget.deleteLater()

        # Show the dashboard widgets
        self.live_plots_widget.show()
        self.jump_analyzer.show()

        # Emit the dashboard ready signal if needed
        self.dashboard_ready.emit()
