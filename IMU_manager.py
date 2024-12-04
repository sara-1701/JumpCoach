from mbientlab.metawear import MetaWear, libmetawear, cbindings
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import numpy as np
from time import time


class SensorCallback:
    def __init__(self, data):
        self.data = data
        self.accel_callback = cbindings.FnVoid_VoidP_DataP(self.handle_accel_data)
        self.gyro_callback = cbindings.FnVoid_VoidP_DataP(self.handle_gyro_data)

    def handle_accel_data(self, context, data):
        accel_value = cbindings.CartesianFloat.from_address(data.contents.value)
        current_time = time()
        self.data["accel"] = np.append(
            self.data["accel"],
            [[current_time, accel_value.x, accel_value.y, accel_value.z]],
            axis=0,
        )

    def handle_gyro_data(self, context, data):
        gyro_value = cbindings.CartesianFloat.from_address(data.contents.value)
        current_time = time()
        self.data["gyro"] = np.append(
            self.data["gyro"],
            [[current_time, gyro_value.x, gyro_value.y, gyro_value.z]],
            axis=0,
        )


class IMUDataThread(QThread):
    connection_status = pyqtSignal(str, bool)  # Signal for connection status

    def __init__(self, address, data):
        super().__init__()
        self.address = address
        self.device = MetaWear(self.address)
        self.running = True
        self.data = data
        self.data[self.address] = {
            "accel": np.empty((0, 4), dtype=float),
            "gyro": np.empty((0, 4), dtype=float),
        }
        self.callback = SensorCallback(self.data[self.address])

    def run(self):
        if self.connect_device() and self.configure_device():
            self.connection_status.emit(self.address, True)
        else:
            self.connection_status.emit(self.address, False)
            return

    def connect_device(self, max_retries=5):
        attempts = 0
        while not self.device.is_connected and attempts < max_retries:
            attempts += 1
            try:
                self.device.connect()
            except Exception as e:
                print(f"Attempt {attempts} failed for {self.address}: {e}")

        if self.device.is_connected:
            print(f"Connected to {self.address} on attempt {attempts}.")
            return True
        else:
            print(f"Failed to connect to {self.address} after {max_retries} attempts.")
            return False

    def configure_device(self):
        try:
            # Configure accelerometer
            libmetawear.mbl_mw_acc_set_odr(self.device.board, 100.0)
            libmetawear.mbl_mw_acc_set_range(self.device.board, 6.0)
            libmetawear.mbl_mw_acc_write_acceleration_config(self.device.board)
            acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(
                self.device.board
            )

            # Configure gyroscope
            libmetawear.mbl_mw_gyro_bmi160_set_odr(
                self.device.board, cbindings.GyroBoschOdr._50Hz
            )
            libmetawear.mbl_mw_gyro_bmi160_set_range(
                self.device.board, cbindings.GyroBoschRange._1000dps
            )
            libmetawear.mbl_mw_gyro_bmi160_write_config(self.device.board)
            gyro_signal = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(
                self.device.board
            )

            # Subscribe to signals
            libmetawear.mbl_mw_datasignal_subscribe(
                gyro_signal, None, self.callback.gyro_callback
            )
            libmetawear.mbl_mw_datasignal_subscribe(
                acc_signal, None, self.callback.accel_callback
            )

            # Start data sampling
            libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)
            libmetawear.mbl_mw_acc_start(self.device.board)
            libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(self.device.board)
            libmetawear.mbl_mw_gyro_bmi160_start(self.device.board)
            print(f"Configuration succeeded for {self.address}")
            return True

        except Exception as e:
            print(f"Configuration failed for {self.address}: {e}")
            self.connection_status.emit(self.address, False)
            return False

    def stop(self):
        self.running = False
        self.device.disconnect()
