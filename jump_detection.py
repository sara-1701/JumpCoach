from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from time import sleep, time


class Jump:
    def __init__(
        self,
        lower_back_accel,
        lower_back_gyro,
        wrist_accel,
        wrist_gyro,
        thigh_accel,
        thigh_gyro,
        metrics,
        detected_time,
        partition,
    ):
        self.lower_back_accel = lower_back_accel
        self.lower_back_gyro = lower_back_gyro
        self.wrist_accel = wrist_accel
        self.wrist_gyro = wrist_gyro
        self.thigh_accel = thigh_accel
        self.thigh_gyro = thigh_gyro
        self.metrics = metrics
        self.detected_time = detected_time
        self.partition = partition

    def __repr__(self):
        details = (
            f"Jump detected at {self.detected_time:.2f} seconds:\n"
            f"  Height: {self.metrics.get('height', 0):.2f} meters\n"
            f"  Takeoff, Peak, Landing Indices: {self.partition}\n"
            f"  Accelerometer Data Points:\n"
            f"    Lower Back: {self.lower_back_accel.shape[0] if self.lower_back_accel is not None else 0} points\n"
            f"    Wrist: {self.wrist_accel.shape[0] if self.wrist_accel is not None else 0} points\n"
            f"    Thigh: {self.thigh_accel.shape[0] if self.thigh_accel is not None else 0} points\n"
            f"  Gyroscope Data Points:\n"
            f"    Lower Back: {self.lower_back_gyro.shape[0] if self.lower_back_gyro is not None else 0} points\n"
            f"    Wrist: {self.wrist_gyro.shape[0] if self.wrist_gyro is not None else 0} points\n"
            f"    Thigh: {self.thigh_gyro.shape[0] if self.thigh_gyro is not None else 0} points"
        )
        return details


class JumpDetectionThread(QThread):
    jump_detected = pyqtSignal(int, int)  # Signal to emit Jump object index for GUI
    first_jump_detected = pyqtSignal()

    def __init__(self, device_info, data, jumps):
        super().__init__()
        self.device_info = device_info
        self.data = data
        self.jumps = jumps
        self.running = True
        self.last_jump_time = -2  # To ensure a 2-second cooldown between jumps

    def run(self):
        self.detect_jumps()

    def detect_jumps(self):
        while self.running:
            # Iterate over device information to find 'Lower Back' device
            for address, device_name in self.device_info.items():
                if (
                    device_name == "Lower Back"
                    and self.data[address]["accel"].shape[0] >= 100
                ):
                    accel_data = self.data[address]["accel"]
                    # Check the last value in the x-direction (second column for 0-index)
                    if accel_data[-1, 1] > 2 and (time() - self.last_jump_time > 2):
                        print("Jump detected!")
                        self.process_detected_jump(address)

            sleep(0.01)  # Slight delay to prevent overloading the CPU

    def process_detected_jump(self, address):
        current_time = time()
        self.last_jump_time = current_time

        # Wait for 1.5 seconds after the jump to ensure all post-jump data is available
        sleep(1.5)

        # Determine the time interval for data extraction
        pre_jump_time = current_time - 1  # Half a second before the jump
        post_jump_time = current_time + 1.5  # One and a half seconds after the jump

        # Prepare data from all devices for the Jump object
        jump_data = {}
        for dev_address, dev_name in self.device_info.items():
            acc_data = self.data[dev_address]["accel"]
            gyro_data = self.data[dev_address]["gyro"]

            # Extract data from half a second before to 1.5 seconds after the jump
            acc_window = acc_data[
                (acc_data[:, 0] >= pre_jump_time) & (acc_data[:, 0] <= post_jump_time)
            ]
            gyro_window = gyro_data[
                (gyro_data[:, 0] >= pre_jump_time) & (gyro_data[:, 0] <= post_jump_time)
            ]

            jump_data[dev_name] = {
                "acc": acc_window,
                "gyro": gyro_window,
            }

        # Calculate metrics using lower back data
        lower_back_velocity = self.calculate_velocity(
            jump_data["Lower Back"]["acc"][
                :, 1
            ]  # Assuming index 1 is the acceleration component
        )
        takeoff_idx, peak_idx, landing_idx = self.find_jump_events_using_velocity(
            lower_back_velocity
        )
        height = self.calculate_height(lower_back_velocity)
        metrics = {"height": height}

        # Create Jump object
        jump = Jump(
            lower_back_accel=jump_data["Lower Back"]["acc"],
            lower_back_gyro=jump_data["Lower Back"]["gyro"],
            wrist_accel=jump_data["Wrist"]["acc"],
            wrist_gyro=jump_data["Wrist"]["gyro"],
            thigh_accel=jump_data["Thigh"]["acc"],
            thigh_gyro=jump_data["Thigh"]["gyro"],
            metrics=metrics,
            detected_time=current_time,  # Use the approximate detected time of the jump
            partition=(takeoff_idx, peak_idx, landing_idx),
        )
        if len(self.jumps) == 0:
            self.first_jump_detected.emit()
        self.jumps.append(jump)
        print(f"Detected jump: {jump}")
        highest_jump_idx = max(
            range(len(self.jumps)), key=lambda i: self.jumps[i].metrics.get("height", 0)
        )
        self.jump_detected.emit(len(self.jumps) - 1, highest_jump_idx)

    def calculate_velocity(self, acc_data, time_interval=0.01):
        """Calculate velocity by integrating acceleration."""
        acc_centered = acc_data - np.mean(acc_data)  # Remove bias
        velocity = np.cumsum(acc_centered) * time_interval
        return velocity

    def find_jump_events_using_velocity(self, velocity):
        takeoff_idx = np.argmax(velocity)
        peak_idx = takeoff_idx + np.argmin(
            np.abs(velocity[takeoff_idx : takeoff_idx + 20])
        )
        landing_idx = peak_idx + np.argmin(velocity[peak_idx:])
        return takeoff_idx, peak_idx, landing_idx

    def calculate_height(self, velocity):
        displacement = np.cumsum(velocity) * 0.01
        return max(displacement) - min(displacement)

    def stop(self):
        self.running = False
