from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class GUIFeedbackBox(QWidget):
    """A widget to display feedback based on jump metrics."""

    def __init__(self, color_palette, jumps):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps  # Reference to the external jumps list
        self.init_ui()

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Remove margins
        layout.setSpacing(5)  # Minimal spacing between widgets

        # Feedback header label
        self.header_title = QLabel("Feedback for Next Jump")
        self.header_title.setAlignment(Qt.AlignCenter)
        self.header_title.setStyleSheet(
            f"""
            font-size: 27px;
            font-family: 'Roboto';
            color: {self.color_palette['plot_fg']};
            margin: 0px;
            padding: 0px;
            """
        )
        layout.addWidget(self.header_title, stretch=0)  # No stretch for the title

        # Feedback text label
        self.feedback_label = QLabel("Perform a jump to receive feedback!")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setWordWrap(True)  # Allow multi-line feedback
        self.feedback_label.setStyleSheet(
            f"""
            font-size: 24px;
            font-family: 'Roboto';
            background-color: {self.color_palette['white']};
            color: {self.color_palette['black']};
            border: 5px solid {self.color_palette['accent_color']};
            border-radius: 5px;
            margin: 0px;
            padding: 0px;
            """
        )
        layout.addWidget(
            self.feedback_label, stretch=1
        )  # Use stretch for the feedback box

    def update_feedback(self, jump_idx, pb_idx, second_pb_idx):
        """
        Update feedback based on metrics comparison between the selected jump and PB.

        Parameters:
        - jump_idx: Index of the selected jump.
        - pb_idx: Index of the personal best jump.
        """
        if not self.jumps:
            self.feedback_label.setText("No jumps recorded yet.")
            return

        selected_jump = self.jumps[jump_idx].metrics
        pb_jump = self.jumps[pb_idx].metrics

        feedback = []

        # Feedback on jump height
        if selected_jump.get("height", 0) >= pb_jump.get("height", 0):
            feedback.append("NEW PB! Amazing height!")
        else:
            heights = [jump.metrics.get("height", 0) for jump in self.jumps]
            sorted_indices = sorted(
                range(len(heights)), key=lambda i: heights[i], reverse=True
            )
            selected_jump_rank = sorted_indices.index(jump_idx) + 1
            feedback.append(f"This was your {selected_jump_rank}th highest jump.")

        # Feedback on vertical arm speed during takeoff
        selected_vertical_speed = selected_jump.get("takeoff_avg_vertical_arm_speed", 0)
        pb_vertical_speed = pb_jump.get("takeoff_avg_vertical_arm_speed", 0)
        if selected_vertical_speed < pb_vertical_speed:
            feedback.append("Swing your arms more during takeoff for better height.")
        elif selected_vertical_speed > pb_vertical_speed:
            feedback.append("Swing your arms less during takeoff to maintain control.")

        # Feedback on lateral arm movement during takeoff
        selected_lateral_speed = selected_jump.get("takeoff_avg_lateral_arm_speed", 0)
        pb_lateral_speed = pb_jump.get("takeoff_avg_lateral_arm_speed", 0)
        if selected_lateral_speed > pb_lateral_speed:
            feedback.append(
                "Reduce lateral arm movement during takeoff for better stability."
            )
        elif selected_lateral_speed < pb_lateral_speed:
            feedback.append("Increase lateral arm movement slightly for more balance.")

        # Feedback on landing arm movement
        selected_landing_movement = selected_jump.get(
            "landing_vertical_arm_movement", 0
        )
        pb_landing_movement = pb_jump.get("landing_vertical_arm_movement", 0)
        if selected_landing_movement < pb_landing_movement:
            feedback.append("Improve arm stability during landing.")
        elif selected_landing_movement > pb_landing_movement:
            feedback.append("Keep your arms closer to your body during landing.")

        # Set feedback text
        self.feedback_label.setText("\n".join(feedback))
