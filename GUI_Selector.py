from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt


class GUISelector(QWidget):
    """A widget to handle the selection and display of jumps."""

    def __init__(
        self, color_palette, jumps, jump_widget, metrics_widget, feedback_widget
    ):
        super().__init__()
        self.color_palette = color_palette
        self.jump_widget = jump_widget
        self.metrics_widget = metrics_widget
        self.feedback_widget = feedback_widget
        self.jumps = jumps  # Reference to the external jumps list

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Add title
        self.title_label = QLabel("Jump Selector")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 28px; font-family: 'Roboto';")
        self.layout.addWidget(self.title_label)

        # Horizontal layout for jump buttons
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(self.buttons_layout)

        self.selected_button = None  # Keep track of the currently selected button
        self.highest_jump_button = None
        self.second_highest_jump_button = None
        self.update_ui(recent_jump_idx=0, highest_jump_idx=0, second_highest_jump_idx=0)

    def update_ui(self, recent_jump_idx, highest_jump_idx, second_highest_jump_idx):
        """Update UI to reflect current jumps, adding or removing buttons as needed."""
        self.highest_jump_button = highest_jump_idx
        self.second_highest_jump_button = second_highest_jump_idx
        self.clear_ui()
        for i in range(1, len(self.jumps) + 1):
            self.add_jump_button(i)
            self.update_jump_view(i)

    def add_jump_button(self, idx):
        """Add a button for each jump."""
        # Determine if this is the highest jump
        is_highest_jump = idx - 1 == self.highest_jump_button

        # Create the button label
        label_text = f"Jump {idx}"
        if is_highest_jump:
            label_text += " (PB)"  # Add the PB label for the highest jump

        button = QPushButton(label_text)

        # Add the new button to the layout
        self.buttons_layout.addWidget(button)

        # Set all buttons to not selected initially
        for i in range(self.buttons_layout.count()):
            existing_button = self.buttons_layout.itemAt(i).widget()
            if existing_button:
                self.set_button_style(existing_button, selected=False)

        # Highlight the new button as the selected one
        self.set_button_style(button, selected=True)
        self.selected_button = button  # Update the selected button reference

        # Handle button click to update selection
        button.clicked.connect(
            lambda checked, idx=idx, btn=button: self.on_button_click(idx, btn)
        )

    def on_button_click(self, idx, button):
        """Handle button click and update styles."""
        # Deselect all buttons
        for i in range(self.buttons_layout.count()):
            existing_button = self.buttons_layout.itemAt(i).widget()
            if existing_button:
                self.set_button_style(existing_button, selected=False)

        # Highlight the clicked button
        self.set_button_style(button, selected=True)
        self.selected_button = button  # Update the selected button reference
        self.update_jump_view(idx)

    def clear_ui(self):
        """Clears the layout of all widgets."""
        while self.buttons_layout.count():
            child = self.buttons_layout.takeAt(0).widget()
            if child:
                child.hide()
                child.deleteLater()

    def update_jump_view(self, jump_idx):
        """Update the jump plot and metrics when a jump is selected."""
        print(f"Updating jump view for jump #{jump_idx}")
        jump_idx -= 1
        self.jump_widget.update_jump_plot(jump_idx)
        self.metrics_widget.update_metrics_table(
            jump_idx, self.highest_jump_button, self.second_highest_jump_button
        )
        self.feedback_widget.update_feedback(
            jump_idx, self.highest_jump_button, self.second_highest_jump_button
        )

    def set_button_style(self, button, selected):
        """Set button style based on selection state."""
        base_style = """
            font-size: 24px;
            padding: 12px 24px;
            border-radius: 10px;
            border: 1px solid {border_color};
            font-weight: normal;
            background-color: {background_color};
            color: {text_color};
        """
        if selected:
            button.setStyleSheet(
                base_style.format(
                    border_color=self.color_palette["dark_grey"],
                    background_color=self.color_palette["accent_color"],
                    text_color=self.color_palette["black"],
                )
            )
        else:
            button.setStyleSheet(
                base_style.format(
                    border_color=self.color_palette["dark_grey"],
                    background_color=self.color_palette["white"],
                    text_color=self.color_palette["dark_grey"],
                )
            )
