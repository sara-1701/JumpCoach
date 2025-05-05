from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
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
    "blue": "#4285F4",
    "red": "#EA4335",
    "yellow": "#FBBC05",
    "green": "#34A853",
    "white": "#fdfdfd",
    "grey": "#F4F4F4",
    "dark_grey": "#5F6368",
    "black": "#000000",
    "plot_bg": "#fdfdfd",
    "plot_fg": "#000000",
    "plot_lines_x": "#4285F4",
    "plot_lines_y": "#EA4335",
    "plot_lines_z": "#34A853",
    "line_takeoff": "#FBBC05",
    "line_peak": "#FBBC05",
    "line_landing": "#FBBC05",
    "app_bg": "#e0e0e0",
    "block_bg": "#f2f3f4",
    "accent_color": "#FFD500",
}


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

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.placeholder_label = QLabel("Jump!")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 64px; padding: 20px;")
        self.layout.addWidget(self.placeholder_label)

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

        main_layout = QHBoxLayout()
        main_layout.addWidget(jump_widget, stretch=2)

        right_panel = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize((panel_width - 60), 170)
        self.selector_widget = GUISelector(
            self.color_palette, self.jumps, jump_widget, metrics_widget, feedback_widget
        )
        scroll_area.setWidget(self.selector_widget)
        right_panel.addWidget(scroll_area, stretch=1)

        right_panel.addWidget(metrics_widget, stretch=2)
        right_panel.addWidget(feedback_widget, stretch=1)

        main_layout.addLayout(right_panel)
        container_layout.addLayout(main_layout)
        self.layout.addWidget(self.container)

    def toggle_ui(self, show_full_ui=False):
        self.placeholder_label.setHidden(show_full_ui)
        self.container.setHidden(not show_full_ui)


class MainApp(QWidget):
    dashboard_ready = pyqtSignal()

    def __init__(self, device_info, data, jumps):
        super().__init__()
        self.device_info = device_info
        self.data = data
        self.jumps = jumps
        self.color_palette = COLORS
        self.setWindowTitle("JumpCoach - Sara and Michael")

        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()
        self.setStyleSheet(f"background-color: {COLORS['app_bg']};")

        # Layouts
        self.main_layout = QHBoxLayout()
        self.connecting_widget = GUIConnecting(self.device_info, self.color_palette)
        self.main_layout.addWidget(self.connecting_widget)

        self.initialize_dashboard()
        self.connecting_widget.all_connected.connect(self.show_dashboard)

        # Expand Feedback Button
        self.expand_feedback_button = QPushButton("Expand Feedback")
        self.expand_feedback_button.setStyleSheet(
            f"""
            background-color: {COLORS['blue']};
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            """
        )
        self.expand_feedback_button.clicked.connect(self.toggle_feedback_fullscreen)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.expand_feedback_button)

        # Wrap everything in wrapper layout
        self.wrapper_layout = QVBoxLayout()
        self.wrapper_layout.addLayout(self.main_layout)
        self.wrapper_layout.addLayout(bottom_layout)
        self.setLayout(self.wrapper_layout)

    def initialize_dashboard(self):
        screen_width = QApplication.primaryScreen().size().width()
        panel_width = screen_width // 3

        self.live_plots_widget = GUILivePlots(
            self.color_palette, self.device_info, self.data
        )
        self.live_plots_widget.setFixedWidth(panel_width)

        self.metrics_widget = GUIMetrics(self.color_palette, self.jumps)
        self.metrics_widget.setFixedWidth(panel_width - 50)

        self.jump_widget = GUIJump(
            self.color_palette, self.device_info, self.jumps, self.metrics_widget
        )
        self.jump_widget.setFixedWidth(panel_width)

        self.feedback_widget = GUIFeedbackBox(self.color_palette, self.jumps)
        self.feedback_widget.setFixedWidth(panel_width - 50)

        self.jump_analyzer = JumpAnalyzer(
            self.color_palette,
            self.jumps,
            self.jump_widget,
            self.metrics_widget,
            self.feedback_widget,
            panel_width,
        )

        self.main_layout.addWidget(self.live_plots_widget, stretch=1)
        self.main_layout.addWidget(self.jump_analyzer, stretch=2)

        self.live_plots_widget.hide()
        self.jump_analyzer.hide()

    def show_dashboard(self):
        self.main_layout.removeWidget(self.connecting_widget)
        self.connecting_widget.deleteLater()

        self.live_plots_widget.show()
        self.jump_analyzer.show()

        self.dashboard_ready.emit()

    def toggle_feedback_fullscreen(self):
        if not hasattr(self, "feedback_fullscreen") or not self.feedback_fullscreen:
            self.feedback_fullscreen = True
            self.expand_feedback_button.hide()

            # Create a fullscreen window (new top-level window)
            self.fullscreen_feedback_window = QWidget()
            self.fullscreen_feedback_window.setStyleSheet(
                f"background-color: {COLORS['block_bg']};"
            )
            layout = QVBoxLayout(self.fullscreen_feedback_window)
            layout.setContentsMargins(0, 0, 0, 0)

            # Create a fresh feedback widget copy
            self.fullscreen_feedback_copy = GUIFeedbackBox(
                self.color_palette, self.jumps
            )
            layout.addWidget(self.fullscreen_feedback_copy)

            # Exit button
            exit_button = QPushButton("Exit Fullscreen")
            exit_button.setStyleSheet("font-size: 16px; padding: 8px;")
            exit_button.clicked.connect(self.exit_feedback_fullscreen)
            layout.addWidget(exit_button, alignment=Qt.AlignRight)

            # Show window fullscreen
            self.fullscreen_feedback_window.setWindowTitle("Feedback - Fullscreen")
            self.fullscreen_feedback_window.showFullScreen()
        else:
            self.exit_feedback_fullscreen()

    def exit_feedback_fullscreen(self):
        self.feedback_fullscreen = False
        self.expand_feedback_button.show()

        # Close and clean up the temporary fullscreen window
        if hasattr(self, "fullscreen_feedback_window"):
            self.fullscreen_feedback_window.close()
            self.fullscreen_feedback_window.deleteLater()
            self.fullscreen_feedback_window = None

        if hasattr(self, "fullscreen_feedback_copy"):
            self.fullscreen_feedback_copy.deleteLater()
            self.fullscreen_feedback_copy = None
