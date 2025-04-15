from PyQt5.QtWidgets import QApplication
from GUI_MainApp import *
from IMU_manager import *
from jump_detection import *
from time import sleep
import pickle


def load_jump_objects(filename="MichaelJumps.pkl"):
    with open(filename, "rb") as file:
        jumps = pickle.load(file)
    return jumps


def save_jump_objects(jumps, filename="465r76t8.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(jumps, file)


# Define device information
device_info = {
    "FA:6C:EB:21:F6:9A": "Wrist",
    "C5:2D:26:FB:96:48": "Lower Back",
    "CD:36:98:87:7A:4D": "Thigh",
}

data = {}  # {Device address: (accel_deque, gyro_deque)}
threads = []  # To manage IMU data threads
jumps = []
import_jumps = True
export_jumps = False

if import_jumps == True:
    jumps = load_jump_objects()
    print(f"Imported Jumps: {jumps}")

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
jump_detection_thread = JumpDetectionThread(device_info, data, jumps, import_jumps)
jump_detection_thread.jump_detected.connect(
    window.jump_analyzer.selector_widget.update_ui
)
jump_detection_thread.first_jump_detected.connect(
    lambda: window.jump_analyzer.toggle_ui(True)
)
jump_detection_thread.start()

# Run the application
app.exec_()


if export_jumps == True:
    jumps = save_jump_objects(jumps)
    print(f"Exported Jumps: {jumps}")

# Cleanup: stop threads
for thread in threads:
    thread.stop()


print("Bye!")
