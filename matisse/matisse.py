from queue import Queue
from warnings import warn  # TODO: Tag warning messages in log, like "WARNING: ..."

import numpy as np
from pyvisa import ResourceManager, VisaIOError
from scipy.signal import savgol_filter, argrelextrema

from wavemaster import WaveMaster
from .scans_plot import ScansPlot
from .stabilization_thread import StabilizationThread


class Matisse:
    # TODO: Make this configurable
    DEVICE_ID = 'USB0::0x17E7::0x0102::07-40-01::INSTR'
    # How far to each side should we scan the BiFi?
    BIREFRINGENT_SCAN_RANGE = 300
    # How far apart should each point be spaced when measuring the diode power?
    BIREFRINGENT_SCAN_STEP = 3
    THIN_ETALON_SCAN_RANGE = 2000
    THIN_ETALON_SCAN_STEP = 10

    MOTOR_STATUS_IDLE = 0x02

    def __init__(self):
        """
        Initialize VISA resource manager, connect to Matisse, clear any errors.

        Additionally, connect to the wavemeter and open up a plot to display results of BiFi/TE scans.
        """
        try:
            # TODO: Add access modifiers on all these instance variables
            self.instrument = ResourceManager().open_resource(self.DEVICE_ID)
            self.target_wavelength = None
            self.stabilization_thread = None
            self.query('ERROR:CLEAR')  # start with a clean slate
            self.wavemeter = WaveMaster()
            self.scans_plot = None
        except VisaIOError as ioerr:
            raise IOError("Can't reach Matisse. Make sure it's on and connected via USB.") from ioerr

    def query(self, command: str, numeric_result=False, raise_on_error=True):
        """
        Send a command to the Matisse and return the response.

        Note that some commands (like setting the position of a stepper motor) take additional time to execute, so do
        not assume the command has finished executing just because the query returns "OK".

        This doesn't raise errors if the error occurred in the controller for a specific component of the Matisse, like
        the birefringent filter motor, for example. That motor has a separate status register with error information
        that can be queried and cleared separately.

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
        """:return: the wavelength (in nanometers) as measured by the wavemeter"""
        return self.wavemeter.get_wavelength()

    # TODO: Make this the definitive control mechanism to start the wavelength selection process
    def set_wavelength(self, wavelength: float):
        """
        Configure the Matisse to output a given wavelength.

        This is the process I'll follow:
        1. Set approx. wavelength using BiFi. This is good to about +-1 nm.
        2. Scan the BiFi back and forth and measure the total laser power at each point. Power looks like upside-down
           parabolas.
        3. Find all local maxima of the laser power data. Move the BiFi to the maximum that's closest to the desired
           wavelength.
        4. Scan the thin etalon back and forth and measure the thin etalon reflex at each point.
        5. Find all local minima of the reflex data. Move the TE to the minimum that's closest to the desired
           wavelength.
        6. Shift the TE to the left or right a little bit. We want to be on the "flank" of the chosen parabola.
        7. Adjust the piezo etalon until desired wavelength is reached.

        :param wavelength: the desired wavelength
        """
        del self.scans_plot
        self.scans_plot = ScansPlot()
        self.target_wavelength = wavelength
        print(f"Setting BiFi to ~{wavelength} nm... ", end='')
        self.set_bifi_wavelength(wavelength)
        print('Done.')
        self.birefringent_filter_scan()
        self.thin_etalon_scan()
        # TODO: piezo etalon
        print('All done.')

    def birefringent_filter_scan(self):
        """
        Initiate a scan of the birefringent filter, selecting the power maximum closest to the target wavelength.

        Additionally, plot the power data and motor position selection.
        """
        center_pos = int(self.query('MOTBI:POS?', numeric_result=True))
        lower_limit = center_pos - self.BIREFRINGENT_SCAN_RANGE
        upper_limit = center_pos + self.BIREFRINGENT_SCAN_RANGE
        max_pos = int(self.query('MOTBI:MAX?', numeric_result=True))
        assert (0 < lower_limit < max_pos and 0 < upper_limit < max_pos and lower_limit < upper_limit), \
            'Conditions for BiFi scan invalid. Motor position must be between ' + \
            f"{self.BIREFRINGENT_SCAN_RANGE} and {max_pos - self.BIREFRINGENT_SCAN_RANGE}"
        positions = np.array(range(lower_limit, upper_limit, self.BIREFRINGENT_SCAN_STEP))
        voltages = np.array([])
        print('Starting BiFi scan... ', end='')
        # TODO: If this becomes a performance bottleneck, do some pre-allocation or something
        for pos in positions:
            self.set_bifi_motor_pos(pos)
            voltages = np.append(voltages, self.query('DPOW:DC?', numeric_result=True))
        self.set_bifi_motor_pos(center_pos)  # return back to where we started, just in case something goes wrong
        print('Done.')

        print('Analyzing scan data... ', end='')
        # Smooth out the data and find extrema
        smoothed_data = savgol_filter(voltages, window_length=31, polyorder=3)
        maxima = argrelextrema(smoothed_data, np.greater, order=5)

        # Find the position of the extremum closest to the target wavelength
        wavelength_differences = np.array([])
        for pos in positions[maxima]:
            self.set_bifi_motor_pos(pos)
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[maxima][np.argmin(wavelength_differences)]
        print(wavelength_differences)
        self.set_bifi_motor_pos(best_pos)
        print('Done.')

        if self.scans_plot is None:
            self.scans_plot = ScansPlot()
        self.scans_plot.plot_birefringent_scan(positions, voltages, smoothed_data)
        self.scans_plot.plot_birefringent_selection(best_pos)
        self.scans_plot.plot_birefringent_maxima(positions[maxima], smoothed_data[maxima])
        self.scans_plot.add_bifi_scan_legend()

    def set_bifi_motor_pos(self, pos: int):
        assert 0 < pos < self.query('MOTBI:MAX?', numeric_result=True), 'Target motor position out of range.'
        # Wait for motor to be ready to accept commands
        while not self.bifi_motor_status() == self.MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTBI:POS {pos}")
        # Wait for motor to finish movement
        while not self.bifi_motor_status() == self.MOTOR_STATUS_IDLE:
            pass

    def set_bifi_wavelength(self, value: float):
        # TODO: Figure out min and max values
        assert 720 < value < 800, 'Target wavelength out of range.'
        # Wait for motor to be ready to accept commands
        while not self.bifi_motor_status() == self.MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTBI:WAVELENGTH {value}")
        # Wait for motor to finish movement
        while not self.bifi_motor_status() == self.MOTOR_STATUS_IDLE:
            pass

    def bifi_motor_status(self):
        """Return the last 8 bits of the BiFi motor status."""
        return int(self.query('MOTBI:STATUS?', numeric_result=True)) & 0b000000011111111

    def thin_etalon_scan(self):
        """
        Initiate a scan of the thin etalon, selecting the reflex minimum closest to the target wavelength.

        Nudges the motor position a little bit away from the minimum to ensure good locking later.
        Additionally, plot the reflex data and motor position selection.
        """
        center_pos = int(self.query('MOTTE:POS?', numeric_result=True))
        lower_limit = center_pos - self.THIN_ETALON_SCAN_RANGE
        upper_limit = center_pos + self.THIN_ETALON_SCAN_RANGE
        max_pos = int(self.query('MOTTE:MAX?', numeric_result=True))
        assert (0 < lower_limit < max_pos and 0 < upper_limit < max_pos and lower_limit < upper_limit), \
            'Conditions for thin etalon scan invalid. Motor position must be between ' + \
            f"{self.THIN_ETALON_SCAN_RANGE} and {max_pos - self.THIN_ETALON_SCAN_RANGE}"
        positions = np.array(range(lower_limit, upper_limit, self.THIN_ETALON_SCAN_STEP))
        voltages = np.array([])
        print('Starting thin etalon scan... ', end='')
        # TODO: If this becomes a performance bottleneck, do some pre-allocation or something
        for pos in positions:
            self.set_thin_etalon_motor_pos(pos)
            voltages = np.append(voltages, self.query('TE:DC?', numeric_result=True))
        self.set_thin_etalon_motor_pos(center_pos)  # return back to where we started, just in case something goes wrong
        print('Done.')

        print('Analyzing scan data... ', end='')
        # Smooth out the data and find extrema
        smoothed_data = savgol_filter(voltages, window_length=41, polyorder=3)
        minima = argrelextrema(smoothed_data, np.less, order=5)

        # Find the position of the extremum closest to the target wavelength
        wavelength_differences = np.array([])
        for pos in positions[minima]:
            self.set_thin_etalon_motor_pos(pos)
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[minima][np.argmin(wavelength_differences)]
        print(wavelength_differences)
        self.set_thin_etalon_motor_pos(best_pos)
        print('Done.')

        if self.scans_plot is None:
            self.scans_plot = ScansPlot()
        self.scans_plot.plot_thin_etalon_scan(positions, voltages, smoothed_data)
        self.scans_plot.plot_thin_etalon_selection(best_pos)
        self.scans_plot.plot_thin_etalon_minima(positions[minima], smoothed_data[minima])
        self.scans_plot.add_thin_etalon_scan_legend()
        # TODO: Small nudge

    def set_thin_etalon_motor_pos(self, pos: int):
        assert (0 < pos < self.query('MOTTE:MAX?', numeric_result=True)), 'Target motor position out of range.'
        # Wait for motor to be ready to accept commands
        while not self.thin_etalon_motor_status() == self.MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTTE:POS {pos}")
        # Wait for motor to finish movement
        while not self.thin_etalon_motor_status() == self.MOTOR_STATUS_IDLE:
            pass

    def thin_etalon_motor_status(self):
        """Return the last 8 bits of the TE motor status."""
        return int(self.query('MOTTE:STATUS?', numeric_result=True)) & 0b000000011111111

    def optimize_piezo_etalon(self):
        # TODO: Just use a binary search method to pick the right value?
        raise NotImplementedError

    def get_refcell_pos(self) -> float:
        """:return: the current position of the reference cell as a float value in [0, 1]"""
        return self.query('SCAN:NOW?', numeric_result=True)

    def set_refcell_pos(self, val: float):
        """Set the current position of the reference cell as a float value in [0, 1]"""
        return self.query(f"SCAN:NOW {val}")

    # TODO: Clean up these lock/unlock methods if they're going to remain one-liners
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
        """
        Assert that the slow piezo, thin etalon, piezo etalon, and fast piezo all have their control loops enabled.

        Throw an error if this condition is not met.
        """
        assert ('RUN' in self.query('SLOWPIEZO:CONTROLSTATUS?')
                and 'RUN' in self.query('THINETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('PIEZOETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('FASTPIEZO:CONTROLSTATUS?')), \
            'Unable to obtain laser lock. Manual correction needed.'

    def stabilize_on(self, tolerance=0.002, delay=0.5):
        """
        Lock the laser and enable stabilization using the reference cell to keep the wavelength constant.

        Starts a StabilizationThread as a daemon for this purpose. To stop stabilizing and unlock the laser, call
        stabilize_off.

        :param tolerance: how much drift you can tolerate in the wavelength, in nanometers
        :param delay: how many seconds to wait in between each correction of the reference cell
        """
        if self.stabilization_thread is not None and self.stabilization_thread.is_alive():
            warn('Already stabilizing laser. Call stabilize_off before trying to stabilize again.')
        else:
            # Message queue has a maxsize of 1 since we'll just tell it to stop later
            self.stabilization_thread = StabilizationThread(self, tolerance, delay, Queue(maxsize=1))
            # Lock the laser and begin stabilization
            print('Locking laser...')
            self.lock_slow_piezo()
            self.lock_thin_etalon()
            self.lock_piezo_etalon()
            self.lock_fast_piezo()
            self.assert_locked()
            # TODO: Note the wavelength given by the user to stabilize.
            print(f"Stabilizing laser at {self.target_wavelength} nm...")
            self.stabilization_thread.start()

    def stabilize_off(self):
        """Disable stabilization loop and unlock the laser. This stops the StabilizationThread."""
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
