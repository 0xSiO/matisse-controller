from .stabilization_thread import StabilizationThread
from wavemaster import WaveMaster
from pyvisa import ResourceManager, VisaIOError
from queue import Queue
from warnings import warn


class Matisse:
    # TODO: Make this configurable?
    DEVICE_ID = 'USB0::0x17E7::0x0102::07-40-01::INSTR'
    # How far to each side should we scan the BiFi?
    BIREFRINGENT_SCAN_LIMIT = 4000

    def __init__(self):
        """Initialize VISA resource manager, connect to Matisse, clear any errors."""
        try:
            self.instrument = ResourceManager().open_resource(self.DEVICE_ID)
            self.target_wavelength = None
            self.stabilization_thread = None
            self.query('ERROR:CLEAR')  # start with a clean slate
            self.wavemeter = WaveMaster()
        except VisaIOError as ioerr:
            raise IOError("Can't reach Matisse. Make sure it's on and connected via USB.") from ioerr

    # TODO: Make this the definitive control mechanism to start the wavelength selection process
    def set_wavelength(self, wavelength: float):
        self.target_wavelength = wavelength

    def query(self, command: str, numeric_result=False, raise_on_error=True):
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

    def wavemeter_wavelength(self) -> float:
        """Get the current wavelength of the laser in nanometers as read from the wavemeter."""
        return self.wavemeter.get_wavelength()

    def birefringent_filter_scan(self):
        current_bifi_pos = self.query('MOTBI:POS?', numeric_result=True)
        lower_limit = current_bifi_pos - self.BIREFRINGENT_SCAN_LIMIT
        upper_limit = current_bifi_pos + self.BIREFRINGENT_SCAN_LIMIT
        # TODO: Scan the motor and grab diode power data

    def get_refcell_pos(self) -> float:
        """Get the current position of the reference cell as a float value in [0, 1]"""
        return self.query('SCAN:NOW?', numeric_result=True)

    def set_refcell_pos(self, val: float):
        """Set the current position of the reference cell as a float value in [0, 1]"""
        return self.query(f"SCAN:NOW {val}")

    def lock_slow_piezo(self):
        self.query('SLOWPIEZO:CONTROLSTATUS RUN')

    def unlock_slow_piezo(self):
        self.query('SLOWPIEZO:CONTROLSTATUS STOP')

    def lock_fast_piezo(self):
        self.query('FASTPIEZO:CONTROLSTATUS RUN')

    def unlock_fast_piezo(self):
        self.query('FASTPIEZO:CONTROLSTATUS STOP')

    def lock_thin_etalon(self):
        self.query('THINETALON:CONTROLSTATUS RUN')

    def unlock_thin_etalon(self):
        self.query('THINETALON:CONTROLSTATUS STOP')

    def lock_piezo_etalon(self):
        self.query('PIEZOETALON:CONTROLSTATUS RUN')

    def unlock_piezo_etalon(self):
        self.query('PIEZOETALON:CONTROLSTATUS STOP')

    def assert_locked(self):
        assert ('RUN' in self.query('SLOWPIEZO:CONTROLSTATUS?')
                and 'RUN' in self.query('THINETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('PIEZOETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('FASTPIEZO:CONTROLSTATUS?')), \
            'Unable to obtain laser lock. Manual correction needed.'

    def stabilize_on(self, wavelength, tolerance, delay=0.5):
        """Stabilize the wavelength of the laser with respect to the wavemeter measurement."""
        if self.stabilization_thread is not None and self.stabilization_thread.is_alive():
            warn('Already stabilizing laser. Call stabilize_off before trying to stabilize again.')
        else:
            # Message queue has a maxsize of 1 since we'll just tell it to stop later
            self.stabilization_thread = StabilizationThread(self, wavelength, tolerance, delay, Queue(maxsize=1))
            # Lock the laser and begin stabilization
            print('Locking laser...')
            self.lock_slow_piezo()
            self.lock_thin_etalon()
            self.lock_piezo_etalon()
            self.lock_fast_piezo()
            self.assert_locked()
            # TODO: Note the wavelength given by the user to stabilize.
            print(f"Stabilizing laser...")
            self.stabilization_thread.start()

    def stabilize_off(self):
        """Disable stabilization loop."""
        if self.stabilization_thread is not None and self.stabilization_thread.is_alive():
            self.stabilization_thread.messages.put('stop')
            print('Stopping stabilization thread...')
            self.stabilization_thread.join()
            print('Unlocking laser...')
            self.unlock_fast_piezo()
            self.unlock_piezo_etalon()
            self.unlock_thin_etalon()
            self.unlock_slow_piezo()
            print('Done.')
        else:
            warn('Stabilization thread is not running.')
