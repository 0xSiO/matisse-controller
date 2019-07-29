import queue
import threading
import time

import numpy as np
from pyvisa import ResourceManager, VisaIOError
from scipy.signal import savgol_filter, argrelextrema

import matisse_controller.config as cfg
from matisse_controller.matisse.constants import Constants
from matisse_controller.matisse.lock_correction_thread import LockCorrectionThread
from matisse_controller.matisse.plotting import BirefringentFilterScanPlotProcess, ThinEtalonScanPlotProcess
from matisse_controller.matisse.stabilization_thread import StabilizationThread
from matisse_controller.wavemaster import WaveMaster


class Matisse(Constants):
    matisse_lock = threading.Lock()

    def __init__(self):
        """
        Initialize VISA resource manager, connect to Matisse, clear any errors.

        Additionally, connect to the wavemeter and open up a plot to display results of BiFi/TE scans.
        """
        try:
            # TODO: Add access modifiers on all these instance variables
            self.instrument = ResourceManager().open_resource(cfg.get(cfg.MATISSE_DEVICE_ID))
            self.target_wavelength = None
            self.stabilization_thread = None
            self.lock_correction_thread = None
            self.plotting_processes = []
            self.exit_flag = False
            self.query('ERROR:CLEAR')  # start with a clean slate
            self.query('MOTORBIREFRINGENT:CLEAR')
            self.query('MOTORTHINETALON:CLEAR')
            self.wavemeter = WaveMaster(cfg.get(cfg.WAVEMETER_PORT))
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

        First I'll check the difference between the current wavelength and the target wavelength.
        If it's greater than about 0.4 nm, do a large birefringent scan to choose a better peak.
        If it's between about 0.15 nm and 0.4 nm, do a small birefringent scan to keep it on the peak.
        If it's between 0.02 nm and 0.15 nm, skip the first birefringent scan and go right to the thin etalon scan.
        If it's less than 0.02 nm, skip all BiFi and TE scans, and just do a RefCell scan.

        This is generally the process I'll follow:
        1. Decide whether to skip any scans, as described above.
        2. Set approx. wavelength using BiFi. This is good to about +-1 nm.
        3. Scan the BiFi back and forth and measure the total laser power at each point.
        4. Find all local maxima, move the BiFi to the maximum that's closest to the desired wavelength.
        5. Move the thin etalon motor directly to a position close to the target wavelength.
        6. Scan the thin etalon back and forth and measure the thin etalon reflex at each point.
        7. Find all local minima. Move the TE to the minimum that's closest to the desired wavelength.
        8. Shift the TE to the left or right a little bit. We want to be on the "flank" of the chosen parabola.
        9. Do a small BiFi scan to make sure we're still on the location with maximum power.
        10. Do a small thin etalon scan to make sure we're still on the flank of the right parabola.
        11. Enable RefCell stabilization, which scans the device up or down until the desired wavelength is reached.

        :param wavelength: the desired wavelength
        """
        assert cfg.get(cfg.WAVELENGTH_LOWER_LIMIT) < wavelength < cfg.get(cfg.WAVELENGTH_UPPER_LIMIT), \
            'Target wavelength out of range.'

        self.target_wavelength = wavelength

        lock_when_done = self.is_lock_correction_on()
        if self.is_lock_correction_on():
            self.stop_laser_lock_correction()
        if self.is_stabilizing():
            self.stabilize_off()

        diff = abs(wavelength - self.wavemeter_wavelength())

        if diff > cfg.get(cfg.LARGE_WAVELENGTH_DRIFT):
            self.reset_motors()
            # Normal BiFi scan
            print(f"Setting BiFi to ~{wavelength} nm... ", end='')
            self.set_bifi_wavelength(wavelength)
            time.sleep(0.1)
            print(f"Done. Wavelength is now {self.wavemeter_wavelength()} nm.")
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
            pass
        if self.exit_flag:
            return
        if lock_when_done:
            self.start_laser_lock_correction()
        self.stabilize_on()

    def reset_motors(self):
        self.query(f"MOTBI:POS {100000}")
        self.query(f"MOTTE:POS {18000}")

    def birefringent_filter_scan(self, scan_range: int = None, repeat=False):
        """
        Initiate a scan of the birefringent filter, selecting the power maximum closest to the target wavelength.

        Additionally, plot the power data and motor position selection.
        """
        if self.exit_flag:
            return
        if self.target_wavelength is None:
            self.target_wavelength = self.wavemeter_wavelength()
        if scan_range is None:
            scan_range = cfg.get(cfg.BIFI_SCAN_RANGE)

        center_pos = int(self.query('MOTBI:POS?', numeric_result=True))
        lower_end = center_pos - scan_range
        upper_end = center_pos + scan_range
        assert (0 < lower_end < Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT
                and 0 < upper_end < Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT
                and lower_end < upper_end), 'Conditions for BiFi scan invalid. Motor position must be between ' + \
                                            f"{scan_range} and {Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT - scan_range}"
        positions = np.array(range(lower_end, upper_end, cfg.get(cfg.BIFI_SCAN_STEP)))
        voltages = np.array([])
        print('Starting BiFi scan... ', end='')
        for pos in positions:
            self.set_bifi_motor_pos(pos)
            voltages = np.append(voltages, self.query('DPOW:DC?', numeric_result=True))
        self.set_bifi_motor_pos(center_pos)  # return back to where we started, just in case something goes wrong
        print('Done.')

        print('Analyzing scan data... ', end='')
        # Smooth out the data and find extrema
        smoothed_data = savgol_filter(voltages, window_length=cfg.get(cfg.BIFI_SMOOTHING_FILTER_WINDOW),
                                      polyorder=cfg.get(cfg.BIFI_SMOOTHING_FILTER_POLYORDER))
        maxima = argrelextrema(smoothed_data, np.greater, order=5)

        # Find the position of the extremum closest to the target wavelength
        wavelength_differences = np.array([])
        for pos in positions[maxima]:
            self.set_bifi_motor_pos(pos)
            time.sleep(0.01)
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[maxima][np.argmin(wavelength_differences)]
        self.set_bifi_motor_pos(best_pos)
        print('Done. ' + str(wavelength_differences))

        if cfg.get(cfg.BIFI_SCAN_SHOW_PLOTS):
            plot_process = BirefringentFilterScanPlotProcess(positions, voltages, smoothed_data, maxima, center_pos,
                                                             best_pos, daemon=True)
            self.plotting_processes.append(plot_process)
            plot_process.start()

        if repeat:
            new_diff = np.min(wavelength_differences)
            if abs(new_diff) > cfg.get(cfg.MEDIUM_WAVELENGTH_DRIFT):
                print('Wavelength still too far away from target value. Starting another scan.')
                self.birefringent_filter_scan(scan_range, repeat=True)

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
        assert cfg.get(cfg.WAVELENGTH_LOWER_LIMIT) < value < cfg.get(cfg.WAVELENGTH_UPPER_LIMIT), \
            'Target wavelength out of range.'
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

    def thin_etalon_scan(self, scan_range: int = None, repeat=False):
        """
        Initiate a scan of the thin etalon, selecting the reflex minimum closest to the target wavelength.

        Nudges the motor position a little bit away from the minimum to ensure good locking later.
        Additionally, plot the reflex data and motor position selection.
        """
        if self.exit_flag:
            return
        if self.target_wavelength is None:
            self.target_wavelength = self.wavemeter_wavelength()
        if scan_range is None:
            scan_range = cfg.get(cfg.THIN_ETA_SCAN_RANGE)

        old_pos = int(self.query('MOTTE:POS?', numeric_result=True))
        lower_end, upper_end = self.limits_for_thin_etalon_scan(old_pos, scan_range)

        positions = np.array(range(lower_end, upper_end, cfg.get(cfg.THIN_ETA_SCAN_STEP)))
        voltages = np.array([])
        print('Starting thin etalon scan... ', end='')
        for pos in positions:
            self.set_thin_etalon_motor_pos(pos)
            voltages = np.append(voltages, self.query('TE:DC?', numeric_result=True))
        self.set_thin_etalon_motor_pos(old_pos)  # return back to where we started, just in case something goes wrong
        print('Done.')

        print('Analyzing scan data... ', end='')
        # Smooth out the data and find extrema
        smoothed_data = savgol_filter(voltages, window_length=cfg.get(cfg.THIN_ETA_SMOOTHING_FILTER_WINDOW),
                                      polyorder=cfg.get(cfg.THIN_ETA_SMOOTHING_FILTER_POLYORDER))
        minima = argrelextrema(smoothed_data, np.less, order=5)

        # Find the position of the extremum closest to the target wavelength
        wavelength_differences = np.array([])
        for pos in positions[minima]:
            self.set_thin_etalon_motor_pos(pos)
            time.sleep(0.01)
            wavelength_differences = np.append(wavelength_differences,
                                               abs(self.wavemeter_wavelength() - self.target_wavelength))
        best_pos = positions[minima][np.argmin(wavelength_differences)] + cfg.get(cfg.THIN_ETA_NUDGE)
        self.set_thin_etalon_motor_pos(best_pos)
        print('Done. ' + str(wavelength_differences))

        if cfg.get(cfg.THIN_ETA_SHOW_PLOTS):
            plot_process = ThinEtalonScanPlotProcess(positions, voltages, smoothed_data, minima, old_pos, best_pos,
                                                     daemon=True)
            self.plotting_processes.append(plot_process)
            plot_process.start()

        if repeat:
            new_diff = np.min(wavelength_differences)
            if new_diff > cfg.get(cfg.SMALL_WAVELENGTH_DRIFT):
                print('Wavelength still too far away from target value. Starting another scan.')
                self.thin_etalon_scan(scan_range, repeat=True)

    def limits_for_thin_etalon_scan(self, current_pos: int, scan_range: int):
        lower_limit = current_pos - scan_range
        upper_limit = current_pos + scan_range
        diff = self.target_wavelength - self.wavemeter_wavelength()
        # Adjust scan limits if we're off by more than 1 mode
        if abs(diff) > Matisse.THIN_ETALON_NM_PER_MODE:
            if diff < 0:
                lower_limit = current_pos - scan_range
                upper_limit = current_pos
            else:
                lower_limit = current_pos
                upper_limit = current_pos + scan_range

        assert (0 < lower_limit < Matisse.THIN_ETALON_UPPER_LIMIT
                and 0 < upper_limit < Matisse.THIN_ETALON_UPPER_LIMIT
                and lower_limit < upper_limit), \
            'Conditions for thin etalon scan invalid. Continuing would put the motor at its upper or lower limit.'

        return lower_limit, upper_limit

    def set_thin_etalon_motor_pos(self, pos: int):
        assert (Matisse.THIN_ETALON_LOWER_LIMIT < pos < Matisse.THIN_ETALON_UPPER_LIMIT), \
            f"Can't set thin etalon motor position to {pos}, this is out of range."
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

    def laser_locked(self):
        return self.all_control_loops_on() and self.fast_piezo_locked()

    def stabilize_on(self):
        """
        Enable stabilization using the reference cell to keep the wavelength constant.

        Starts a StabilizationThread as a daemon for this purpose. To stop stabilizing and unlock the laser, call
        stabilize_off.
        """
        if self.is_stabilizing():
            print('WARNING: Already stabilizing laser. Call stabilize_off before trying to stabilize again.')
        else:
            self.stabilization_thread = StabilizationThread(self, queue.Queue(), daemon=True)

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

    def start_scan(self, mode):
        self.query(f"SCAN:MODE {mode}")
        self.query(f"SCAN:STATUS RUN")

    def stop_scan(self):
        self.query(f"SCAN:STATUS STOP")

    def is_scanning(self):
        return 'RUN' in self.query('SCAN:STATUS?')

    def is_stabilizing(self):
        return self.stabilization_thread is not None and self.stabilization_thread.is_alive()

    def get_stabilizing_piezo_positions(self):
        current_refcell_pos = self.query('SCAN:NOW?', numeric_result=True)
        current_slow_pz_pos = self.query('SLOWPIEZO:NOW?', numeric_result=True)
        current_pz_eta_pos = self.query('PIEZOETALON:BASELINE?', numeric_result=True)
        return current_refcell_pos, current_pz_eta_pos, current_slow_pz_pos

    def is_any_limit_reached(self):
        """Returns true if the RefCell, slow piezo, or piezo etalon are very close to one of their limits."""

        refcell_pos, pz_eta_pos, slow_pz_pos = self.get_stabilizing_piezo_positions()
        offset = cfg.get(cfg.COMPONENT_LIMIT_OFFSET)
        return not (self.REFERENCE_CELL_LOWER_LIMIT + offset < refcell_pos < self.REFERENCE_CELL_UPPER_LIMIT - offset
                    and self.SLOW_PIEZO_LOWER_LIMIT + offset < slow_pz_pos < self.SLOW_PIEZO_UPPER_LIMIT - offset
                    and self.PIEZO_ETALON_LOWER_LIMIT + offset < pz_eta_pos < self.PIEZO_ETALON_UPPER_LIMIT - offset)

    def reset_stabilization_piezos(self):
        """
        Reset the slow piezo to the center, and the RefCell and piezo etalon according to the following rules:
            If RefCell is at upper limit, piezo etalon is likely near lower limit
                If wavelength is still too low, move RefCell down lower than usual and piezo etalon higher than usual
            If RefCell is at lower limit, piezo etalon is likely near upper limit
                If wavelength is still too high, move RefCell up higher than usual and piezo etalon lower than usual
            Else,
                Move RefCell and piezo etalon to their center positions.

        A target wavelength must already be set in order to run this method.
        """
        current_refcell_pos, current_pz_eta_pos, current_slow_pz_pos = self.get_stabilizing_piezo_positions()
        current_wavelength = self.wavemeter_wavelength()

        offset = cfg.get(cfg.COMPONENT_LIMIT_OFFSET)
        if (current_refcell_pos > Matisse.REFERENCE_CELL_UPPER_LIMIT - offset
                and current_wavelength < self.target_wavelength):
            self.query(f"SCAN:NOW {cfg.get(cfg.REFCELL_LOWER_CORRECTION_POS)}")
            self.query(f"PIEZOETALON:BASELINE {cfg.get(cfg.PIEZO_ETA_UPPER_CORRECTION_POS)}")
        elif (current_refcell_pos < Matisse.REFERENCE_CELL_LOWER_LIMIT + offset
              and current_wavelength > self.target_wavelength):
            self.query(f"SCAN:NOW {cfg.get(cfg.REFCELL_UPPER_CORRECTION_POS)}")
            self.query(f"PIEZOETALON:BASELINE {cfg.get(cfg.PIEZO_ETA_LOWER_CORRECTION_POS)}")
        else:
            # TODO: Maybe check if we really need to move the piezo etalon
            self.query(f"PIEZOETALON:BASELINE {cfg.get(cfg.PIEZO_ETA_MID_CORRECTION_POS)}")

        self.query(f"SLOWPIEZO:NOW {cfg.get(cfg.SLOW_PIEZO_MID_CORRECTION_POS)}")

    # TODO: Make sure you're measuring the right value
    # TODO: Stop scanning and stabilizing when doing this
    def get_reference_cell_transmission_spectrum(self):
        positions = np.linspace(0.1, 0.6, 128)
        values = np.array([])
        old_refcell_pos = self.query(f"SCAN:NOW?", numeric_result=True)
        for pos in positions:
            self.query(f"SCAN:NOW {pos}")
            values = np.append(values, self.query('FASTPIEZO:INPUT?'))
        self.query(f"SCAN:NOW {old_refcell_pos}")
        return positions, values

    # TODO: Check that the Airy peaks don't wildly vary in height
    def set_recommended_fast_piezo_setpoint(self):
        positions, values = self.get_reference_cell_transmission_spectrum()
        setpoint = (np.max(values) + np.min(values)) / 2
        import matplotlib.pyplot as plt
        plt.plot(positions, values)
        plt.axhline(setpoint, 0, 1)
        print(f"Recommended fast piezo setpoint: {setpoint}")

    def start_laser_lock_correction(self):
        if self.is_lock_correction_on():
            print('WARNING: Lock correction is already running.')
        else:
            print('Starting laser lock.')
            self.lock_correction_thread = LockCorrectionThread(self, cfg.get(cfg.LOCKING_TIMEOUT), queue.Queue(),
                                                               daemon=True)
            if self.target_wavelength is None:
                self.target_wavelength = self.wavemeter_wavelength()
            self.lock_correction_thread.start()

    def stop_laser_lock_correction(self):
        if self.is_lock_correction_on():
            self.lock_correction_thread.messages.put('stop')
            self.lock_correction_thread.join()
        else:
            print('WARNING: laser is not locked.')

    def is_lock_correction_on(self):
        return self.lock_correction_thread is not None and self.lock_correction_thread.is_alive()
