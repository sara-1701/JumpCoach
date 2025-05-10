from PyQt5.QtWidgets import QApplication
from GUI_MainApp import MainApp
from IMU_manager import IMUDataThread
from jump_detection import JumpDetectionThread, Jump
from time import sleep
import pickle

# -------------------- CONFIG --------------------
IMPORT_JUMPS = True
EXPORT_JUMPS = True
INPUT_FILENAME = "May5/Zengwhen4.pkl"
OUTPUT_FILENAME = "May5/Zhengyu.pkl"

DEVICE_INFO = {
    "FA:6C:EB:21:F6:9A": "Wrist",
    "C5:2D:26:FB:96:48": "Lower Back",
    "CD:36:98:87:7A:4D": "Thigh",
}


# -------------------- IO UTILS --------------------
def load_jumps(filename, *, recalc=True):
    """Return a list of Jump objects.
    If recalc=True we rebuild every Jump from the raw 6‑axis IMU arrays."""
    with open(filename, "rb") as f:
        loaded = pickle.load(f)

    if not recalc:  # keep old behaviour if you ever need it
        return loaded

    rebuilt = []
    for i, j in enumerate(loaded):  # j is the pickled Jump
        rebuilt.append(
            Jump(
                lower_back_accel=j.lower_back_accel,
                lower_back_gyro=j.lower_back_gyro,
                wrist_accel=j.wrist_accel,
                wrist_gyro=j.wrist_gyro,
                thigh_accel=j.thigh_accel,
                thigh_gyro=j.thigh_gyro,
                detected_time=j.detected_time,
                partition=j.partition,
                imported=True,
            )
        )
    return rebuilt


def save_jumps(jumps, filename):
    with open(filename, "wb") as f:
        pickle.dump(jumps, f)
    print(f"Exported {len(jumps)} jumps to {filename}")


# -------------------- MAIN APP --------------------
def main():
    data = {}
    jumps = load_jumps(INPUT_FILENAME) if IMPORT_JUMPS else []
    print(f"Imported {len(jumps)} jumps") if IMPORT_JUMPS else None

    app = QApplication([])

    window = MainApp(DEVICE_INFO, data, jumps)
    window.show()

    # Start IMU threads
    threads = []
    for address in DEVICE_INFO:
        thread = IMUDataThread(address, data)
        thread.connection_status.connect(window.connecting_widget.update_status)
        thread.start()
        threads.append(thread)
        sleep(0.1)

    # Start Jump Detection thread
    jump_thread = JumpDetectionThread(DEVICE_INFO, data, jumps, IMPORT_JUMPS)
    jump_thread.jump_detected.connect(window.jump_analyzer.selector_widget.update_ui)
    jump_thread.first_jump_detected.connect(
        lambda: window.jump_analyzer.toggle_ui(True)
    )
    jump_thread.start()

    app.exec_()

    if EXPORT_JUMPS:
        save_jumps(jumps, OUTPUT_FILENAME)

    for thread in threads:
        thread.stop()

    print("Bye!")


if __name__ == "__main__":
    main()
