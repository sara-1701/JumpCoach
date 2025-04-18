from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal
from GUI_Connecting import GUIConnecting
from GUI_LivePlots import GUILivePlots
from GUI_Jump import GUIJump
from GUI_Metrics import GUIMetrics
from GUI_Selector import *
from GUI_Feedback import *


# Define Google color palette
COLORS = {
    "blue": "#4285F4",  # Google's blue
    "red": "#EA4335",  # Google's red
    "yellow": "#FBBC05",  # Google's yellow
    "green": "#34A853",  # Google's green
    "white": "#fdfdfd",  # White for backgrounds
    "grey": "#F4F4F4",  # Light grey for backgrounds
    "dark_grey": "#5F6368",  # Dark grey for text
    "black": "#000000",  # Black for text
    "plot_bg": "#fdfdfd",  # Background for plots
    "plot_fg": "#000000",  # Foreground for plots
    "plot_lines_x": "#4285F4",  # X-axis line color
    "plot_lines_y": "#EA4335",  # Y-axis line color
    "plot_lines_z": "#34A853",  # Z-axis line color
    "line_takeoff": "#FBBC05",
    "line_peak": "#FBBC05",
    "line_landing": "#FBBC05",
    "app_bg": "#e0e0e0",  # Light grey for app background
    "block_bg": "#f2f3f4",  # Light grey for plot blocks
    "accent_color": "#FFD500",
}


from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QLabel, QWidget, QHBoxLayout


class JumpAnalyzer(QWidget):
    def __init__(
        self,
        color_palette,
        jumps,
        jump_widget,
        metrics_widget,
        feedback_widget,
        panel_width,
    ):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.jump_widget = jump_widget
        self.metrics_widget = metrics_widget
        self.feedback_widget = feedback_widget
        self.panel_width = panel_width

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Initial placeholder label
        self.placeholder_label = QLabel("Jump!")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 64px; padding: 20px;")
        self.layout.addWidget(self.placeholder_label)

        # Container for the entire JumpAnalyzer box (initially hidden)
        self.container = QWidget()
        self.container.setHidden(True)
        self.container.setStyleSheet(
            f"""
            background-color: {color_palette['block_bg']};
            border-radius: 10px;
            padding: 0px;
            """
        )
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # JumpGUI (on the left side, larger)
        main_layout = QHBoxLayout()
        main_layout.addWidget(jump_widget, stretch=2)

        # Right panel (selector, metrics, and feedback)
        right_panel = QVBoxLayout()

        # Scrollable selector
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize((panel_width - 60), 170)
        self.selector_widget = GUISelector(
            self.color_palette, self.jumps, jump_widget, metrics_widget, feedback_widget
        )
        scroll_area.setWidget(self.selector_widget)
        right_panel.addWidget(scroll_area, stretch=1)

        # Metrics and feedback
        right_panel.addWidget(metrics_widget, stretch=2)
        right_panel.addWidget(feedback_widget, stretch=1)

        # Combine layouts
        main_layout.addLayout(right_panel)
        container_layout.addLayout(main_layout)
        self.layout.addWidget(self.container)

    def toggle_ui(self, show_full_ui=False):
        if show_full_ui:
            self.placeholder_label.setHidden(True)
            self.container.setHidden(False)
        else:
            self.placeholder_label.setHidden(False)
            self.container.setHidden(True)


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

        # Create the Feedback widget using GUIFeedbackBox
        self.feedback_widget = GUIFeedbackBox(self.color_palette, self.jumps)
        self.feedback_widget.setFixedWidth(panel_width - 50)

        # Create the JumpAnalyzer component
        self.jump_analyzer = JumpAnalyzer(
            self.color_palette,
            self.jumps,
            self.jump_widget,
            self.metrics_widget,
            self.feedback_widget,
            panel_width,
        )

        # Add widgets to the main layout
        self.main_layout.addWidget(self.live_plots_widget, stretch=1)
        self.main_layout.addWidget(self.jump_analyzer, stretch=2)

        # Hide widgets initially
        self.live_plots_widget.hide()
        self.jump_analyzer.hide()

    def show_dashboard(self):
        # Remove the connecting widget
        self.main_layout.removeWidget(self.connecting_widget)
        self.connecting_widget.deleteLater()

        # Show the dashboard widgets
        self.live_plots_widget.show()
        self.jump_analyzer.show()

        # Emit the dashboard ready signal if needed
        self.dashboard_ready.emit()
