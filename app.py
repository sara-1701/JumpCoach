from PyQt5.QtWidgets import QApplication
from GUI_MainApp import *
from IMU_manager import *
from jump_detection import *
from time import sleep

# Define device information
device_info = {
    "FA:6C:EB:21:F6:9A": "Wrist",
    "D9:85:F5:D6:7B:ED": "Lower Back",
    "CD:36:98:87:7A:4D": "Thigh",
}

data = {}  # {Device address: (accel_deque, gyro_deque)}
threads = []  # To manage IMU data threads
jumps = []

# Initialize the application
app = QApplication([])

# Create the main app window
window = MainApp(device_info, data, jumps)
window.show()

# Start IMU threads and add them to the threads list
for address in device_info:
    thread = IMUDataThread(address, data)
    thread.connection_status.connect(window.connecting_widget.update_status)
    thread.start()
    threads.append(thread)
    sleep(0.1)  # Slight delay to stagger connections

# Start the Jump Detection thread
jump_detection_thread = JumpDetectionThread(device_info, data, jumps)
jump_detection_thread.jump_detected.connect(
    window.jump_analyzer.selector_widget.update_ui
)
jump_detection_thread.first_jump_detected.connect(
    lambda: window.jump_analyzer.toggle_ui(True)
)
jump_detection_thread.start()


# Run the application
app.exec_()

# Cleanup: stop threads
for thread in threads:
    thread.stop()


print("Bye!")
