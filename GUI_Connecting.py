from PyQt5.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QTimer
from mbientlab.metawear import MetaWear, libmetawear, cbindings


class GUIConnecting(QWidget):
    all_connected = pyqtSignal()

    def __init__(self, device_info, color_palette):
        super().__init__()
        self.device_info = device_info
        self.color_palette = color_palette
        self.connected_count = 0
        self.status_boxes = {}
        self.loading_texts = ["", ".", "..", "..."]
        self.current_loading_index = 0

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Add connection title
        self.connection_title = QLabel("Let's first connect to the devices", self)
        self.connection_title.setAlignment(Qt.AlignCenter)
        self.connection_title.setFont(QFont("Roboto", 24))
        self.main_layout.addWidget(self.connection_title)

        # Add device connection boxes
        self.status_layout = QHBoxLayout()
        self.status_layout.setSpacing(5)
        self.status_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.addLayout(self.status_layout)
        for address, name in self.device_info.items():
            self.add_status_box(address, name)

        # Add spacer below
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Timer for loading animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_loading_animation)
        self.animation_timer.start(500)  # Update every 500ms

    def add_status_box(self, address, name):
        label = QLabel(f"{name}\n{address}\nConnecting...", self)
        label.setStyleSheet(
            f"""
            background-color: {self.color_palette['grey']};
            padding: 20px;
            font-size: 20px;
            font-family: 'Roboto', sans-serif;
            border-radius: 10px;
            border: 1px solid {self.color_palette['dark_grey']};
        """
        )
        label.setFixedSize(250, 150)
        label.setAlignment(Qt.AlignCenter)
        self.status_boxes[address] = label
        self.status_layout.addWidget(label)

    def update_loading_animation(self):
        self.current_loading_index = (self.current_loading_index + 1) % len(
            self.loading_texts
        )
        for address, label in self.status_boxes.items():
            if "Connected" not in label.text() and "Failed" not in label.text():
                label.setText(
                    f"{self.device_info[address]}\n{address}\nConnecting{self.loading_texts[self.current_loading_index]}"
                )

    def update_status(self, address, connected):
        label = self.status_boxes[address]
        if connected:
            label.setText(f"{self.device_info[address]}\n{address}\nConnected")
            label.setStyleSheet(
                f"""
                background-color: {self.color_palette['green']};
                padding: 20px;
                font-size: 20px;
                font-family: 'Roboto', sans-serif;
                border-radius: 10px;
                border: 1px solid {self.color_palette['dark_grey']};
            """
            )
            self.connected_count += 1
        else:
            label.setText(f"{self.device_info[address]}\n{address}\nFailed")
            label.setStyleSheet(
                f"""
                background-color: {self.color_palette['red']};
                padding: 20px;
                font-size: 20px;
                font-family: 'Roboto', sans-serif;
                border-radius: 10px;
                border: 1px solid {self.color_palette['dark_grey']};
            """
            )

        # Check if all devices are connected
        if self.connected_count == len(self.device_info):
            QTimer.singleShot(1000, self.all_connected.emit)
