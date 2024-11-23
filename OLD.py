from PyQt5.QtWidgets import QApplication
from Project.Code.GUI_OLD_DELETE import MainApp
from IMU_manager import IMUDataThread
from time import sleep

# Define globals in main
imu_info = {
    "D9:85:F5:D6:7B:ED": "Lower Back",
    "FA:6C:EB:21:F6:9A": "Wrist",
    "CD:36:98:87:7A:4D": "Thigh",
}

data_queues = {}  # {IMU address: (accel_deque, gyro_deque)}
threads = []  # List to manage threads

# Initialize the application
app = QApplication([])

# Create the GUI
window = MainApp(imu_info)
window.show()

# Start threads for connecting and managing IMUs
for address in imu_info:
    thread = IMUDataThread(address, data_queues)
    thread.connection_status.connect(window.update_status)
    thread.update_data.connect(window.update_plot)
    thread.start()
    threads.append(thread)
    sleep(0.5)

# Run the GUI
app.exec_()

# Cleanup: stop threads
for thread in threads:
    thread.stop()

print("Bye!")
