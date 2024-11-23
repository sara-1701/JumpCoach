from mbientlab.metawear import MetaWear, libmetawear, cbindings
from collections import deque
from PyQt5.QtCore import QThread, pyqtSignal
from time import time


class SensorCallback:
    def __init__(self, acc_deque, gyro_deque):
        self.acc_deque = acc_deque
        self.gyro_deque = gyro_deque
        self.accel_callback = cbindings.FnVoid_VoidP_DataP(self.handle_accel_data)
        self.gyro_callback = cbindings.FnVoid_VoidP_DataP(self.handle_gyro_data)

    def handle_accel_data(self, context, data):
        accel_value = cbindings.CartesianFloat.from_address(data.contents.value)
        self.acc_deque.append([accel_value.x, accel_value.y, accel_value.z])

    def handle_gyro_data(self, context, data):
        gyro_value = cbindings.CartesianFloat.from_address(data.contents.value)
        self.gyro_deque.append([gyro_value.x, gyro_value.y, gyro_value.z])


class IMUDataThread(QThread):
    update_data = pyqtSignal(str, list, list)  # Signal to update GUI plots
    connection_status = pyqtSignal(str, bool)  # Signal for connection status

    def __init__(self, address, data_queues):
        super().__init__()
        self.address = address
        self.device = MetaWear(self.address)
        self.running = True
        self.data_queues = data_queues

    def run(self):
        connected = False
        max_retries = 5

        # Retry logic for connecting to the IMU
        for attempt in range(1, max_retries + 1):
            try:
                print(
                    f"Attempting to connect to {self.address} (Attempt {attempt}/{max_retries})..."
                )
                self.device.connect()
                if self.device.is_connected:
                    print(f"Connected to {self.address} on attempt {attempt}.")
                    connected = True
                    break
            except Exception as e:
                print(f"Attempt {attempt} failed for {self.address}: {e}")

        if not connected:
            print(f"Failed to connect to {self.address} after {max_retries} attempts.")
            self.connection_status.emit(self.address, False)
            return

        # Set up data queues and callback
        acc_deque = deque(maxlen=200)
        gyro_deque = deque(maxlen=200)
        self.data_queues[self.address] = (acc_deque, gyro_deque)

        callback = SensorCallback(acc_deque, gyro_deque)

        try:
            # Configure accelerometer
            libmetawear.mbl_mw_acc_set_odr(self.device.board, 50.0)
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

            # Subscribe to gyro and accelerometer
            libmetawear.mbl_mw_datasignal_subscribe(
                gyro_signal, None, callback.gyro_callback
            )
            libmetawear.mbl_mw_datasignal_subscribe(
                acc_signal, None, callback.accel_callback
            )

            # Start sampling
            libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)
            libmetawear.mbl_mw_acc_start(self.device.board)
            libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(self.device.board)
            libmetawear.mbl_mw_gyro_bmi160_start(self.device.board)

            self.connection_status.emit(self.address, True)

            # Continuously emit updated data to the GUI
            while self.running:
                start_time = time()  # Track when the loop starts
                try:
                    self.update_data.emit(
                        self.address, list(acc_deque), list(gyro_deque)
                    )
                except Exception as e:
                    print(f"Error in thread for {self.address}: {e}")

                elapsed = time() - start_time
                sleep_time = max(
                    0, 0.02 - elapsed
                )  # Maintain 50 Hz (1/50 = 0.02 seconds)
                self.msleep(int(sleep_time * 1000))  # Convert to milliseconds

        except Exception as e:
            print(f"Error collecting data from {self.address}: {e}")
        finally:
            self.device.disconnect()

    def stop(self):
        self.running = False
