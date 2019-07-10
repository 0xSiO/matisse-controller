from serial import Serial


class Wavemeter:
    SERIAL_PORT = 'COM4'

    def __init__(self):
        self.serial = Serial(self.SERIAL_PORT)

    def open(self):
        self.serial.open()

    def close(self):
        self.serial.close()

    def query(self, command: str):
        if not self.serial.is_open:
            self.open()
        # Ensure a newline is at the end
        command = command.strip() + '\n'
        self.serial.write(command.encode())
        return self.serial.read_all().strip().decode()

    def get_wavelength(self):
        return float(self.query('VAL?').split(',')[1])
