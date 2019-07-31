# These names specify keys in the configuration.CONFIGURATION dictionary. Make sure that any new entries have a default
# value set in configuration.DEFAULTS, otherwise you'll get a KeyError when trying to access them.

MATISSE_DEVICE_ID = 'matisse.device_id'
WAVEMETER_PORT = 'wavemeter.port'
WAVEMETER_PRECISION = 'wavemeter.precision'

COMPONENT_LIMIT_OFFSET = 'matisse.component_limit_offset'

WAVELENGTH_LOWER_LIMIT = 'matisse.wavelength.lower_limit'
WAVELENGTH_UPPER_LIMIT = 'matisse.wavelength.upper_limit'

SCAN_LIMIT = 'matisse.scanning.limit'

BIFI_SCAN_RANGE = 'matisse.scanning.birefringent_filter.range'
BIFI_SCAN_RANGE_SMALL = 'matisse.scanning.birefringent_filter.range_small'
BIFI_SCAN_STEP = 'matisse.scanning.birefringent_filter.step'
BIFI_SCAN_SHOW_PLOTS = 'matisse.scanning.birefringent_filter.show_plots'
BIFI_SMOOTHING_FILTER_WINDOW = 'matisse.scanning.birefringent_filter.smoothing_filter.window'
BIFI_SMOOTHING_FILTER_POLYORDER = 'matisse.scanning.birefringent_filter.smoothing_filter.polyorder'

THIN_ETA_SCAN_RANGE = 'matisse.scanning.thin_etalon.range'
THIN_ETA_SCAN_RANGE_SMALL = 'matisse.scanning.thin_etalon.range_small'
THIN_ETA_SCAN_STEP = 'matisse.scanning.thin_etalon.step'
THIN_ETA_NUDGE = 'matisse.scanning.thin_etalon.nudge'
THIN_ETA_SHOW_PLOTS = 'matisse.scanning.thin_etalon.show_plots'
THIN_ETA_SMOOTHING_FILTER_WINDOW = 'matisse.scanning.thin_etalon.smoothing_filter.window'
THIN_ETA_SMOOTHING_FILTER_POLYORDER = 'matisse.scanning.thin_etalon.smoothing_filter.polyorder'

REFCELL_SCAN_RISING_SPEED = 'matisse.scanning.refcell.rising_speed'
REFCELL_SCAN_FALLING_SPEED = 'matisse.scanning.refcell.falling_speed'

LARGE_WAVELENGTH_DRIFT = 'matisse.scanning.wavelength_drift.large'
MEDIUM_WAVELENGTH_DRIFT = 'matisse.scanning.wavelength_drift.medium'
SMALL_WAVELENGTH_DRIFT = 'matisse.scanning.wavelength_drift.small'

LOCKING_TIMEOUT = 'matisse.locking.timeout'
FAST_PZ_SETPOINT_SCAN_LOWER_LIMIT = 'matisse.locking.fast_piezo_setpoint.refcell_lower_limit'
FAST_PZ_SETPOINT_SCAN_UPPER_LIMIT = 'matisse.locking.fast_piezo_setpoint.refcell_upper_limit'
FAST_PZ_SETPOINT_NUM_POINTS = 'matisse.locking.fast_piezo_setpoint.num_points'
FAST_PZ_SETPOINT_NUM_SCANS = 'matisse.locking.fast_piezo_setpoint.num_scans'

STABILIZATION_RISING_SPEED = 'matisse.stabilization.rising_speed'
STABILIZATION_FALLING_SPEED = 'matisse.stabilization.falling_speed'
STABILIZATION_DELAY = 'matisse.stabilization.delay'
STABILIZATION_TOLERANCE = 'matisse.stabilization.tolerance'

PIEZO_ETA_UPPER_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos_upper'
SLOW_PIEZO_UPPER_CORRECTION_POS = 'matisse.correction.slow_piezo_pos_upper'
REFCELL_UPPER_CORRECTION_POS = 'matisse.correction.refcell_pos_upper'
PIEZO_ETA_MID_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos_mid'
SLOW_PIEZO_MID_CORRECTION_POS = 'matisse.correction.slow_piezo_pos_mid'
REFCELL_MID_CORRECTION_POS = 'matisse.correction.refcell_pos_mid'
PIEZO_ETA_LOWER_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos_lower'
SLOW_PIEZO_LOWER_CORRECTION_POS = 'matisse.correction.slow_piezo_pos_lower'
REFCELL_LOWER_CORRECTION_POS = 'matisse.correction.refcell_pos_lower'
