from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
import numpy as np
import random


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
        self.feedback_label.setAlignment(Qt.AlignLeft)  # Set text alignment to left
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
            padding: 15px;
            line-height: 1.4;  /* Reduced line spacing for more compact feedback lines */
            """
        )
        layout.addWidget(
            self.feedback_label, stretch=1
        )  # Use stretch for the feedback box

    def update_feedback(self, jump_idx, pb_idx, second_pb_idx):
        """
        Update feedback based on metrics comparison between the selected jump and PB.
        """
        feedback_dict = {
            # Priority Metrics
            "height": {
                "new_pb": "NEW PB! Amazing jump!",
                "high_rank": "This is your #X highest jump.",
                "worst": "This is your worst jump so far...",
            },
            "landing_impact_jerk": {
                "slightly_increase": "Try to land slightly softer for safety.",
                "increase": "Landing was harder so focus on landing softer.",
                "significantly_increase": "Land much softer! Avoid slamming into the ground.",
                "slightly_decrease": "Landing is slightly softer. Good.",
                "decrease": "Landing impact improved. Great!",
                "significantly_decrease": "Landing impact is significantly better. Awesome!",
            },
            # Takeoff Metrics
            "takeoff_knee_bend": {
                "slightly_increase": "Bend your knees slightly more during takeoff.",
                "increase": "Bend your knees more during takeoff.",
                "significantly_increase": "Bend your knees a lot more during takeoff.",
                "slightly_decrease": "Bend your knees slightly less during takeoff.",
                "decrease": "Bend your knees less during takeoff.",
                "significantly_decrease": "Don't overbend your knees during takeoff.",
            },
            "takeoff_avg_vertical_arm_speed": {
                "slightly_increase": "Swing your arms slightly more during takeoff.",
                "increase": "Swing your arms more during takeoff.",
                "significantly_increase": "Your arms are stiff. Swing them more during takeoff.",
                "slightly_decrease": "Swing your arms slightly less.",
                "decrease": "Swing your arms less.",
                "significantly_decrease": "Your arms are going crazy. Swing them less during takeoff.",
            },
            "takeoff_avg_lateral_arm_speed": {
                "slightly_increase": "Slightly increase lateral arm swing during takeoff.",
                "increase": "Increase lateral arm swing during takeoff.",
                "significantly_increase": "Significantly increase lateral arm swing during takeoff.",
                "slightly_decrease": "Slightly decrease lateral arm swing during takeoff.",
                "decrease": "Decrease lateral arm swing during takeoff.",
                "significantly_decrease": "Your arms are flopping like a bird. Decrease lateral arm swing during takeoff.",
            },
            # Airtime Metrics
            "airtime": {
                "slightly_increase": "",
                "increase": "",
                "significantly_increase": "Crazy airtime increase. Are you cheating JumpCoach?",
                "slightly_decrease": "",
                "decrease": "",
                "significantly_decrease": "You barely lifted your legs... Try harder...",
            },
            # Landing Metrics
            "landing_knee_bend": {
                "slightly_increase": "Bend your knees slightly more during landing.",
                "increase": "Bend your knees more during landing.",
                "significantly_increase": "You're landing too stiffly. Bend your knees properly during landing.",
                "slightly_decrease": "Bend your knees slightly less during landing.",
                "decrease": "Bend your knees less during landing.",
                "significantly_decrease": "Don't overbend your knees during landing. You will get hurt doing this",
            },
            # Movement Metrics
            "forward_backward_movement": {
                "slightly_increase": "",
                "increase": "",
                "significantly_increase": "You're falling forward/backward when jumping.  Stay more balanced.",
                "slightly_decrease": "",
                "decrease": "",
                "significantly_decrease": "You're falling forward/backward when jumping.  Stay more balanced.",
            },
            "lateral_movement": {
                "slightly_increase": "",
                "increase": "",
                "significantly_increase": "You're hopping sideways like a crab. Stay more balanced.",
                "slightly_decrease": "",
                "decrease": "",
                "significantly_decrease": "You're hopping sideways like a crab. Stay more balanced.",
            },
        }

        # Positive PB feedback messages
        pb_feedback_messages = [
            "Keep doing what you're doing!",
            "Fantastic performance! Stay explosive!",
            "You're crushing it! Keep up the great work!",
            "Amazing job! You're setting new standards!",
            "Impressive! Stay consistent and keep it up!",
        ]

        if not self.jumps:
            self.feedback_label.setText("No jumps recorded yet.")
            return []

        # Handle the baseline case
        if len(self.jumps) == 1:
            self.feedback_label.setText(
                "Baseline Recorded. Jump again to receive feedback!"
            )
            return []

        selected_jump = self.jumps[jump_idx].metrics
        pb_jump = self.jumps[pb_idx].metrics
        feedback = []
        changes = []

        # Priority metrics
        priority_metrics = ["height", "landing_impact_jerk"]

        # Handle priority metrics
        for metric in priority_metrics:
            if metric == "height":
                height_value = selected_jump.get(metric, 0)
                pb_value = pb_jump.get(metric, 0)
                if height_value >= pb_value:
                    # Add PB feedback
                    feedback.append(feedback_dict["height"]["new_pb"])
                    feedback.append(random.choice(pb_feedback_messages))
                else:
                    heights = [jump.metrics.get("height", 0) for jump in self.jumps]
                    sorted_indices = sorted(
                        range(len(heights)), key=lambda i: heights[i], reverse=True
                    )
                    selected_jump_rank = sorted_indices.index(jump_idx) + 1
                    if selected_jump_rank == len(heights):
                        feedback.append(feedback_dict["height"]["worst"])
                    else:
                        feedback.append(
                            feedback_dict["height"]["high_rank"].replace(
                                "#X", str(selected_jump_rank)
                            )
                        )
            elif metric == "landing_impact_jerk":
                selected_value = selected_jump.get(metric, 0)
                pb_value = pb_jump.get(metric, 0)
                if (
                    pb_value != 0
                    and not np.isnan(pb_value)
                    and not np.isnan(selected_value)
                ):
                    change = ((selected_value - pb_value) / pb_value) * 100
                else:
                    change = 0

                if change > 50:
                    feedback.append(feedback_dict[metric]["significantly_increase"])
                elif change > 20:
                    feedback.append(feedback_dict[metric]["increase"])
                elif change > 5:
                    feedback.append(feedback_dict[metric]["slightly_increase"])
                elif change < -50:
                    feedback.append(feedback_dict[metric]["significantly_decrease"])
                elif change < -20:
                    feedback.append(feedback_dict[metric]["decrease"])
                elif change < -5:
                    feedback.append(feedback_dict[metric]["slightly_decrease"])

        # Add Top 3 Metrics by Change (excluding priority metrics)
        for metric, pb_value in pb_jump.items():
            if (
                metric in priority_metrics  # Skip priority metrics
                or metric not in feedback_dict  # Skip metrics not in the dictionary
            ):
                continue
            selected_value = selected_jump.get(metric, 0)
            if (
                pb_value != 0
                and not np.isnan(pb_value)
                and not np.isnan(selected_value)
            ):
                change = ((selected_value - pb_value) / pb_value) * 100
            else:
                change = 0

            changes.append((metric, change))

        # Sort by absolute change and get top 3
        changes = sorted(changes, key=lambda x: abs(x[1]), reverse=True)
        top_changes = []
        for metric, change in changes:
            if len(top_changes) >= 1:
                break
            feedback_line = ""

            if change > 50:
                feedback_line = feedback_dict[metric].get("significantly_increase", "")
            elif change > 20:
                feedback_line = feedback_dict[metric].get("increase", "")
            elif change > 5:
                feedback_line = feedback_dict[metric].get("slightly_increase", "")
            elif change < -50:
                feedback_line = feedback_dict[metric].get("significantly_decrease", "")
            elif change < -20:
                feedback_line = feedback_dict[metric].get("decrease", "")
            elif change < -5:
                feedback_line = feedback_dict[metric].get("slightly_decrease", "")

            if feedback_line:  # Only add non-empty feedback
                feedback.append(feedback_line)
                top_changes.append(metric)

        # Format feedback as bullet points with a blank line between sections
        formatted_feedback = "\n\n".join(f"• {item}" for item in feedback)
        self.feedback_label.setText(formatted_feedback)

        # Return metrics for further use
        return priority_metrics + top_changes
