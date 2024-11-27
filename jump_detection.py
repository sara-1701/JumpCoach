from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from time import sleep, time


class Jump:
    def __init__(
        self,
        lower_back_acc,
        lower_back_gyro,
        wrist_acc,
        wrist_gyro,
        thigh_acc,
        thigh_gyro,
        metrics,
        detected_time,
        partition,
    ):
        self.lower_back_acc = lower_back_acc
        self.lower_back_gyro = lower_back_gyro
        self.wrist_acc = wrist_acc
        self.wrist_gyro = wrist_gyro
        self.thigh_acc = thigh_acc
        self.thigh_gyro = thigh_gyro
        self.metrics = metrics
        self.detected_time = detected_time
        self.partition = partition

    def __repr__(self):
        return f"Jump(detected_time={self.detected_time}, height={self.metrics.get('height', 0):.2f})"


class JumpDetectionThread(QThread):
    jump_detected = pyqtSignal(int)  # Signal to emit Jump object for GUI

    def __init__(self, device_info, data, jumps):
        super().__init__()
        self.data = data
        self.device_info = device_info
        self.jumps = jumps  # Shared list to store jumps
        self.running = True
        self.last_jump_time = -2  # To ensure a 2-second cooldown between jumps

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

    def detect_jumps(self):
        while self.running:
            # Check if the lower back IMU data is available
            if "D9:85:F5:D6:7B:ED" not in self.data:
                sleep(0.01)
                continue

            # Extract the lower back accelerometer data
            lower_back_accel_data = self.data["D9:85:F5:D6:7B:ED"]["accel"]

            # Ensure the accelerometer data is not empty
            if lower_back_accel_data.shape[0] >= 100:  # At least 1 second of data
                current_time = time()
                if lower_back_accel_data[-1, 1] > 2 and (
                    current_time - self.last_jump_time > 2
                ):
                    print("Jump detected!")
                    self.last_jump_time = current_time

                    # Wait for 2 seconds to ensure post-jump data is available
                    sleep(2)

                    # Extract the last 200 points (or all available if fewer)
                    lower_back_acc = lower_back_accel_data[-200:]
                    wrist_acc = self.data.get("FA:6C:EB:21:F6:9A", {}).get(
                        "accel", np.zeros((0, 4))
                    )[-200:]
                    thigh_acc = self.data.get("CD:36:98:87:7A:4D", {}).get(
                        "accel", np.zeros((0, 4))
                    )[-200:]

                    # Extract the acceleration X values
                    lower_back_acc_x = lower_back_acc[:, 1]
                    lower_back_velocity_x = self.calculate_velocity(lower_back_acc_x)

                    # Partition Jump
                    takeoff_idx, peak_idx, landing_idx = (
                        self.find_jump_events_using_velocity(lower_back_velocity_x)
                    )

                    # Calculate metrics
                    height = self.calculate_height(lower_back_velocity_x)
                    metrics = {"height": height}

                    # Create Jump object
                    jump = Jump(
                        lower_back_acc=lower_back_acc,
                        lower_back_gyro=self.data["D9:85:F5:D6:7B:ED"]["gyro"][-200:],
                        wrist_acc=wrist_acc,
                        wrist_gyro=self.data.get("FA:6C:EB:21:F6:9A", {}).get(
                            "gyro", np.zeros((0, 4))
                        )[-200:],
                        thigh_acc=thigh_acc,
                        thigh_gyro=self.data.get("CD:36:98:87:7A:4D", {}).get(
                            "gyro", np.zeros((0, 4))
                        )[-200:],
                        metrics=metrics,
                        detected_time=current_time,
                        partition=(takeoff_idx, peak_idx, landing_idx),
                    )
                    self.jumps.append(jump)
                    self.jump_detected.emit(len(self.jumps) - 1)

            sleep(0.01)  # Control loop rate

    def run(self):
        self.detect_jumps()

    def stop(self):
        self.running = False
