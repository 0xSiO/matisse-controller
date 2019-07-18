from serial import Serial, SerialException


class WaveMaster:
    # TODO: Make this configurable
    SERIAL_PORT = 'COM5'

    def __init__(self):
        try:
            self.serial = Serial(self.SERIAL_PORT)
        except SerialException as err:
            raise IOError("Couldn't open connection to wavemeter.") from err

    def open(self):
        self.serial.open()

    def close(self):
        self.serial.close()

    # TODO: Raise Python error on command error
    def query(self, command: str):
        if not self.serial.is_open:
            self.open()
        # Ensure a newline is at the end
        command = command.strip() + '\n\n'
        self.serial.write(command.encode())
        self.serial.flush()
        return self.serial.readline().strip().decode()

    def get_raw_value(self):
        return self.query('VAL?').split(',')[1].strip()

    def get_wavelength(self):
        raw_value = self.get_raw_value()
        # Keep trying until we get a number
        while raw_value == 'NO SIGNAL' or raw_value == 'MULTI-LINE':
            raw_value = self.get_raw_value()
        return float(raw_value)
