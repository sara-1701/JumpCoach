from PyQt5.QtWidgets import QApplication
from GUI_MainApp import MainApp
from IMU_manager import IMUDataThread
from jump_detection import JumpDetectionThread
from time import sleep

# Define device information
device_info = {
    "D9:85:F5:D6:7B:ED": "Lower Back",
    "FA:6C:EB:21:F6:9A": "Wrist",
    "CD:36:98:87:7A:4D": "Thigh",
}

data_queues = {}  # {Device address: (accel_deque, gyro_deque)}
threads = []  # To manage IMU data threads
jumps = []

# Initialize the application
app = QApplication([])

# Create the main app window
window = MainApp(device_info, jumps)
window.show()

# Start IMU threads and add them to the threads list
for address in device_info:
    thread = IMUDataThread(address, data_queues)
    thread.connection_status.connect(window.connecting_widget.update_status)
    thread.update_data.connect(window.live_plots_widget.update_plot)
    thread.start()
    threads.append(thread)
    sleep(0.1)  # Slight delay to stagger connections

# Start the Jump Detection thread
jump_detection_thread = JumpDetectionThread(data_queues, jumps)
jump_detection_thread.jump_detected.connect(window.jump_widget.update_jump_plot)
jump_detection_thread.start()


# Run the application
app.exec_()

# Cleanup: stop threads
for thread in threads:
    thread.stop()


print("Bye!")
