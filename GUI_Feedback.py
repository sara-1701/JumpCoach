from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt


class GUIFeedbackBox(QWidget):
    def __init__(self, color_palette):
        super().__init__()
        self.color_palette = color_palette
        self.init_ui()

    def init_ui(self):
        # Set main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Feedback header label
        header_title = QLabel("Feedback for next Jump", self)
        header_title.setAlignment(Qt.AlignCenter)
        header_title.setStyleSheet(
            f"""
            font-size: 28px;
            font-family: 'Roboto';
            margin-right: 30px;
            color: {self.color_palette['plot_fg']};
            """
        )
        layout.addWidget(header_title)

        # Feedback text box
        self.feedback_text = QTextEdit()
        self.feedback_text.setPlaceholderText("Enter your feedback here...")
        self.feedback_text.setStyleSheet(
            f"""
            background-color: {self.color_palette['white']};
            color: {self.color_palette['black']};
            font-size: 16px;
            border: 1px solid {self.color_palette['dark_grey']};
            border-radius: 5px;
            padding: 10px;
            """
        )
        layout.addWidget(self.feedback_text)

    def get_feedback(self):
        """Get the current text from the feedback box."""
        return self.feedback_text.toPlainText()

    def set_feedback(self, text):
        """Set text in the feedback box."""
        self.feedback_text.setText(text)
