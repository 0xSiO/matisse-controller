import threading
import queue

import numpy as np
from pyvisa import ResourceManager, VisaIOError
from scipy.signal import savgol_filter, argrelextrema

from matisse.lock_correction_thread import LockCorrectionThread
from matisse.scans_plot import ScansPlot
from matisse.stabilization_thread import StabilizationThread
from wavemaster import WaveMaster


# TODO: Consider making a singleton instance
class Matisse:
    matisse_lock = threading.Lock()

    # How far to each side should we scan the BiFi?
    BIREFRINGENT_SCAN_RANGE = 300
    # How far apart should each point be spaced when measuring the diode power?
    BIREFRINGENT_SCAN_STEP = 3
    THIN_ETALON_SCAN_RANGE = 2000  # TODO: Decrease this, it takes too long
    THIN_ETALON_SCAN_STEP = 10

    # TODO: Confirm this parameter is ok to use, flank seems to default to 'left'
    THIN_ETALON_NUDGE = -75

    # How long to wait, in seconds, before giving up on locking the laser.
    LOCKING_TIMEOUT = 7.0

    BIREFRINGENT_FILTER_LOWER_LIMIT = 0
    BIREFRINGENT_FILTER_UPPER_LIMIT = 188096
    THIN_ETALON_LOWER_LIMIT = 0
    THIN_ETALON_UPPER_LIMIT = 45797
    PIEZO_ETALON_LOWER_LIMIT = -1
    PIEZO_ETALON_UPPER_LIMIT = 1
    REFERENCE_CELL_LOWER_LIMIT = 0
    REFERENCE_CELL_UPPER_LIMIT = 0.7
    SLOW_PIEZO_LOWER_LIMIT = 0
    SLOW_PIEZO_UPPER_LIMIT = 0.7

    MOTOR_STATUS_IDLE = 0x02

    def __init__(self, device_id: str, wavemeter_port: str):
        """
        Initialize VISA resource manager, connect to Matisse, clear any errors.

        Additionally, connect to the wavemeter and open up a plot to display results of BiFi/TE scans.
        """
        try:
            # TODO: Add access modifiers on all these instance variables
            self.instrument = ResourceManager().open_resource(device_id)
            self.target_wavelength = None
            self.stabilization_thread = None
            self.lock_correction_thread = None
            self.query('ERROR:CLEAR')  # start with a clean slate
            self.wavemeter = WaveMaster(wavemeter_port)
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
            with Matisse.matisse_lock:
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
        # TODO: self.optimize_piezo_etalon()
        print('All done.')

    def birefringent_filter_scan(self):
        """
        Initiate a scan of the birefringent filter, selecting the power maximum closest to the target wavelength.

        Additionally, plot the power data and motor position selection.
        """
        center_pos = int(self.query('MOTBI:POS?', numeric_result=True))
        lower_limit = center_pos - Matisse.BIREFRINGENT_SCAN_RANGE
        upper_limit = center_pos + Matisse.BIREFRINGENT_SCAN_RANGE
        assert (0 < lower_limit < Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT and 0 < upper_limit < Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT and lower_limit < upper_limit), \
            'Conditions for BiFi scan invalid. Motor position must be between ' + \
            f"{Matisse.BIREFRINGENT_SCAN_RANGE} and {Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT - Matisse.BIREFRINGENT_SCAN_RANGE}"
        positions = np.array(range(lower_limit, upper_limit, Matisse.BIREFRINGENT_SCAN_STEP))
        voltages = np.array([])
        print('Starting BiFi scan... ', end='')
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
        if self.target_wavelength is None:
            self.target_wavelength = self.wavemeter_wavelength()
        wavelength_differences = np.array([])
        for pos in positions[maxima]:
            self.set_bifi_motor_pos(pos)
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[maxima][np.argmin(wavelength_differences)]
        print(wavelength_differences)
        self.set_bifi_motor_pos(best_pos)
        print('Done.')

        # TODO: When plot window is closed, this doesn't just become None.
        if self.scans_plot is None:
            self.scans_plot = ScansPlot()
        self.scans_plot.plot_birefringent_scan(positions, voltages, smoothed_data)
        self.scans_plot.plot_birefringent_selection(best_pos)
        self.scans_plot.plot_birefringent_maxima(positions[maxima], smoothed_data[maxima])
        self.scans_plot.add_bifi_scan_legend()

    def set_bifi_motor_pos(self, pos: int):
        assert 0 < pos < Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT, 'Target motor position out of range.'
        # Wait for motor to be ready to accept commands
        while not self.bifi_motor_status() == Matisse.MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTBI:POS {pos}")
        # Wait for motor to finish movement
        while not self.bifi_motor_status() == Matisse.MOTOR_STATUS_IDLE:
            pass

    def set_bifi_wavelength(self, value: float):
        # TODO: Figure out min and max values
        assert 720 < value < 800, 'Target wavelength out of range.'
        # Wait for motor to be ready to accept commands
        while not self.bifi_motor_status() == Matisse.MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTBI:WAVELENGTH {value}")
        # Wait for motor to finish movement
        while not self.bifi_motor_status() == Matisse.MOTOR_STATUS_IDLE:
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
        lower_limit = center_pos - Matisse.THIN_ETALON_SCAN_RANGE
        upper_limit = center_pos + Matisse.THIN_ETALON_SCAN_RANGE
        assert (0 < lower_limit < Matisse.THIN_ETALON_UPPER_LIMIT and 0 < upper_limit < Matisse.THIN_ETALON_UPPER_LIMIT and lower_limit < upper_limit), \
            'Conditions for thin etalon scan invalid. Motor position must be between ' + \
            f"{Matisse.THIN_ETALON_SCAN_RANGE} and {Matisse.THIN_ETALON_UPPER_LIMIT - Matisse.THIN_ETALON_SCAN_RANGE}"
        positions = np.array(range(lower_limit, upper_limit, Matisse.THIN_ETALON_SCAN_STEP))
        voltages = np.array([])
        print('Starting thin etalon scan... ', end='')
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
        if self.target_wavelength is None:
            self.target_wavelength = self.wavemeter_wavelength()
        wavelength_differences = np.array([])
        for pos in positions[minima]:
            self.set_thin_etalon_motor_pos(pos)
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[minima][np.argmin(wavelength_differences)] + Matisse.THIN_ETALON_NUDGE
        print(wavelength_differences)
        self.set_thin_etalon_motor_pos(best_pos)
        print('Done.')

        if self.scans_plot is None:
            self.scans_plot = ScansPlot()
        self.scans_plot.plot_thin_etalon_scan(positions, voltages, smoothed_data)
        self.scans_plot.plot_thin_etalon_selection(best_pos)
        self.scans_plot.plot_thin_etalon_minima(positions[minima], smoothed_data[minima])
        self.scans_plot.add_thin_etalon_scan_legend()

    def set_thin_etalon_motor_pos(self, pos: int):
        assert (0 < pos < Matisse.THIN_ETALON_UPPER_LIMIT), 'Target motor position out of range.'
        # Wait for motor to be ready to accept commands
        while not self.thin_etalon_motor_status() == Matisse.MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTTE:POS {pos}")
        # Wait for motor to finish movement
        while not self.thin_etalon_motor_status() == Matisse.MOTOR_STATUS_IDLE:
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

    def set_slow_piezo_control(self, enable: bool):
        self.query(f"SLOWPIEZO:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def set_fast_piezo_control(self, enable: bool):
        self.query(f"FASTPIEZO:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def set_thin_etalon_control(self, enable: bool):
        self.query(f"THINETALON:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def set_piezo_etalon_control(self, enable: bool):
        self.query(f"PIEZOETALON:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def all_control_loops_on(self):
        """
        Returns whether the slow piezo, thin etalon, piezo etalon, and fast piezo all have their control loops enabled.
        """
        return ('RUN' in self.query('SLOWPIEZO:CONTROLSTATUS?')
                and 'RUN' in self.query('THINETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('PIEZOETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('FASTPIEZO:CONTROLSTATUS?'))

    def fast_piezo_locked(self):
        return 'TRUE' in self.query('FASTPIEZO:LOCK?')

    def stabilize_on(self, tolerance=0.001, delay=0.5):
        """
        Enable stabilization using the reference cell to keep the wavelength constant.

        Starts a StabilizationThread as a daemon for this purpose. To stop stabilizing and unlock the laser, call
        stabilize_off.

        :param tolerance: how much drift you can tolerate in the wavelength, in nanometers
        :param delay: how many seconds to wait in between each correction of the reference cell
        """
        if self.is_stabilizing():
            print('WARNING: Already stabilizing laser. Call stabilize_off before trying to stabilize again.')
        else:
            self.stabilization_thread = StabilizationThread(self, tolerance, delay, queue.Queue())

            if self.target_wavelength is None:
                self.target_wavelength = self.wavemeter_wavelength()
            print(f"Stabilizing laser at {self.target_wavelength} nm...")
            self.stabilization_thread.start()

    def stabilize_off(self):
        """Disable stabilization loop and unlock the laser. This stops the StabilizationThread."""
        if self.is_stabilizing():
            print('Stopping stabilization thread.')
            self.stabilization_thread.messages.put('stop')
            self.stabilization_thread.join()
            print('Stabilization thread has been stopped.')
        else:
            print('WARNING: Stabilization thread is not running.')

    def is_stabilizing(self):
        return self.stabilization_thread is not None and self.stabilization_thread.is_alive()

    def is_any_limit_reached(self):
        """Returns true if the RefCell, slow piezo, or piezo etalon are very close to one of their limits."""

        current_refcell_pos = self.query('SCAN:NOW?', numeric_result=True)
        current_slow_pz_pos = self.query('SLOWPIEZO:NOW?', numeric_result=True)
        current_pz_eta_pos = self.query('PIEZOETALON:BASELINE?', numeric_result=True)

        offset = 0.05
        return not (self.REFERENCE_CELL_LOWER_LIMIT + offset < current_refcell_pos < self.REFERENCE_CELL_UPPER_LIMIT - offset
               and self.SLOW_PIEZO_LOWER_LIMIT + offset < current_slow_pz_pos < self.SLOW_PIEZO_UPPER_LIMIT - offset
               and self.PIEZO_ETALON_LOWER_LIMIT + offset < current_pz_eta_pos < self.PIEZO_ETALON_UPPER_LIMIT - offset)

    def start_laser_lock_correction(self):
        if self.is_lock_correction_on():
            print('WARNING: Lock correction is already running.')
        else:
            print('Starting laser lock.')
            self.lock_correction_thread = LockCorrectionThread(self, Matisse.LOCKING_TIMEOUT, queue.Queue())
            self.lock_correction_thread.start()

    def stop_laser_lock_correction(self):
        if self.is_lock_correction_on():
            self.lock_correction_thread.messages.put('stop')
            self.lock_correction_thread.join()
        else:
            print('WARNING: laser is not locked.')

    def is_lock_correction_on(self):
        return self.lock_correction_thread is not None and self.lock_correction_thread.is_alive()
