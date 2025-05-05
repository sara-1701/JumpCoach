from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from time import sleep, time
from scipy.integrate import cumtrapz
from scipy.signal import butter, filtfilt
import traceback

# ----------------------------------------------------
#  Utility: Personal‑best bookkeeping
# ----------------------------------------------------


def recompute_pb_flags(jumps):
    """(Re)assign pb_index / second_pb_index for every jump.

    For the *i‑th* jump (chronological order):
        • pb_index        → index of best height among jumps[0..i]
        • second_pb_index → index of 2nd‑best height among jumps[0..i] (None if <2)"""
    best_idx, second_idx = None, None
    best_h, second_h = -float("inf"), -float("inf")

    for i, j in enumerate(jumps):
        h = j.metrics.get("height", -float("inf")) if j.metrics else -float("inf")

        # update running leaders
        if h > best_h:
            second_idx, second_h = best_idx, best_h
            best_idx, best_h = i, h
        elif h > second_h:
            second_idx, second_h = i, h

        j.pb_index = best_idx
        j.second_pb_index = second_idx


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
        self.detected_time = detected_time

        # --- Raw Signals ---
        self.lower_back_accel = interpolate_to_uniform_spacing(lower_back_accel)
        self.lower_back_gyro = interpolate_to_uniform_spacing(lower_back_gyro)
        self.wrist_accel = interpolate_to_uniform_spacing(wrist_accel)
        self.wrist_gyro = interpolate_to_uniform_spacing(wrist_gyro)
        self.thigh_accel = interpolate_to_uniform_spacing(thigh_accel)
        self.thigh_gyro = interpolate_to_uniform_spacing(thigh_gyro)

        # --- Processed Signals ---
        self.lower_back_vel = take_integral(lower_back_accel)
        self.lower_back_disp = take_integral(self.lower_back_vel)
        self.lower_back_jerk = take_derivative(lower_back_accel)
        self.lower_back_ang_disp = take_integral(lower_back_gyro)

        self.wrist_vel = take_integral(wrist_accel)
        self.wrist_disp = take_integral(self.wrist_vel)
        self.wrist_jerk = take_derivative(wrist_accel)
        self.wrist_ang_disp = take_integral(wrist_gyro)

        self.thigh_vel = take_integral_for_leg(thigh_accel)
        self.thigh_disp = take_integral_for_leg(self.thigh_vel)
        self.thigh_jerk = take_derivative(thigh_accel)
        self.thigh_ang_disp = take_integral_for_leg(thigh_gyro)

        # --- Partition & Metrics ---
        try:
            self.partition = self.find_jump_events()
        except Exception as e:
            print(f"❌ Partitioning failed: {e}")
            self.partition = None

        self.metrics = self.calculate_metrics() if self.partition else None

        # --- Feedback Info ---
        self.feedback = None
        self.pb_index = None
        self.second_pb_index = None
        self.feedback_metrics = []
        self.stored_comparison_metrics = {
            "comparison_metrics": None,
            "comparison_label": "N/A",
        }

    def __repr__(self):
        return (
            f"Jump at {self.detected_time:.2f}s | "
            f"LB Accel: {len(self.lower_back_accel)} | "
            f"Wrist Accel: {len(self.wrist_accel)} | "
            f"Thigh Accel: {len(self.thigh_accel)}"
        )

    # ---------------------- event + metric helpers ----------------------
    def find_jump_events(self):
        timestamps = self.lower_back_vel[:, 0]
        vertical_velocity = self.lower_back_vel[:, 1]
        takeoff_idx = np.argmax(vertical_velocity)
        landing_idx = takeoff_idx + np.argmin(vertical_velocity[takeoff_idx:])
        peak_idx = takeoff_idx + np.argmin(
            np.abs(vertical_velocity[takeoff_idx:landing_idx])
        )
        return timestamps[takeoff_idx], timestamps[peak_idx], timestamps[landing_idx]

    def calculate_metrics(self):
        metrics = {
            "airtime": calculate_airtime(self.partition),
            "height": calculate_height_from_airtime(calculate_airtime(self.partition)),
            "total_arm_movement": calculate_total_arm_movement(self.wrist_disp),
            "landing_impact_jerk": calculate_landing_impact(
                self.thigh_jerk, self.partition[2]
            ),
            "takeoff_knee_bend": calculate_max_knee_bend_accel(
                self.thigh_accel, 0, self.partition[0]
            ),
            "landing_knee_bend": calculate_combined_knee_bend(
                self.thigh_accel,
                self.thigh_ang_disp,
                self.partition[2],
                self.thigh_accel[-1][0],
            ),
        }
        return metrics


class JumpDetectionThread(QThread):
    jump_detected = pyqtSignal(int, int, int)
    first_jump_detected = pyqtSignal()

    def __init__(self, device_info, data, jumps, import_jumps_flag):
        super().__init__()
        self.device_info = device_info
        self.data = data
        self.jumps = jumps
        self.running = True
        self.last_jump_time = -2
        self.import_jumps_flag = import_jumps_flag

    # ---------------------- main loop ----------------------
    def run(self):
        self.detect_jumps()

    def detect_jumps(self):
        while self.running:
            # ----- handle restored jumps once -----
            if self.import_jumps_flag:
                self.import_jumps_flag = False
                print("\nRestoring previously imported jumps")

                recompute_pb_flags(self.jumps)  # <-- ensure PB flags are correct
                self.first_jump_detected.emit()

                last_idx = len(self.jumps) - 1
                if last_idx >= 0:
                    j = self.jumps[last_idx]
                    self.jump_detected.emit(
                        last_idx, j.pb_index or -1, j.second_pb_index or -1
                    )
                else:
                    print("No jumps found in imported data.")

            # ----- live detection from lower‑back accelerometer -----
            for address, device_name in self.device_info.items():
                if (
                    device_name == "Lower Back"
                    and self.data[address]["accel"].shape[0] >= 100
                ):
                    accel_data = self.data[address]["accel"]
                    if accel_data[-1, 1] > 2.0 and (time() - self.last_jump_time > 2):
                        print("Jump detected!")
                        self.process_detected_jump()
            sleep(0.01)

    # ---------------------- process new live jump ----------------------
    def process_detected_jump(self):
        now = time()
        self.last_jump_time = now
        sleep(2)  # wait for post‑event data

        pre, post = now - 1.5, now + 1.5
        jump_segments = {}
        for addr, name in self.device_info.items():
            a = self.data[addr]["accel"]
            g = self.data[addr]["gyro"]
            a_win = a[(a[:, 0] >= pre) & (a[:, 0] <= post)].copy()
            g_win = g[(g[:, 0] >= pre) & (g[:, 0] <= post)].copy()
            a_win[:, 1:] *= 9.81  # m/s²
            jump_segments[name] = {"accel": a_win, "gyro": g_win}

        j = Jump(
            lower_back_accel=jump_segments["Lower Back"]["accel"],
            lower_back_gyro=jump_segments["Lower Back"]["gyro"],
            wrist_accel=jump_segments["Wrist"]["accel"],
            wrist_gyro=jump_segments["Wrist"]["gyro"],
            thigh_accel=jump_segments["Thigh"]["accel"],
            thigh_gyro=jump_segments["Thigh"]["gyro"],
            detected_time=now,
        )

        if j.metrics is None:
            print("⚠️  Faulty jump (no valid metrics). Not saving.")
            return

        if not self.jumps:
            self.first_jump_detected.emit()

        self.jumps.append(j)
        recompute_pb_flags(self.jumps)  # <-- single source of truth

        idx = len(self.jumps) - 1
        if hasattr(self, "window"):
            fb_metrics = self.window.feedback_widget.update_feedback(
                idx, j.pb_index or -1, j.second_pb_index or -1
            )
            j.feedback = self.window.feedback_widget.feedback_label.text()
            j.feedback_metrics = fb_metrics

        print(
            f"✅ Jump #{idx + 1} saved with height: {j.metrics.get('height', 0):.2f} m"
        )
        self.jump_detected.emit(idx, j.pb_index or -1, j.second_pb_index or -1)

    def stop(self):
        self.running = False


def interpolate_to_uniform_spacing(signal):
    """
    Resample the input signal so that it has uniformly spaced timestamps.

    Parameters:
    - signal: np.ndarray of shape (N, 4), where column 0 is timestamp, 1-3 are x, y, z.

    Returns:
    - np.ndarray of shape (N, 4) with uniform timestamps and interpolated x, y, z.
    """
    if signal.shape[0] < 2:
        return signal  # Not enough data to interpolate

    timestamps = signal[:, 0]
    start_time = timestamps[0]
    end_time = timestamps[-1]
    n_samples = len(timestamps)

    # Create uniform time vector
    uniform_times = np.linspace(start_time, end_time, n_samples)

    # Interpolate x, y, z separately
    interpolated_xyz = np.zeros((n_samples, 3))
    for i in range(1, 4):
        interpolated_xyz[:, i - 1] = np.interp(uniform_times, timestamps, signal[:, i])

    return np.column_stack((uniform_times, interpolated_xyz))


def take_integral_for_leg(data):
    timestamps = data[:, 0]
    values = data[:, 1:]
    # print(len(timestamps))
    # print(len(values))
    # print(timestamps[0])
    # print(len(values[0]), values[0])
    # print(len(data))
    # print(
    #    len(
    #        np.column_stack(
    #            (timestamps, cumtrapz(values, timestamps, axis=0, initial=0))
    #        )
    #    )
    # )
    # print()
    return np.column_stack(
        (timestamps, cumtrapz(values, timestamps, axis=0, initial=0))
    )

    # time_intervals = 3.0 / max(len(values), 1)
    # values_centered = values - np.mean(values, axis=0)
    # integrated_values = np.cumsum(values_centered, axis=0) * time_intervals
    # return np.column_stack((timestamps, integrated_values))


def take_integral(data):
    timestamps = data[:, 0]
    values = data[:, 1:]
    time_intervals = 3.0 / max(len(values), 1)
    values_centered = values - np.mean(values, axis=0)
    integrated_values = np.cumsum(values_centered, axis=0) * time_intervals
    return np.column_stack((timestamps, integrated_values))


def take_derivative(data):
    timestamps = data[:, 0]
    values = data[:, 1:]
    values[:, 0], values[:, 1], values[:, 2] = (
        low_pass_filter(values[:, 0]),
        low_pass_filter(values[:, 1]),
        low_pass_filter(values[:, 2]),
    )
    time_intervals = np.diff(timestamps).reshape(-1, 1)  # (N-1, 1)
    value_diffs = np.diff(values, axis=0)  # (N-1, 3)
    time_intervals[time_intervals == 0] = 1e-6
    derivatives = value_diffs / time_intervals
    derivatives = np.vstack([np.zeros((1, values.shape[1])), derivatives])
    return np.column_stack((timestamps, derivatives))


def calculate_height_from_airtime(airtime):
    return (9.81 * airtime**2) / 8


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


def calculate_total_movement(velocity, starttime, endtime, axis):
    axis_map = {"x": 1, "y": 2, "z": 3}
    axis_idx = axis_map.get(axis)
    timestamps = velocity[:, 0]
    values = np.abs(
        velocity[:, axis_idx]
    )  # Take absolute velocity fto account for direction

    # Find indices for the time range
    start_idx = np.abs(timestamps - starttime).argmin()
    end_idx = np.abs(timestamps - endtime).argmin()

    # Integrate using trapezoidal rule
    relevant_timestamps = timestamps[start_idx : end_idx + 1]
    relevant_values = values[start_idx : end_idx + 1]
    return np.trapz(relevant_values, relevant_timestamps)


def calculate_distance_traveled(lower_back_disp, starttime, endtime, axis):
    """
    Calculate the distance traveled along a specific axis using displacement data.
    """
    axis_map = {"x": 1, "y": 2, "z": 3}
    axis_idx = axis_map.get(axis)
    timestamps = lower_back_disp[:, 0]
    displacement = lower_back_disp[:, axis_idx]

    start_idx = np.abs(timestamps - starttime).argmin()
    end_idx = np.abs(timestamps - endtime).argmin()

    phase_displacement = displacement[start_idx : end_idx + 1]

    if axis_idx == 1:
        return max(phase_displacement)
    return max(phase_displacement) - min(phase_displacement)


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


def calculate_total_arm_movement(data):
    x = calculate_movement(data, "x", data[0][0], data[-1][0])
    y = calculate_movement(data, "y", data[0][0], data[-1][0])
    z = calculate_movement(data, "z", data[0][0], data[-1][0])
    return x + y + z


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


def calculate_landing_impact(thigh_jerk, starttime):
    # Extract timestamps and jerk components
    timestamps = thigh_jerk[:, 0]
    jerk_data = thigh_jerk[:, 1:]  # x, y, z columns

    # Find the indices corresponding to the landing phase
    start_idx = np.abs(timestamps - starttime).argmin() - 15
    end_idx = start_idx + 25

    # Extract the landing phase jerk data
    landing_jerk = jerk_data[start_idx : end_idx + 1, :]
    if landing_jerk.shape[0] < 2:  # Not enough data points to calculate metrics
        return [0, 0]

    # Compute magnitude of jerk (Euclidean norm)
    # jerk_magnitude = np.linalg.norm(landing_jerk, axis=1)

    # Return useful metrics
    peak_jerk = np.max(landing_jerk[:, 0])

    return peak_jerk


from scipy.signal import butter, filtfilt


def low_pass_filter(data, cutoff=2.0, fs=100, order=2):
    """Return filtfilt‑filtered data, but skip filtering when the vector is too short.

    Parameters
    ----------
    data : 1‑D NumPy array
    cutoff : float, cutoff frequency [Hz]
    fs : float, sampling rate [Hz]
    order : int, Butterworth order
    """
    if data is None or len(data) == 0:
        return data

    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype="low", analog=False)
    padlen = 3 * (max(len(a), len(b)) - 1)  # rule used by SciPy
    if len(data) <= padlen:
        return data  # not enough samples to filter safely

    return filtfilt(b, a, data)


# ------------------------------------------------------------------
#  Metric helpers with short‑signal protection
# ------------------------------------------------------------------


def calculate_max_knee_bend_accel(accel_data, starttime, endtime, apply_filter=False):
    """Max knee bend from accelerometer with optional filtering and safety guard."""
    # slice window
    ts = accel_data[:, 0]
    win = accel_data[(ts >= starttime) & (ts <= endtime), 1:3]  # ax, ay
    if win.shape[0] < 2:
        return 0

    ax, ay = win[:, 0], win[:, 1]
    if apply_filter and len(ax) > 9:  # padlen = 9 for order‑2
        ax, ay = low_pass_filter(ax), low_pass_filter(ay)

    pitch = np.degrees(np.arctan2(-ay, ax))
    return float(np.max(pitch))


def calculate_max_knee_bend_gyro(gyro_data, starttime, endtime, co=0):
    """Max knee bend from gyro with filtering guard."""
    win = gyro_data[(gyro_data[:, 0] >= starttime) & (gyro_data[:, 0] <= endtime)]
    if win.shape[0] < 2:
        return 0
    gz = win[:, 3]
    if co > 0 and len(gz) > 9:
        gz = low_pass_filter(gz, co, 100)
    return float(np.max(np.abs(gz)))


def calculate_combined_knee_bend(accel, gyro, t0, t1, co=1, alpha=0.68):
    a_ang = calculate_max_knee_bend_accel(accel, t0, t1, apply_filter=bool(co))
    g_ang = calculate_max_knee_bend_gyro(gyro, t0, t1, co)
    return alpha * g_ang + (1 - alpha) * a_ang
