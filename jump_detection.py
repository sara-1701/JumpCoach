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

    def __init__(self, data_queues, jumps):
        super().__init__()
        self.data_queues = data_queues  # {Device address: (accel_deque, gyro_deque)}
        self.jumps = jumps  # Shared list to store jumps
        self.running = True
        self.last_jump_time = -2  # To ensure a 2-second cooldown between jumps

    def calculate_velocity(self, acc_data, time_interval=0.01):
        """Calculate velocity by integrating acceleration."""
        acc_centered = np.array(acc_data) - np.mean(acc_data)  # Remove bias
        velocity = np.cumsum(acc_centered) * time_interval
        return velocity

    # Function to find takeoff, jump peak, and landing points using velocity
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
            if "D9:85:F5:D6:7B:ED" not in self.data_queues:
                sleep(0.01)
                continue

            lower_back_data = self.data_queues["D9:85:F5:D6:7B:ED"][
                0
            ]  # Acceleration data

            if len(lower_back_data) >= 100:  # At least 1 second of data
                current_time = time()
                if lower_back_data[-1][0] > 2 and (
                    current_time - self.last_jump_time > 2
                ):
                    print("Jump detected!")
                    self.last_jump_time = current_time

                    # Wait for 3 second to ensure post-jump data is available
                    sleep(3)

                    # Extract 100 points before and 100 points after the jump
                    lower_back_acc = list(self.data_queues["D9:85:F5:D6:7B:ED"][0])[
                        -200:
                    ]
                    lower_back_gyro = list(self.data_queues["D9:85:F5:D6:7B:ED"][1])[
                        -200:
                    ]
                    wrist_acc = list(self.data_queues["FA:6C:EB:21:F6:9A"][0])[-200:]
                    wrist_gyro = list(self.data_queues["FA:6C:EB:21:F6:9A"][1])[-200:]
                    thigh_acc = list(self.data_queues["CD:36:98:87:7A:4D"][0])[-200:]
                    thigh_gyro = list(self.data_queues["CD:36:98:87:7A:4D"][1])[-200:]

                    # Get low back x acceleration
                    lower_back_acc_x = [point[0] for point in lower_back_acc]
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
                        lower_back_gyro=lower_back_gyro,
                        wrist_acc=wrist_acc,
                        wrist_gyro=wrist_gyro,
                        thigh_acc=thigh_acc,
                        thigh_gyro=thigh_gyro,
                        metrics=metrics,
                        detected_time=current_time,
                        partition=(takeoff_idx, peak_idx, landing_idx),
                    )
                    self.jumps.append(jump)  # Add to shared list
                    self.jump_detected.emit(len(self.jumps) - 1)  # Emit jump for GUI

            sleep(0.01)  # Control loop rate

    def run(self):
        self.detect_jumps()

    def stop(self):
        self.running = False
