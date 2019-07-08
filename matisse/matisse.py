import visa
from pyvisa import VisaIOError


class Matisse:
    DEVICE_ID = 'USB0::0x17E7::0x0102::07-40-01::INSTR'

    def __init__(self):
        """Initialize VISA resource manager and connect to Matisse."""
        resource_manager = visa.ResourceManager()
        try:
            self.instrument = resource_manager.open_resource(self.DEVICE_ID)
            self.query('ERROR:CLEAR')  # start with a clean slate
        except VisaIOError as ioerr:
            raise IOError("Can't reach Matisse. Make sure it's on and connected via USB.") from ioerr

    def query(self, command='', numeric_result=False, raise_on_error=True):
        """
        Send a command to the Matisse and return the response, optionally converting to a floating-point value.
        Will optionally raise Python error if a Matisse error occurs.

        :param command: the command to send
        :param numeric_result: whether to convert the second portion of the result to a float
        :param raise_on_error: whether to raise Matisse errors in Python runtime
        :return: the response from the Matisse to the given command
        """
        result: str = self.instrument.query(command).strip()
        if result.startswith('!ERROR'):
            if raise_on_error:
                raise RuntimeError("Error executing Matisse command '" + command + "' " + self.query('ERROR:CODE?'))
        elif numeric_result:
            result: float = float(result.split()[1])
        return result
