MATISSE_DEVICE_ID = 'An NI-VISA instrument descriptor for the Matisse.'
WAVEMETER_PORT = 'The serial port to use for reading from the wavemeter.'
WAVEMETER_PRECISION = 'Precision of the readings from the wavemeter. 1 -> 0.1, 2 -> 0.01, 3 -> 0.001, etc.'

COMPONENT_LIMIT_OFFSET = 'How close should a component be to its limit before automatically taking an appropriate action?'

WAVELENGTH_LOWER_LIMIT = 'The lowest wavelength the Matisse is capable of producing.'
WAVELENGTH_UPPER_LIMIT = 'The highest wavelength the Matisse is capable of producing.'

BIFI_SCAN_RANGE = 'Total amount of motor steps to move (left and right) when doing a BiFi scan.'
BIFI_SCAN_RANGE_SMALL = 'Total amount of motor steps to move (left and right) when doing a small BiFi scan.'
BIFI_SCAN_STEP = 'Amount of motor steps to increment when doing a BiFi scan.'
BIFI_SCAN_SHOW_PLOTS = 'Should we open matplotlib windows after a BiFi scan?'
BIFI_SMOOTHING_FILTER_WINDOW = 'Smaller -> more accurate, less smooth. Larger -> less accurate, more smooth. See scipy.signal.savgol_filter.'
BIFI_SMOOTHING_FILTER_POLYORDER = 'Savitzky-Golay filter parameter for BiFi scan. See scipy.signal.savgol_filter.'

THIN_ETA_SCAN_RANGE = 'Total amount of motor steps to move (left and right) when doing a thin etalon scan.'
THIN_ETA_SCAN_RANGE_SMALL = 'Total amount of motor steps to move (left and right) when doing a small thin etalon scan.'
THIN_ETA_SCAN_STEP = 'Amount of motor steps to increment when doing a thin etalon scan.'
THIN_ETA_NUDGE = 'Amount of motor steps to move after a thin etalon scan has finished.'
THIN_ETA_SHOW_PLOTS = 'Should we open matplotlib windows after a thin etalon scan?'
THIN_ETA_SMOOTHING_FILTER_WINDOW = 'Smaller -> more accurate, less smooth. Larger -> less accurate, more smooth. See scipy.signal.savgol_filter.'
THIN_ETA_SMOOTHING_FILTER_POLYORDER = 'Savitzky-Golay filter parameter for thin etalon scan. See scipy.signal.savgol_filter.'

REFCELL_SCAN_RISING_SPEED = "The speed at which the RefCell increases when using 'Scan Device Up'"
REFCELL_SCAN_FALLING_SPEED = "The speed at which the RefCell decreases when using 'Scan Device Down'"

LARGE_WAVELENGTH_DRIFT = 'Definition of large drift, in nanometers. The BiFi is primarily used to correct this drift.'
MEDIUM_WAVELENGTH_DRIFT = 'Definition of medium drift, in nanometers. The thin etalon is primarily used to correct this drift.'
SMALL_WAVELENGTH_DRIFT = 'Definition of small drift, in nanometers. The RefCell is primarily used to correct this drift.'

LOCKING_TIMEOUT = 'How long to wait, in seconds, before giving up on locking the laser.'

STABILIZATION_RISING_SPEED = 'The speed at which the RefCell increases when using auto-stabilization.'
STABILIZATION_FALLING_SPEED = 'The speed at which the RefCell decreases when using auto-stabilization.'
STABILIZATION_DELAY = 'How long to wait, in seconds, between each auto-stabilization loop.'
STABILIZATION_TOLERANCE = 'How much drift is tolerated, in nanometers, when auto-stabilizing.'

PIEZO_ETA_UPPER_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos_upper'
SLOW_PIEZO_UPPER_CORRECTION_POS = 'matisse.correction.slow_piezo_pos_upper'
REFCELL_UPPER_CORRECTION_POS = 'matisse.correction.refcell_pos_upper'
PIEZO_ETA_MID_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos_mid'
SLOW_PIEZO_MID_CORRECTION_POS = 'matisse.correction.slow_piezo_pos_mid'
REFCELL_MID_CORRECTION_POS = 'matisse.correction.refcell_pos_mid'
PIEZO_ETA_LOWER_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos_lower'
SLOW_PIEZO_LOWER_CORRECTION_POS = 'matisse.correction.slow_piezo_pos_lower'
REFCELL_LOWER_CORRECTION_POS = 'matisse.correction.refcell_pos_lower'
