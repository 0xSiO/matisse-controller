import visa
import queue

from .stabilization_thread import StabilizationThread
from pyvisa import VisaIOError
from warnings import warn


class Matisse:
    DEVICE_ID = 'USB0::0x17E7::0x0102::07-40-01::INSTR'

    def __init__(self):
        """Initialize VISA resource manager, connect to Matisse, clear any errors."""
        resource_manager = visa.ResourceManager()
        try:
            self.instrument = resource_manager.open_resource(self.DEVICE_ID)
            self.stabilization_thread = None
            self.query('ERROR:CLEAR')  # start with a clean slate
        except VisaIOError as ioerr:
            raise IOError("Can't reach Matisse. Make sure it's on and connected via USB.") from ioerr

    def query(self, command='', numeric_result=False, raise_on_error=True):
        """
        Send a command to the Matisse and return the response.

        :param command: the command to send
        :param numeric_result: whether to convert the second portion of the result to a float
        :param raise_on_error: whether to raise a Python error if Matisse error occurs
        :return: the response from the Matisse to the given command
        """
        try:
            result: str = self.instrument.query(command).strip()
        except VisaIOError as ioerr:
            raise IOError("Couldn't execute command. Check Matisse is on and connected via USB.") from ioerr

        if result.startswith('!ERROR'):
            if raise_on_error:
                err_codes = self.query('ERROR:CODE?')
                self.query('ERROR:CLEAR')
                raise RuntimeError("Error executing Matisse command '" + command + "' " + err_codes)
        elif numeric_result:
            result: float = float(result.split()[1])
        return result

    def bifi_wavelength(self) -> float:
        """Get the current position of the birefringent filter in terms of a wavelength, in nanometers."""
        return self.query('MOTBI:WL?', numeric_result=True)

    def wavemeter_wavelength(self) -> float:
        """Get the current wavelength of the laser in nanometers as read from the wavemeter."""
        # TODO: initialize IO connection to wavemeter
        raise NotImplementedError

    def get_refcell_pos(self) -> float:
        """Get the current position of the reference cell as a float value in [0, 1]"""
        return self.query('SCAN:NOW?', numeric_result=True)

    def set_refcell_pos(self, val: float):
        """Set the current position of the reference cell as a float value in [0, 1]"""
        return self.query(f"SCAN:NOW {val}")

    def stabilize_on(self, tolerance, delay=0.5):
        """Stabilize the wavelength of the laser with respect to the wavemeter measurement."""
        if self.stabilization_thread is not None and self.stabilization_thread.is_alive():
            warn('Already stabilizing laser. Call stabilize_off before trying to stabilize again.')
        else:
            self.stabilization_thread = StabilizationThread(self, tolerance, delay, queue.Queue())
            self.stabilization_thread.start()
            print(f"Stabilizing laser at {self.bifi_wavelength()} nm...")

    def stabilize_off(self):
        """Disable stabilization loop."""
        self.stabilization_thread.queue.put('stop')
