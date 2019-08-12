import threading

from serial import Serial, SerialException


# TODO: Give up on reading wavemeter display if it takes too long
class WaveMaster:
    """An interface to serial port communication with the Coherent WaveMaster wavemeter."""

    wavemeter_lock = threading.Lock()

    def __init__(self, port: str):
        try:
            self.serial = Serial(port)
        except SerialException as err:
            raise IOError("Couldn't open connection to wavemeter.") from err

    def __del__(self):
        self.serial.close()

    def query(self, command: str) -> str:
        """
        Wait to acquire an exclusive lock on the serial port, then send a command to the wavemeter.

        Parameters
        ----------
        command : str
            the command to send to the wavemeter

        Returns
        -------
        str
            the response from the wavemeter to the given command
        """
        with WaveMaster.wavemeter_lock:
            try:
                if not self.serial.is_open:
                    self.serial.open()
                # Ensure a newline is at the end
                command = command.strip() + '\n\n'
                self.serial.write(command.encode())
                self.serial.flush()
                return self.serial.readline().strip().decode()
            except SerialException as err:
                raise IOError("Error communicating with wavemeter serial port.") from err

    def get_raw_value(self) -> str:
        """
        Returns
        -------
        str
            the raw output from the wavemeter display
        """
        return self.query('VAL?').split(',')[1].strip()

    def get_wavelength(self) -> float:
        """
        Returns
        -------
        float
            a measurement from the wavemeter

        Notes
        -----
        Blocks the calling thread until a number is received.
        """
        raw_value = self.get_raw_value()
        # Keep trying until we get a number
        while raw_value == 'NO SIGNAL' or raw_value == 'MULTI-LINE':
            raw_value = self.get_raw_value()
        return float(raw_value)
