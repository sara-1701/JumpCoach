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
        details = (
            f"Jump detected at {self.detected_time:.2f} seconds\n"
            f"Lower Back - Accel points: {len(self.lower_back_accel)}, Gyro points: {len(self.lower_back_gyro)}\n"
            f"Wrist - Accel points: {len(self.wrist_accel)}, Gyro points: {len(self.wrist_gyro)}\n"
            f"Thigh - Accel points: {len(self.thigh_accel)}, Gyro points: {len(self.thigh_gyro)}"
        )
        return details

    # CALCULATE PARTITIONS --------------------------------------------
    def find_jump_events(self):
        # Extract timestamps and vertical (x-axis) velocity
        timestamps = self.lower_back_vel[:, 0]
        vertical_velocity = self.lower_back_vel[:, 1]  # x-axis
        # print(vertical_velocity)
        # Find indices for takeoff, peak, and landing
        takeoff_idx = np.argmax(vertical_velocity)  # Maximum upward velocity
        # print(takeoff_idx, vertical_velocity[takeoff_idx])

        landing_idx = takeoff_idx + np.argmin(vertical_velocity[takeoff_idx:])
        # print(landing_idx)
        # print(vertical_velocity[takeoff_idx:landing_idx])
        peak_idx = takeoff_idx + np.argmin(
            np.abs(vertical_velocity[takeoff_idx:landing_idx])
        )

        # Get corresponding times
        takeoff_time = timestamps[takeoff_idx]
        peak_time = timestamps[peak_idx]
        landing_time = timestamps[landing_idx]

        return (takeoff_time, peak_time, landing_time)

    # CALCULATE METRICS --------------------------------------------
    def calculate_metrics(self):
        """
        Calculate all jump metrics using available data and partition timestamps.
        """
        takeoff_time, peak_time, landing_time = self.partition

        metrics = {
            "airtime": calculate_airtime(self.partition),
            "height": calculate_height_from_displacement(
                self.lower_back_disp, self.partition
            ),
            "distance_traveled_x": calculate_distance_traveled(
                self.lower_back_disp, axis="x"
            ),
            "side_movement": calculate_distance_traveled(
                self.lower_back_disp, axis="y"
            ),
            "forward_backward_movement": calculate_distance_traveled(
                self.lower_back_disp, axis="z"
            ),
            "takeoff_max_vertical_arm_speed": calculate_max_speed(
                self.wrist_vel, "x", 0, takeoff_time
            ),
            "rise_max_vertical_arm_speed": calculate_max_speed(
                self.wrist_vel, "x", takeoff_time, peak_time
            ),
            "fall_max_vertical_arm_speed": calculate_max_speed(
                self.wrist_vel, "x", peak_time, landing_time
            ),
            "landing_max_vertical_arm_speed": calculate_max_speed(
                self.wrist_vel, "x", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_max_frontal_arm_speed": calculate_max_speed(
                self.wrist_vel, "y", 0, takeoff_time
            ),
            "rise_max_frontal_arm_speed": calculate_max_speed(
                self.wrist_vel, "y", takeoff_time, peak_time
            ),
            "fall_max_frontal_arm_speed": calculate_max_speed(
                self.wrist_vel, "y", peak_time, landing_time
            ),
            "landing_max_frontal_arm_speed": calculate_max_speed(
                self.wrist_vel, "y", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_max_lateral_arm_speed": calculate_max_speed(
                self.wrist_vel, "z", 0, takeoff_time
            ),
            "rise_max_lateral_arm_speed": calculate_max_speed(
                self.wrist_vel, "z", takeoff_time, peak_time
            ),
            "fall_max_lateral_arm_speed": calculate_max_speed(
                self.wrist_vel, "z", peak_time, landing_time
            ),
            "landing_max_lateral_arm_speed": calculate_max_speed(
                self.wrist_vel, "z", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_avg_vertical_arm_speed": calculate_average_speed(
                self.wrist_vel, "x", 0, takeoff_time
            ),
            "rise_avg_vertical_arm_speed": calculate_average_speed(
                self.wrist_vel, "x", takeoff_time, peak_time
            ),
            "fall_avg_vertical_arm_speed": calculate_average_speed(
                self.wrist_vel, "x", peak_time, landing_time
            ),
            "landing_avg_vertical_arm_speed": calculate_average_speed(
                self.wrist_vel, "x", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_avg_frontal_arm_speed": calculate_average_speed(
                self.wrist_vel, "y", 0, takeoff_time
            ),
            "rise_avg_frontal_arm_speed": calculate_average_speed(
                self.wrist_vel, "y", takeoff_time, peak_time
            ),
            "fall_avg_frontal_arm_speed": calculate_average_speed(
                self.wrist_vel, "y", peak_time, landing_time
            ),
            "landing_avg_frontal_arm_speed": calculate_average_speed(
                self.wrist_vel, "y", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_avg_lateral_arm_speed": calculate_average_speed(
                self.wrist_vel, "z", 0, takeoff_time
            ),
            "rise_avg_lateral_arm_speed": calculate_average_speed(
                self.wrist_vel, "z", takeoff_time, peak_time
            ),
            "fall_avg_lateral_arm_speed": calculate_average_speed(
                self.wrist_vel, "z", peak_time, landing_time
            ),
            "landing_avg_lateral_arm_speed": calculate_average_speed(
                self.wrist_vel, "z", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_vertical_arm_movement": calculate_movement(
                self.wrist_disp, "x", 0, takeoff_time
            ),
            "rise_vertical_arm_movement": calculate_movement(
                self.wrist_disp, "x", takeoff_time, peak_time
            ),
            "fall_vertical_arm_movement": calculate_movement(
                self.wrist_disp, "x", peak_time, landing_time
            ),
            "landing_vertical_arm_movement": calculate_movement(
                self.wrist_disp, "x", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_frontal_arm_movement": calculate_movement(
                self.wrist_disp, "y", 0, takeoff_time
            ),
            "rise_frontal_arm_movement": calculate_movement(
                self.wrist_disp, "y", takeoff_time, peak_time
            ),
            "fall_frontal_arm_movement": calculate_movement(
                self.wrist_disp, "y", peak_time, landing_time
            ),
            "landing_frontal_arm_movement": calculate_movement(
                self.wrist_disp, "y", landing_time, self.wrist_disp[-1][0]
            ),
            "takeoff_lateral_arm_movement": calculate_movement(
                self.wrist_disp, "z", 0, takeoff_time
            ),
            "rise_lateral_arm_movement": calculate_movement(
                self.wrist_disp, "z", takeoff_time, peak_time
            ),
            "fall_lateral_arm_movement": calculate_movement(
                self.wrist_disp, "z", peak_time, landing_time
            ),
            "landing_lateral_arm_movement": calculate_movement(
                self.wrist_disp, "z", landing_time, self.wrist_disp[-1][0]
            ),
            "_vertical_arm_movement": calculate_movement(
                self.wrist_disp, "x", 0, self.wrist_disp[-1][0]
            ),
            "_lateral_arm_movement": calculate_movement(
                self.wrist_disp, "y", 0, self.wrist_disp[-1][0]
            ),
            "_frontal_arm_movement": calculate_movement(
                self.wrist_disp, "z", 0, self.wrist_disp[-1][0]
            ),
            "landing_impact_max_acceleration": calculate_landing_impact(
                self.wrist_disp, landing_time
            )[0],
            "landing_impact_jerk": calculate_landing_impact(
                self.wrist_disp, landing_time
            )[1],
        }

        return metrics


class JumpDetectionThread(QThread):
    jump_detected = pyqtSignal(
        int, int, int
    )  # Signal to emit Jump object index for GUI
    first_jump_detected = pyqtSignal()

    def __init__(self, device_info, data, jumps, import_jumps_flag):
        super().__init__()
        self.device_info = device_info
        self.data = data
        self.jumps = jumps
        self.running = True
        self.last_jump_time = -2  # To ensure a 2-second cooldown between jumps
        self.import_jumps_flag = import_jumps_flag

    def run(self):
        self.detect_jumps()

    def detect_jumps(self):
        while self.running:
            if self.import_jumps_flag:
                self.import_jumps_flag = False
                print(f"\nRecalculate jumps")
                # Recreate each jump object in place to recalculate metrics
                for i in range(len(self.jumps)):
                    old_jump = self.jumps[i]
                    self.jumps[i] = Jump(
                        lower_back_accel=old_jump.lower_back_accel,
                        lower_back_gyro=old_jump.lower_back_gyro,
                        wrist_accel=old_jump.wrist_accel,
                        wrist_gyro=old_jump.wrist_gyro,
                        thigh_accel=old_jump.thigh_accel,
                        thigh_gyro=old_jump.thigh_gyro,
                        detected_time=old_jump.detected_time,
                    )
                self.first_jump_detected.emit()
                sorted_indices = sorted(
                    range(len(self.jumps)),
                    key=lambda i: self.jumps[i].metrics.get("height", 0),
                    reverse=True,
                )
                highest_jump_idx = sorted_indices[0]
                second_highest_jump_idx = (
                    sorted_indices[1] if len(sorted_indices) > 1 else None
                )

                # Emit the indices
                self.jump_detected.emit(
                    len(self.jumps) - 1, highest_jump_idx, second_highest_jump_idx
                )
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

        sorted_indices = sorted(
            range(len(self.jumps)),
            key=lambda i: self.jumps[i].metrics.get("height", 0),
            reverse=True,
        )
        highest_jump_idx = sorted_indices[0]
        second_highest_jump_idx = sorted_indices[1] if len(sorted_indices) > 1 else None

        # Emit the indices
        self.jump_detected.emit(
            len(self.jumps) - 1, highest_jump_idx, second_highest_jump_idx
        )

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


def calculate_height_from_displacement(lower_back_disp, partition):
    takeoff_time, _, landing_time = partition

    # Find the indices for takeoff and landing times
    takeoff_idx = np.where(lower_back_disp[:, 0] == takeoff_time)[0][0]
    landing_idx = np.where(lower_back_disp[:, 0] == landing_time)[0][0]
    airtime_lower_back_disp = lower_back_disp[takeoff_idx : landing_idx + 1, :]
    x_airtime_lower_back_disp = airtime_lower_back_disp[:, 1]
    y_airtime_lower_back_disp = airtime_lower_back_disp[:, 2]
    z_airtime_lower_back_disp = airtime_lower_back_disp[:, 3]
    return np.max(x_airtime_lower_back_disp)


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


def calculate_airtime(partition):
    """
    Calculate the airtime of the jump based on the partition timestamps.
    """
    takeoff_time, _, landing_time = partition
    return landing_time - takeoff_time


def calculate_distance_traveled(lower_back_disp, axis):
    """
    Calculate the distance traveled along a specific axis using displacement data.
    """
    axis_map = {"x": 1, "y": 2, "z": 3}
    axis_idx = axis_map.get(axis)

    displacement = lower_back_disp[:, axis_idx]
    if axis_idx == 1:
        return max(displacement)
    return max(displacement) - min(displacement)


def calculate_max_speed(velocity, axis, starttime, endtime):
    """
    Calculate the arm swing speed along a specific axis and during a specific phase.
    """
    axis_map = {"x": 1, "y": 2, "z": 3}
    axis_idx = axis_map.get(axis)

    # Extract velocities for the phase (assume all velocities during the phase are relevant)
    timestamps = velocity[:, 0]
    start_idx = np.abs(timestamps - starttime).argmin()
    end_idx = np.abs(timestamps - endtime).argmin()

    phase_velocity = velocity[start_idx : end_idx + 1, axis_idx]
    if len(phase_velocity) == 0:
        return 0
    return max(np.abs(phase_velocity))


def calculate_average_speed(velocity, axis, starttime, endtime):
    """
    Calculate the arm swing speed along a specific axis and during a specific phase.
    """
    axis_map = {"x": 1, "y": 2, "z": 3}
    axis_idx = axis_map.get(axis)

    # Extract velocities for the phase (assume all velocities during the phase are relevant)
    timestamps = velocity[:, 0]
    start_idx = np.abs(timestamps - starttime).argmin()
    end_idx = np.abs(timestamps - endtime).argmin()

    phase_velocity = velocity[start_idx : end_idx + 1, axis_idx]
    if len(phase_velocity) == 0:
        return 0
    return sum(np.abs(phase_velocity)) / len(phase_velocity)


def calculate_movement(displacement, axis, starttime, endtime):
    axis_map = {"x": 1, "y": 2, "z": 3}
    axis_idx = axis_map.get(axis)

    # Extract velocities for the phase (assume all velocities during the phase are relevant)
    timestamps = displacement[:, 0]
    start_idx = np.abs(timestamps - starttime).argmin()
    end_idx = np.abs(timestamps - endtime).argmin()

    phase_displacement = displacement[start_idx : end_idx + 1, axis_idx]
    if len(phase_displacement) == 0:
        return 0
    total_distance = np.sum(np.abs(np.diff(phase_displacement)))
    return total_distance


import numpy as np


def calculate_landing_impact(thigh_accel, starttime):
    """
    Calculate a landing impact metric using the thigh IMU acceleration data.

    Returns:
    - A dictionary containing:
        - 'peak_acceleration': The maximum magnitude of acceleration during landing.
        - 'mean_jerk': The average rate of change of acceleration (jerk) during landing.
    """
    # Extract timestamps and acceleration components
    timestamps = thigh_accel[:, 0]
    accel_data = thigh_accel[:, 1:]  # x, y, z columns

    # Find the indices corresponding to the landing phase
    start_idx = np.abs(timestamps - starttime).argmin() - 2
    end_idx = start_idx + 20

    # Extract the landing phase acceleration data
    landing_accel = accel_data[start_idx : end_idx + 1, :]
    landing_timestamps = timestamps[start_idx : end_idx + 1]

    if landing_accel.shape[0] < 2:  # Not enough data points to calculate metrics
        return [0, 0]

    # Calculate the magnitude of acceleration (Euclidean norm)
    accel_magnitude = np.linalg.norm(landing_accel, axis=1)

    # Calculate peak acceleration during landing
    peak_acceleration = np.max(accel_magnitude)

    # Calculate jerk (rate of change of acceleration)
    time_intervals = np.diff(landing_timestamps)  # Time intervals between samples
    accel_diff = np.diff(accel_magnitude)  # Differences in acceleration
    jerk = accel_diff / time_intervals  # Jerk (rate of change of acceleration)
    mean_jerk = np.mean(np.abs(jerk))  # Average absolute jerk

    return [peak_acceleration, mean_jerk]
