from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt


class GUISelector(QWidget):
    """A widget to handle the selection and display of jumps."""

    def __init__(self, color_palette, jumps, jump_widget, metrics_widget):
        super().__init__()
        self.color_palette = color_palette
        self.jump_widget = jump_widget
        self.metrics_widget = metrics_widget
        self.jumps = jumps  # Reference to the external jumps list

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        self.selector_label = None  # Initialize the placeholder label variable
        self.init_ui()

    def init_ui(self):
        """Initial UI setup with a placeholder label if there are no jumps."""
        self.update_ui()

    def update_ui(self):
        """Update UI to reflect current jumps, adding or removing buttons as needed."""
        # Clear existing widgets first
        self.clear_ui()
        # Add buttons for each jump or show the placeholder if the list is empty
        if not self.jumps:
            self.add_placeholder_label()
        else:
            for idx, jump in enumerate(self.jumps, start=1):
                self.add_jump_button(idx)
                self.update_jump_view(idx)

    def add_placeholder_label(self):
        """Add or show the placeholder label."""
        if not self.selector_label:
            self.selector_label = QLabel("Jump to see your performance!")
            self.selector_label.setAlignment(Qt.AlignCenter)
            self.selector_label.setStyleSheet(
                f"font-size: 16px; color: {self.color_palette['dark_grey']};"
            )
            self.layout.addWidget(self.selector_label)
        else:
            self.selector_label.show()  # Ensure the label is visible if reused

    def add_jump_button(self, idx):
        """Add a button for each jump."""
        button = QPushButton(f"Jump {idx}")
        button.setStyleSheet(
            f"background-color: {self.color_palette['blue']}; color: {self.color_palette['white']}; font-size: 14px;"
        )
        button.clicked.connect(lambda checked, idx=idx: self.update_jump_view(idx))
        self.layout.addWidget(button)

    def clear_ui(self):
        """Clears the layout of all widgets except the placeholder, if present."""
        while self.layout.count():
            child = self.layout.takeAt(0).widget()
            if child:
                child.hide()
                child.deleteLater()
        # Reset the placeholder label for potential reuse
        self.selector_label = None

    def update_jump_view(self, jump_idx):
        print("Update Jump View")
        jump_idx -= 1
        """Update the jump plot and metrics when a jump is selected."""
        self.jump_widget.update_jump_plot(jump_idx)
        self.metrics_widget.update_metrics_table(jump_idx)
