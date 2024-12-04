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
        detected_time,
    ):
        self.lower_back_accel = lower_back_accel
        self.lower_back_vel = take_integral(lower_back_accel)
        self.lower_back_disp = take_integral(self.lower_back_vel)
        self.lower_back_gyro = lower_back_gyro
        self.lower_back_ang_disp = take_integral(lower_back_gyro)

        self.wrist_accel = wrist_accel
        self.wrist_vel = take_integral(wrist_accel)
        self.wrist_disp = take_integral(self.wrist_vel)
        self.wrist_gyro = wrist_gyro
        self.wrist_ang_disp = take_integral(wrist_gyro)

        self.thigh_accel = thigh_accel
        self.thigh_vel = take_integral(thigh_accel)
        self.thigh_disp = take_integral(self.thigh_vel)
        self.thigh_gyro = thigh_gyro
        self.thigh_ang_disp = take_integral(thigh_gyro)

        self.detected_time = detected_time
        self.partition = self.find_jump_events()
        self.metrics = self.calculate_metrics()

    def __repr__(self):
        details = f"Jump detected at {self.detected_time:.2f} seconds:\n"
        return details

    # CALCULATE PARTITIONS --------------------------------------------
    def find_jump_events(self):
        # Calculate velocity for the lower back accelerometer
        velocity_data = self.lower_back_vel

        # Extract timestamps and vertical (x-axis) velocity
        timestamps = velocity_data[:, 0]  # First column is timestamps
        vertical_velocity = velocity_data[:, 1]  # First column is x-axis velocity

        # Find indices for takeoff, peak, and landing
        takeoff_idx = np.argmax(vertical_velocity)  # Maximum upward velocity
        peak_idx = takeoff_idx + np.argmin(
            np.abs(vertical_velocity[takeoff_idx : takeoff_idx + 20])
        )
        landing_idx = peak_idx + np.argmin(vertical_velocity[peak_idx:])

        # Get corresponding times
        takeoff_time = timestamps[takeoff_idx]
        peak_time = timestamps[peak_idx]
        landing_time = timestamps[landing_idx]

        return (takeoff_time, peak_time, landing_time)

    # CALCULATE METRICS --------------------------------------------
    def calculate_metrics(self):
        height = calculate_height(self.lower_back_vel, self.partition)
        return {"height": height}


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

            # Convert acceleration from g to m/s²
            acc_window[
                :, 1:
            ] *= 9.81  # Applying the conversion factor to all acceleration columns

            jump_data[dev_name] = {
                "accel": acc_window,
                "gyro": gyro_window,
            }

        # Create Jump object with converted acceleration data
        jump = Jump(
            lower_back_accel=jump_data["Lower Back"]["accel"],
            lower_back_gyro=jump_data["Lower Back"]["gyro"],
            wrist_accel=jump_data["Wrist"]["accel"],
            wrist_gyro=jump_data["Wrist"]["gyro"],
            thigh_accel=jump_data["Thigh"]["accel"],
            thigh_gyro=jump_data["Thigh"]["gyro"],
            detected_time=current_time,  # Use the approximate detected time of the jump
        )

        if len(self.jumps) == 0:
            self.first_jump_detected.emit()
        self.jumps.append(jump)
        print(f"Detected jump: {jump}")
        highest_jump_idx = max(
            range(len(self.jumps)), key=lambda i: self.jumps[i].metrics.get("height", 0)
        )
        self.jump_detected.emit(len(self.jumps) - 1, highest_jump_idx)

    # FIND PARTITIONS----------------------------------------------

    def stop(self):
        self.running = False


def take_integral(data):
    timestamps = data[:, 0]
    values = data[:, 1:]
    time_intervals = 2.0 / max(len(values), 1)
    values_centered = values - np.mean(values, axis=0)
    integrated_values = np.cumsum(values_centered, axis=0) * time_intervals
    return np.column_stack((timestamps, integrated_values))


def calculate_height(jump_velocity_data, partition):
    takeoff_time, _, landing_time = partition

    # Extract the timestamps and velocity components
    timestamps = jump_velocity_data[:, 0]  # First column is the timestamp
    vertical_velocity = jump_velocity_data[:, 1]

    # Find the indices for takeoff and landing times
    takeoff_idx = np.where(timestamps == takeoff_time)[0][0]
    landing_idx = np.where(timestamps == landing_time)[0][0]

    # Consider only the vertical velocity and timestamps between takeoff and landing
    relevant_velocity = vertical_velocity[takeoff_idx : landing_idx + 1]
    relevant_timestamps = timestamps[takeoff_idx : landing_idx + 1]
    print(f"Relevant timestamps: {[round(i, 20) for i in relevant_timestamps]}")
    print(f"airtime: : {(relevant_timestamps[-1] - relevant_timestamps[0])}")
    print(len(relevant_timestamps))
    # Dynamically calculate the time interval
    time_interval = (relevant_timestamps[-1] - relevant_timestamps[0]) / (
        len(relevant_timestamps) - 1
    )
    print(f"Calculated Time Interval: {time_interval}")

    # Integrate vertical velocity to compute displacement (height)
    displacement = np.cumsum(relevant_velocity) * time_interval

    # Height is the maximum displacement achieved during the jump
    print(f"Displacement: {displacement}")
    return max(displacement)
