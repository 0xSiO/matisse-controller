import threading

from serial import Serial, SerialException


class WaveMaster:
    wavemeter_lock = threading.Lock()
    PRECISION = 3

    def __init__(self, port: str):
        try:
            self.serial = Serial(port)
        except SerialException as err:
            raise IOError("Couldn't open connection to wavemeter.") from err

    def open(self):
        self.serial.open()

    def close(self):
        self.serial.close()

    def query(self, command: str):
        with WaveMaster.wavemeter_lock:
            try:
                if not self.serial.is_open:
                    self.open()
                # Ensure a newline is at the end
                command = command.strip() + '\n\n'
                self.serial.write(command.encode())
                self.serial.flush()
                return self.serial.readline().strip().decode()
            except SerialException as err:
                raise IOError("Error communicating with wavemeter serial port.") from err

    def get_raw_value(self):
        return self.query('VAL?').split(',')[1].strip()

    def get_wavelength(self):
        raw_value = self.get_raw_value()
        # Keep trying until we get a number
        while raw_value == 'NO SIGNAL' or raw_value == 'MULTI-LINE':
            raw_value = self.get_raw_value()
        return float(raw_value)
