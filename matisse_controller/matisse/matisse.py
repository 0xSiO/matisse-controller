import queue
import threading
import time

import numpy as np
from pyvisa import ResourceManager, VisaIOError
from scipy.signal import savgol_filter, argrelextrema

import matisse_controller.config as cfg
from matisse_controller.matisse.constants import *
from matisse_controller.matisse.control_loops_on import ControlLoopsOn
from matisse_controller.matisse.event_report import log_event, EventType
from matisse_controller.matisse.lock_correction_thread import LockCorrectionThread
from matisse_controller.matisse.plotting import BirefringentFilterScanPlotProcess, ThinEtalonScanPlotProcess
from matisse_controller.matisse.stabilization_thread import StabilizationThread
from matisse_controller.wavemaster import WaveMaster


class Matisse:
    matisse_lock = threading.Lock()

    def __init__(self):
        try:
            # Initialize VISA resource manager, connect to Matisse and wavemeter, clear any errors.
            self._instrument = ResourceManager().open_resource(cfg.get(cfg.MATISSE_DEVICE_ID))
            self.target_wavelength = None
            self._stabilization_thread = None
            self._lock_correction_thread = None
            self._plotting_processes = []
            self.exit_flag = False
            self._scan_attempts = 0
            self._scan_device_attempts = 0
            self._force_large_scan = True
            self._restart_set_wavelength = False
            self.is_setting_wavelength = False
            self.is_scanning_bifi = False
            self.is_scanning_thin_etalon = False
            self.stabilization_auto_corrections = 0
            self.query('ERROR:CLEAR')  # start with a clean slate
            self.query('MOTORBIREFRINGENT:CLEAR')
            self.query('MOTORTHINETALON:CLEAR')
            self._wavemeter = WaveMaster(cfg.get(cfg.WAVEMETER_PORT))
        except VisaIOError as ioerr:
            raise IOError("Can't reach Matisse. Make sure it's on and connected via USB.") from ioerr

    def __del__(self):
        try:
            self._instrument.close()
        except AttributeError:
            # No instrument to close
            pass

    def query(self, command: str, numeric_result=False, raise_on_error=True):
        """
        Send a command to the Matisse and return the response.

        Note that some commands (like setting the position of a stepper motor) take additional time to execute, so do
        not assume the command has finished executing just because the query returns "OK".

        This doesn't raise errors if the error occurred in the controller for a specific component of the Matisse, like
        the birefringent filter motor, for example. That motor has a separate status register with error information
        that can be queried and cleared separately.

        Parameters
        ----------
        command : str
            the command to send
        numeric_result : bool
            whether to convert the second portion of the result to a float
        raise_on_error : bool
            whether to raise a Python error if Matisse error occurs

        Returns
        -------
        str or float
            The response from the Matisse to the given command
        """
        try:
            with Matisse.matisse_lock:
                result: str = self._instrument.query(command).strip()
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
        """
        Returns
        -------
        float
            the wavelength (in nanometers) as measured by the wavemeter
        """
        return self._wavemeter.get_wavelength()

    def wavemeter_raw_value(self) -> str:
        """
        Returns
        -------
        str
            the raw reading from the wavemeter (what's on the display at the moment)
        """
        return self._wavemeter.get_raw_value()

    def set_wavelength(self, wavelength: float):
        """
        Configure the Matisse to output a given wavelength.

        If the laser is locked and/or stabilizing, pause those operations for the duration of the method.

        First I'll check the difference between the current wavelength and the target wavelength.

        - If this is the first time this is being run, do a large birefringent scan regardless of the difference.
        - If it's greater than cfg.LARGE_WAVELENGTH_DRIFT, do a large birefringent scan to choose a better peak.
        - If it's between about cfg.MEDIUM_WAVELENGTH_DRIFT and cfg.LARGE_WAVELENGTH_DRIFT, do a small birefringent scan
          to keep it on the peak.
        - If it's between cfg.SMALL_WAVELENGTH_DRIFT nm and cfg.MEDIUM_WAVELENGTH_DRIFT, skip the first birefringent
          scan and go right to the thin etalon scan.
        - If it's less than cfg.SMALL_WAVELENGTH_DRIFT, skip all BiFi and TE scans, and just do a RefCell scan.

        This is generally the process I'll follow:

        1. Decide whether to skip any scans, as described above.
        2. Set approx. wavelength using BiFi. This is supposed to be good to about +-1 nm but it's usually very far off.
        3. Scan the BiFi back and forth and measure the total laser power at each point.
        4. Find all local maxima, move the BiFi to the maximum that's closest to the desired wavelength.
        5. Move the thin etalon motor directly to a position close to the target wavelength.
        6. Scan the thin etalon back and forth and measure the thin etalon reflex at each point.
        7. Find all local minima. Move the TE to the minimum that's closest to the desired wavelength.
        8. Shift the thin etalon a over bit by cfg.THIN_ETA_NUDGE. We want to be on the "flank" of the chosen parabola.
        9. Do a small BiFi scan to make sure we're still on the location with maximum power. If the distance to the new
           motor location is very small, just leave the motor where it is.
        10. Do a small thin etalon scan to make sure we're still on the flank of the right parabola.
        11. Attempt to lock the laser, setting the fast piezo setpoint if needed.
        12. Enable RefCell stabilization, which scans the device up or down until the desired wavelength is reached.

        If more than cfg.SCAN_LIMIT scan attempts pass before stabilizing, restart the whole process over again.
        If, during stabilization, more than cfg.CORRECTION_LIMIT corrections are made, start with a large birefringent
        scan the next time this method is run.
        If more than cfg.SCAN_DEVICE_LIMIT attempts are made to set the wavelength using only the RefCell, start with a
        large birefringent scan the next time this method is run. This is to prevent falling into a dip in the power
        diode curve, which causes large jumps in the wavelength (~0.4 nm) that cannot be easily fixed otherwise.

        A scan may decide it needs to start the process over again for some other reason, like the thin etalon moving to
        a location with mostly noise.

        Parameters
        ----------
        wavelength : float
            the desired wavelength
        """
        self.is_setting_wavelength = True
        assert cfg.get(cfg.WAVELENGTH_LOWER_LIMIT) < wavelength < cfg.get(cfg.WAVELENGTH_UPPER_LIMIT), \
            'Target wavelength out of range.'

        self.target_wavelength = wavelength

        if self.is_lock_correction_on():
            self.stop_laser_lock_correction()
        if self.is_stabilizing():
            self.stabilize_off()

        while True:
            self._scan_attempts = 0
            diff = abs(wavelength - self.wavemeter_wavelength())

            if diff > cfg.get(cfg.LARGE_WAVELENGTH_DRIFT) or self._force_large_scan:
                # Notice we randomize the position of the thin etalon a little bit to avoid returning to exactly the
                # same state each time. This is to further avoid the possibility of getting stuck in an endless loop.
                rand_offset = np.random.randint(-cfg.get(cfg.THIN_ETA_RAND_RANGE), cfg.get(cfg.THIN_ETA_RAND_RANGE) + 1)
                self.query(f"MOTTE:POS {cfg.get(cfg.THIN_ETA_RESET_POS) + rand_offset}")
                self.reset_stabilization_piezos()
                # Normal BiFi scan
                print(f"Setting BiFi to ~{wavelength} nm... ")
                self.set_bifi_wavelength(wavelength)
                time.sleep(cfg.get(cfg.WAVEMETER_MEASUREMENT_DELAY))
                print(f"Done. Wavelength is now {self.wavemeter_wavelength()} nm. "
                      "(This is often very wrong, don't worry)")
                self.birefringent_filter_scan(repeat=True)
                self.thin_etalon_scan(repeat=True)
                self.birefringent_filter_scan(scan_range=cfg.get(cfg.BIFI_SCAN_RANGE_SMALL), repeat=True)
                self.thin_etalon_scan(scan_range=cfg.get(cfg.THIN_ETA_SCAN_RANGE_SMALL), repeat=True)
            elif cfg.get(cfg.MEDIUM_WAVELENGTH_DRIFT) < diff <= cfg.get(cfg.LARGE_WAVELENGTH_DRIFT):
                # Small BiFi scan
                self.birefringent_filter_scan(scan_range=cfg.get(cfg.BIFI_SCAN_RANGE_SMALL), repeat=True)
                self.thin_etalon_scan(repeat=True)
                self.birefringent_filter_scan(scan_range=cfg.get(cfg.BIFI_SCAN_RANGE_SMALL), repeat=True)
                self.thin_etalon_scan(scan_range=cfg.get(cfg.THIN_ETA_SCAN_RANGE_SMALL), repeat=True)
            elif cfg.get(cfg.SMALL_WAVELENGTH_DRIFT) < diff <= cfg.get(cfg.MEDIUM_WAVELENGTH_DRIFT):
                # No BiFi scan, TE scan only
                self.thin_etalon_scan(repeat=True)
                self.birefringent_filter_scan(scan_range=cfg.get(cfg.BIFI_SCAN_RANGE_SMALL), repeat=True)
                self.thin_etalon_scan(scan_range=cfg.get(cfg.THIN_ETA_SCAN_RANGE_SMALL), repeat=True)
            else:
                # No BiFi, no TE. Scan device only.
                self._scan_device_attempts += 1

            # Restart/exit conditions
            if self.exit_flag:
                self.is_setting_wavelength = False
                return
            if self._restart_set_wavelength:
                self._restart_set_wavelength = False
                print('Restarting wavelength-setting process.')
                continue
            elif self._scan_attempts > cfg.get(cfg.SCAN_LIMIT):
                print('WARNING: Number of scan attempts exceeded. Starting wavelength-setting process over again.')
                log_event(EventType.SCAN_LIMIT_EXCEEDED, self, self.wavemeter_wavelength(),
                          f"too many scans, exceeded limit of {cfg.get(cfg.SCAN_LIMIT)}, restarting set_wavelength")
                self._force_large_scan = True
                continue
            elif self.stabilization_auto_corrections > cfg.get(cfg.CORRECTION_LIMIT):
                print('WARNING: Number of stabilization auto-corrections exceeded. Starting wavelength-setting process '
                      'over again.')
                log_event(EventType.STABILIZATION_LIMIT_EXCEEDED, self, self.wavemeter_wavelength(),
                          f"too many stabilization corrections, exceeded limit of {cfg.get(cfg.CORRECTION_LIMIT)}, "
                          'restarting set_wavelength')
                self.stabilization_auto_corrections = 0
                self._force_large_scan = True
                continue
            elif self._scan_device_attempts > cfg.get(cfg.SCAN_DEVICE_LIMIT):
                print('WARNING: Limit for number of times scanning device exceeded. Starting wavelength-setting '
                      'process over again.')
                log_event(EventType.SCAN_DEVICE_LIMIT_EXCEEDED, self, self.wavemeter_wavelength(),
                          f"too many times scanning device, exceeded limit of {cfg.get(cfg.SCAN_DEVICE_LIMIT)}, "
                          'restarting set_wavelength')
                self._scan_device_attempts = 0
                self._force_large_scan = True
            else:
                self._force_large_scan = False
                break

        self.start_laser_lock_correction()
        print('Attempting to lock laser...')
        while not self.laser_locked():
            if self.exit_flag:
                self.is_setting_wavelength = False
                return
            if not self.is_lock_correction_on():
                print('Lock failed, trying again.')
                self.set_recommended_fast_piezo_setpoint()
                self.start_laser_lock_correction()
            time.sleep(1)
        self.stabilize_on()

        self.is_setting_wavelength = False

    def reset_motors(self):
        """Move the birefringent filter and thin etalon motors to their configured reset positions."""
        self.query(f"MOTBI:POS {cfg.get(cfg.BIFI_RESET_POS)}")
        self.query(f"MOTTE:POS {cfg.get(cfg.THIN_ETA_RESET_POS)}")

    def close_all_plots(self):
        """Close all plot windows."""
        for process in self._plotting_processes:
            process.terminate()

    def birefringent_filter_scan(self, scan_range: int = None, repeat=False):
        """
        Initiate a scan of the birefringent filter, selecting the power maximum closest to the target wavelength.

        A configurable Savitzky-Golay filter is used to smooth the data for analysis.

        The position is not changed if the difference between the current position and the "best" position is less than
        1/6 of the average separation between peaks in the power diode curve.

        Additionally, plot the power data and motor position selection if plotting is enabled for this scan.

        Parameters
        ----------
        scan_range : int
            number of motor positions to scan left and right
        repeat : bool
            whether to repeat the scan until the wavelength difference is less than cfg.MEDIUM_WAVELENGTH_DRIFT
        """
        self.is_scanning_bifi = True
        if self.exit_flag or self._scan_attempts > cfg.get(cfg.SCAN_LIMIT) or self._restart_set_wavelength:
            self.is_scanning_bifi = False
            return
        if self.target_wavelength is None:
            self.target_wavelength = self.wavemeter_wavelength()
        if scan_range is None:
            scan_range = cfg.get(cfg.BIFI_SCAN_RANGE)

        self._scan_attempts += 1
        old_pos = int(self.query('MOTBI:POS?', numeric_result=True))
        lower_end = old_pos - scan_range
        upper_end = old_pos + scan_range
        assert (0 < lower_end < BIREFRINGENT_FILTER_UPPER_LIMIT
                and 0 < upper_end < BIREFRINGENT_FILTER_UPPER_LIMIT
                and lower_end < upper_end), 'Conditions for BiFi scan invalid. Motor position must be between ' + \
                                            f"{scan_range} and {BIREFRINGENT_FILTER_UPPER_LIMIT - scan_range}"
        positions = np.array(range(lower_end, upper_end, cfg.get(cfg.BIFI_SCAN_STEP)))
        voltages = np.array([])
        print('Starting BiFi scan... ')
        for pos in positions:
            self.set_bifi_motor_pos(pos)
            voltages = np.append(voltages, self.query('DPOW:DC?', numeric_result=True))
        self.set_bifi_motor_pos(old_pos)  # return back to where we started, just in case something goes wrong
        print('Done.')

        print('Analyzing scan data... ')
        # Smooth out the data and find extrema
        smoothed_data = savgol_filter(voltages, window_length=cfg.get(cfg.BIFI_SMOOTHING_FILTER_WINDOW),
                                      polyorder=cfg.get(cfg.BIFI_SMOOTHING_FILTER_POLYORDER))
        maxima = argrelextrema(smoothed_data, np.greater, order=5)

        # Find the position of the extremum closest to the target wavelength
        wavelength_differences = np.array([])
        for pos in positions[maxima]:
            self.set_bifi_motor_pos(pos)
            time.sleep(cfg.get(cfg.WAVEMETER_MEASUREMENT_DELAY))
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[maxima][np.argmin(wavelength_differences)]

        # By default, let's assume we're using the new position.
        using_new_pos = True

        if len(positions[maxima]) > 1:
            difference_threshold = np.mean(np.diff(positions[maxima])) / 6
            if abs(old_pos - best_pos) > difference_threshold:
                self.set_bifi_motor_pos(best_pos)
            else:
                print('Current BiFi motor position is close enough, leaving it alone.')
                self.set_bifi_motor_pos(old_pos)
                using_new_pos = False
        else:
            self.set_bifi_motor_pos(best_pos)
        print('Done.')
        self.is_scanning_bifi = False

        if cfg.get(cfg.BIFI_SCAN_SHOW_PLOTS):
            # TODO: Label wavelength at each peak
            plot_process = BirefringentFilterScanPlotProcess(positions, voltages, smoothed_data, maxima, old_pos,
                                                             best_pos, using_new_pos, daemon=True)
            self._plotting_processes.append(plot_process)
            plot_process.start()

        if repeat:
            new_diff = np.min(wavelength_differences)
            if abs(new_diff) > cfg.get(cfg.MEDIUM_WAVELENGTH_DRIFT):
                print('Wavelength still too far away from target value. Starting another scan.')
                self.birefringent_filter_scan(scan_range, repeat=True)

    def set_bifi_motor_pos(self, pos: int):
        """
        Set the birefringent filter motor to the selected position. This method will block the calling thread until the
        motor status is idle again.

        Parameters
        ----------
        pos : int
            the desired motor position
        """
        assert 0 < pos < BIREFRINGENT_FILTER_UPPER_LIMIT, 'Target motor position out of range.'
        # Wait for motor to be ready to accept commands
        while not self.bifi_motor_status() == MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTBI:POS {pos}")
        # Wait for motor to finish movement
        while not self.bifi_motor_status() == MOTOR_STATUS_IDLE:
            pass

    def set_bifi_wavelength(self, value: float):
        """
        Set the birefringent filter motor to the approximate position corresponding to the given wavelength. This
        position is determined by the Matisse.

        Parameters
        ----------
        value : float
            the desired wavelength
        """
        assert cfg.get(cfg.WAVELENGTH_LOWER_LIMIT) < value < cfg.get(cfg.WAVELENGTH_UPPER_LIMIT), \
            'Target wavelength out of range.'
        # Wait for motor to be ready to accept commands
        while not self.bifi_motor_status() == MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTBI:WAVELENGTH {value}")
        # Wait for motor to finish movement
        while not self.bifi_motor_status() == MOTOR_STATUS_IDLE:
            pass

    def bifi_motor_status(self):
        """
        Returns
        -------
        int
            the last 8 bits of the birefringent filter motor status
        """
        return int(self.query('MOTBI:STATUS?', numeric_result=True)) & 0b000000011111111

    def thin_etalon_scan(self, scan_range: int = None, repeat=False):
        """
        Initiate a scan of the thin etalon, selecting the reflex minimum closest to the target wavelength.

        A configurable Savitzky-Golay filter is used to smooth the data for analysis.

        The position is not changed if the difference between the current position and the "best" position is less than
        1/6 of the average separation between valleys in the reflex curve.

        If the thin etalon moves too far to one side and we end up in a valley of the power diode curve, the wavelength
        will make large jumps, so a small birefringent scan is performed to correct this.

        If the thin etalon moves into a region with too much noise (as determined by a normalized RMS deviation), quit
        early and perform a large scan next time set_wavelength is called.

        Nudges the motor position a little bit away from the minimum to ensure good locking later.
        Additionally, plot the reflex data and motor position selection.

        Parameters
        ----------
        scan_range : int
            number of motor positions to scan left and right
        repeat : bool
            whether to repeat the scan until the wavelength difference is less than cfg.SMALL_WAVELENGTH_DRIFT
        """
        self.is_scanning_thin_etalon = True
        if self.exit_flag or self._scan_attempts > cfg.get(cfg.SCAN_LIMIT) or self._restart_set_wavelength:
            self.is_scanning_thin_etalon = False
            return
        if self.target_wavelength is None:
            self.target_wavelength = self.wavemeter_wavelength()
        if scan_range is None:
            scan_range = cfg.get(cfg.THIN_ETA_SCAN_RANGE)

        self._scan_attempts += 1
        old_pos = int(self.query('MOTTE:POS?', numeric_result=True))
        lower_end, upper_end = self.limits_for_thin_etalon_scan(old_pos, scan_range)

        positions = np.array(range(lower_end, upper_end, cfg.get(cfg.THIN_ETA_SCAN_STEP)))
        voltages = np.array([])
        print('Starting thin etalon scan... ')
        for pos in positions:
            self.set_thin_etalon_motor_pos(pos)
            voltages = np.append(voltages, self.query('TE:DC?', numeric_result=True))
        self.set_thin_etalon_motor_pos(old_pos)  # return back to where we started, just in case something goes wrong
        print('Done.')

        print('Analyzing scan data... ')
        # Smooth out the data and find extrema
        smoothed_data = savgol_filter(voltages, window_length=cfg.get(cfg.THIN_ETA_SMOOTHING_FILTER_WINDOW),
                                      polyorder=cfg.get(cfg.THIN_ETA_SMOOTHING_FILTER_POLYORDER))

        normalized_std_dev = np.sqrt(np.sum(((smoothed_data - voltages) / smoothed_data) ** 2))
        print(f"Normalized standard deviation from smoothed data: {normalized_std_dev}")
        # Example good value: 1.5, example bad value: 2.5
        if normalized_std_dev > cfg.get(cfg.THIN_ETA_MAX_ALLOWED_STDDEV):
            print('Abnormal deviation from smoothed curve detected, the scan region might just contain noise.')
            self._restart_set_wavelength = True
            self._force_large_scan = True
            self.is_scanning_thin_etalon = False
            return

        minima = argrelextrema(smoothed_data, np.less, order=5)

        # Find the position of the extremum closest to the target wavelength
        wavelength_differences = np.array([])
        for pos in positions[minima]:
            self.set_thin_etalon_motor_pos(pos)
            time.sleep(cfg.get(cfg.WAVEMETER_MEASUREMENT_DELAY))
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_minimum_index = np.argmin(wavelength_differences)
        best_pos = positions[minima][best_minimum_index] + cfg.get(cfg.THIN_ETA_NUDGE)

        # By default, let's assume we're using the new position.
        using_new_pos = True

        if len(positions[minima]) > 1:
            difference_threshold = np.mean(np.diff(positions[minima])) / 6
            if abs(old_pos - best_pos) > difference_threshold:
                self.set_thin_etalon_motor_pos(best_pos)
            else:
                print('Current thin etalon motor position is close enough, leaving it alone.')
                self.set_thin_etalon_motor_pos(old_pos)
                using_new_pos = False
        else:
            self.set_thin_etalon_motor_pos(best_pos)
        print('Done.')
        self.is_scanning_thin_etalon = False

        adjacent_differences = np.diff(wavelength_differences)
        left_too_large = (best_minimum_index >= 1 and
                          adjacent_differences[best_minimum_index - 1] > cfg.get(cfg.LARGE_WAVELENGTH_DRIFT))
        right_too_large = (best_minimum_index < len(wavelength_differences) - 1 and
                           adjacent_differences[best_minimum_index] > cfg.get(cfg.LARGE_WAVELENGTH_DRIFT))
        if left_too_large or right_too_large:
            print('Large jump in wavelength detected, correcting birefringent filter position.')
            self.birefringent_filter_scan(cfg.get(cfg.BIFI_SCAN_RANGE_SMALL), repeat=False)
            print('Returning to thin etalon scan.')

        if cfg.get(cfg.THIN_ETA_SHOW_PLOTS):
            plot_process = ThinEtalonScanPlotProcess(positions, voltages, smoothed_data, minima, old_pos, best_pos,
                                                     using_new_pos, daemon=True)
            self._plotting_processes.append(plot_process)
            plot_process.start()

        if repeat:
            new_diff = np.min(wavelength_differences)
            if new_diff > cfg.get(cfg.SMALL_WAVELENGTH_DRIFT):
                print('Wavelength still too far away from target value. Starting another scan.')
                self.thin_etalon_scan(scan_range, repeat=True)

    def limits_for_thin_etalon_scan(self, current_pos: int, scan_range: int) -> (int, int):
        """
        Calculate appropriate lower and upper limits for a thin etalon scan.

        If the current wavelength difference is more than 1 thin etalon mode, change the limits of the scan to only go
        left or right, rather than scanning on both sides of the current position.

        Parameters
        ----------
        current_pos: the current position of the thin etalon
        scan_range: the desired range of the thin etalon scan

        Returns
        -------
        int, int
            the appropriate lower and upper limits for the scan
        """
        lower_limit = current_pos - scan_range
        upper_limit = current_pos + scan_range
        diff = self.target_wavelength - self.wavemeter_wavelength()
        # Adjust scan limits if we're off by more than 1 mode
        if abs(diff) > THIN_ETALON_NM_PER_MODE:
            if diff < 0:
                lower_limit = current_pos - scan_range
                upper_limit = current_pos
            else:
                lower_limit = current_pos
                upper_limit = current_pos + scan_range

        assert (0 < lower_limit < THIN_ETALON_UPPER_LIMIT
                and 0 < upper_limit < THIN_ETALON_UPPER_LIMIT
                and lower_limit < upper_limit), \
            'Conditions for thin etalon scan invalid. Continuing would put the motor at its upper or lower limit.'

        return lower_limit, upper_limit

    def set_thin_etalon_motor_pos(self, pos: int):
        """
        Set the thin etalon motor to the selected position. This method will block the calling thread until the motor
        status is idle again.

        Parameters
        ----------
        pos : int
            the desired motor position
        """
        assert (THIN_ETALON_LOWER_LIMIT < pos < THIN_ETALON_UPPER_LIMIT), \
            f"Can't set thin etalon motor position to {pos}, this is out of range."
        # Wait for motor to be ready to accept commands
        while not self.thin_etalon_motor_status() == MOTOR_STATUS_IDLE:
            pass
        self.query(f"MOTTE:POS {pos}")
        # Wait for motor to finish movement
        while not self.thin_etalon_motor_status() == MOTOR_STATUS_IDLE:
            pass

    def thin_etalon_motor_status(self):
        """
        Returns
        -------
        int
            the last 8 bits of the thin etalon motor status
        """
        return int(self.query('MOTTE:STATUS?', numeric_result=True)) & 0b000000011111111

    def set_slow_piezo_control(self, enable: bool):
        """Set the status of the control loop for the slow piezo."""
        self.query(f"SLOWPIEZO:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def set_fast_piezo_control(self, enable: bool):
        """Set the status of the control loop for the fast piezo."""
        self.query(f"FASTPIEZO:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def set_thin_etalon_control(self, enable: bool):
        """Set the status of the control loop for the thin etalon."""
        self.query(f"THINETALON:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def set_piezo_etalon_control(self, enable: bool):
        """Set the status of the control loop for the piezo etalon."""
        self.query(f"PIEZOETALON:CONTROLSTATUS {'RUN' if enable else 'STOP'}")

    def all_control_loops_on(self):
        """
        Returns
        -------
        bool
            whether the slow piezo, thin etalon, piezo etalon, and fast piezo all have their control loops enabled
        """
        return ('RUN' in self.query('SLOWPIEZO:CONTROLSTATUS?')
                and 'RUN' in self.query('THINETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('PIEZOETALON:CONTROLSTATUS?')
                and 'RUN' in self.query('FASTPIEZO:CONTROLSTATUS?'))

    def fast_piezo_locked(self):
        """
        Returns
        -------
        bool
            whether the fast piezo is currently locked
        """
        return 'TRUE' in self.query('FASTPIEZO:LOCK?')

    def laser_locked(self):
        """
        Returns
        -------
        bool
            whether the laser is locked, which means all control loops are on and the fast piezo is locked
        """
        return self.all_control_loops_on() and self.fast_piezo_locked()

    def stabilize_on(self):
        """
        Enable stabilization using the stabilization piezos and thin etalon to keep the wavelength constant.

        If there is no target wavelength set, stabilize at the current wavelength.

        Starts a `matisse_controller.matisse.stabilization_thread.StabilizationThread` as a daemon for this purpose.
        To stop stabilizing the laser, call `Matisse.stabilize_off`.
        """
        if self.is_stabilizing():
            print('WARNING: Already stabilizing laser. Call stabilize_off before trying to stabilize again.')
        else:
            self._stabilization_thread = StabilizationThread(self, queue.Queue(), daemon=True)

            if self.target_wavelength is None:
                self.target_wavelength = self.wavemeter_wavelength()
            print(f"Stabilizing laser at {self.target_wavelength} nm...")
            self._stabilization_thread.start()

    def stabilize_off(self):
        """Exit the stabilization loop, which stops the stabilization thread."""
        if self.is_stabilizing():
            print('Stopping stabilization thread.')
            self._stabilization_thread.messages.put('stop')
            self._stabilization_thread.join()
            print('Stabilization thread has been stopped.')
        else:
            print('WARNING: Stabilization thread is not running.')

    def start_scan(self, direction):
        """
        Start a device scan in the given direction. To configure the speed of the scan, use the queries
        SCAN:RISINGSPEED or SCAN:FALLINGSPEED.

        Parameters
        ----------
        direction : int
            `SCAN_MODE_UP` (0) or `SCAN_MODE_DOWN` (1)
        """
        self.query(f"SCAN:MODE {direction}")
        self.query(f"SCAN:STATUS RUN")

    def stop_scan(self):
        """Terminate a device scan."""
        self.query(f"SCAN:STATUS STOP")

    def is_scanning(self):
        """
        Returns
        -------
        bool
            whether the device is currently scanning
        """
        return 'RUN' in self.query('SCAN:STATUS?')

    def is_stabilizing(self):
        """
        Returns
        -------
        bool
            whether the stabilization thread is running
        """
        return self._stabilization_thread is not None and self._stabilization_thread.is_alive()

    def get_stabilizing_piezo_positions(self):
        """
        Returns
        -------
        (float, float, float)
            the current positions of the "stabilization piezos": RefCell, piezo etalon, and slow piezo
        """
        current_refcell_pos = self.query('SCAN:NOW?', numeric_result=True)
        current_slow_pz_pos = self.query('SLOWPIEZO:NOW?', numeric_result=True)
        current_pz_eta_pos = self.query('PIEZOETALON:BASELINE?', numeric_result=True)
        return current_refcell_pos, current_pz_eta_pos, current_slow_pz_pos

    def is_any_limit_reached(self):
        """
        Returns
        -------
        bool
            whether any of the stabilization piezos are very close to their limits
        """
        refcell_pos, pz_eta_pos, slow_pz_pos = self.get_stabilizing_piezo_positions()
        offset = cfg.get(cfg.COMPONENT_LIMIT_OFFSET)
        return not (REFERENCE_CELL_LOWER_LIMIT + offset < refcell_pos < REFERENCE_CELL_UPPER_LIMIT - offset
                    and SLOW_PIEZO_LOWER_LIMIT + offset < slow_pz_pos < SLOW_PIEZO_UPPER_LIMIT - offset
                    and PIEZO_ETALON_LOWER_LIMIT + offset < pz_eta_pos < PIEZO_ETALON_UPPER_LIMIT - offset)

    def reset_stabilization_piezos(self):
        """
        Reset the slow piezo to the center, and the RefCell and piezo etalon according to the following rules:

        - If RefCell is at upper limit, piezo etalon is likely near lower limit
        - If wavelength is still too low, move RefCell down lower than usual and piezo etalon higher than usual
        - If RefCell is at lower limit, piezo etalon is likely near upper limit
        - If wavelength is still too high, move RefCell up higher than usual and piezo etalon lower than usual
        - Else, move RefCell and piezo etalon to their center positions.

        A target wavelength must already be set in order to run this method.
        """
        current_refcell_pos, current_pz_eta_pos, current_slow_pz_pos = self.get_stabilizing_piezo_positions()
        current_wavelength = self.wavemeter_wavelength()

        offset = cfg.get(cfg.COMPONENT_LIMIT_OFFSET)
        if (current_refcell_pos > REFERENCE_CELL_UPPER_LIMIT - offset
                and current_wavelength < self.target_wavelength):
            self.query(f"SCAN:NOW {cfg.get(cfg.REFCELL_LOWER_CORRECTION_POS)}")
            self.query(f"PIEZOETALON:BASELINE {cfg.get(cfg.PIEZO_ETA_UPPER_CORRECTION_POS)}")
        elif (current_refcell_pos < REFERENCE_CELL_LOWER_LIMIT + offset
              and current_wavelength > self.target_wavelength):
            self.query(f"SCAN:NOW {cfg.get(cfg.REFCELL_UPPER_CORRECTION_POS)}")
            self.query(f"PIEZOETALON:BASELINE {cfg.get(cfg.PIEZO_ETA_LOWER_CORRECTION_POS)}")
        else:
            self.query(f"SCAN:NOW {cfg.get(cfg.REFCELL_MID_CORRECTION_POS)}")
            self.query(f"PIEZOETALON:BASELINE {cfg.get(cfg.PIEZO_ETA_MID_CORRECTION_POS)}")

        self.query(f"SLOWPIEZO:NOW {cfg.get(cfg.SLOW_PIEZO_MID_CORRECTION_POS)}")

    def get_reference_cell_transmission_spectrum(self):
        """
        Scan the reference cell from cfg.FAST_PZ_SETPOINT_SCAN_LOWER_LIMIT to cfg.FAST_PZ_SETPOINT_SCAN_UPPER_LIMIT,
        measuring the input to the fast piezo for each position. This creates a curve that represents the transmission
        spectrum of the reference cell.

        Returns
        -------
        (ndarray, ndarray)
            the positions and input values measured during the scan
        """
        # TODO: Make a context manager for pausing stabilization/scanning
        stabilize_when_done = False
        if self.is_stabilizing():
            self.stabilize_off()
            stabilize_when_done = True
        self.stop_scan()

        positions = np.linspace(cfg.get(cfg.FAST_PZ_SETPOINT_SCAN_LOWER_LIMIT),
                                cfg.get(cfg.FAST_PZ_SETPOINT_SCAN_UPPER_LIMIT),
                                cfg.get(cfg.FAST_PZ_SETPOINT_NUM_POINTS))
        values = np.array([])
        old_refcell_pos = self.query(f"SCAN:NOW?", numeric_result=True)
        for pos in positions:
            self.query(f"SCAN:NOW {pos}")
            values = np.append(values, self.query('FASTPIEZO:INPUT?', numeric_result=True))
        self.query(f"SCAN:NOW {old_refcell_pos}")

        # TODO: Double check whether to start stabilizing again or to enable lock correction
        if stabilize_when_done:
            self.stabilize_on()

        return positions, values

    def set_recommended_fast_piezo_setpoint(self):
        """
        Analyze the data from the reference cell transmission spectrum, and set the fast piezo setpoint to a point
        about halfway between the min and max points on the spectrum. The recommended value is determined by averaging
        a number of scans given by cfg.FAST_PZ_SETPOINT_NUM_SCANS.
        """
        with ControlLoopsOn(self):
            num_scans = cfg.get(cfg.FAST_PZ_SETPOINT_NUM_SCANS)
            total = 0
            for i in range(0, num_scans):
                positions, values = self.get_reference_cell_transmission_spectrum()
                setpoint = (np.max(values) + np.min(values)) / 2
                total += setpoint
            recommended_setpoint = total / num_scans
            print(f"Setting fast piezo setpoint to {recommended_setpoint}")
            self.query(f"FASTPIEZO:CONTROLSETPOINT {recommended_setpoint}")

    def start_laser_lock_correction(self):
        """
        Try to lock the laser, and make automatic corrections to the stabilization piezos if needed.

        If there is no target wavelength set, lock at the current wavelength.

        Starts a `matisse_controller.matisse.lock_correction_thread.LockCorrectionThread` as a daemon for this purpose.
        Call `Matisse.stop_laser_lock_correction` to disable lock.
        """
        if self.is_lock_correction_on():
            print('WARNING: Lock correction is already running.')
        else:
            print('Starting laser lock.')
            self._lock_correction_thread = LockCorrectionThread(self, cfg.get(cfg.LOCKING_TIMEOUT), queue.Queue(),
                                                                daemon=True)
            if self.target_wavelength is None:
                self.target_wavelength = self.wavemeter_wavelength()
            self._lock_correction_thread.start()

    def stop_laser_lock_correction(self):
        """Disable the lock correction loop, which stops the lock correction thread."""
        if self.is_lock_correction_on():
            self._lock_correction_thread.messages.put('stop')
            self._lock_correction_thread.join()
        else:
            print('WARNING: laser is not locked.')

    def is_lock_correction_on(self):
        """
        Returns
        -------
        bool
            whether the lock correction thread is running
        """
        return self._lock_correction_thread is not None and self._lock_correction_thread.is_alive()
