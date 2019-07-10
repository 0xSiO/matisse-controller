from serial import Serial, SerialException


class WaveMaster:
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

    def get_wavelength(self):
        return float(self.query('VAL?').split(',')[1])
