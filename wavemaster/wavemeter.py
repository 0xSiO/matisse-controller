from serial import Serial


class Wavemeter:
    def __init__(self, port_name: str):
        self.serial = Serial(port_name)

    def open(self):
        self.serial.open()

    def close(self):
        self.serial.close()

    def query(self, command):
        if not self.serial.is_open:
            self.open()
        # run command, return result
