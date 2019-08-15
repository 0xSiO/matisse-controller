MATISSE_DEVICE_ID = 'An NI-VISA instrument descriptor for the Matisse.'
WAVEMETER_PORT = 'The serial port to use for reading from the wavemeter.'
WAVEMETER_PRECISION = 'Precision of the readings from the wavemeter. 1 -> 0.1, 2 -> 0.01, 3 -> 0.001, etc.'
WAVEMETER_MEASUREMENT_DELAY = 'The delay, in seconds, to wait before reading a measurement from the wavemeter during a scan.'

STATUS_MONITOR_DELAY = 'The delay, in seconds, between each update of the status monitor at the bottom of the window.'
STATUS_MONITOR_FONT_SIZE = 'The font size of the status monitor at the bottom of the window.'

BIFI_RESET_POS = 'The position at which to set the birefringent motor during a reset operation.'
THIN_ETA_RESET_POS = 'The position at which to set the thin etalon motor during a reset operation, or before a large scan.'

REPORT_EVENTS = 'Should we log important events (like an automatic correction while stabilizing) to a CSV file?'

COMPONENT_LIMIT_OFFSET = 'How close should a component be to its limit before automatically taking an appropriate action?'

WAVELENGTH_LOWER_LIMIT = 'The lowest wavelength the Matisse is capable of producing.'
WAVELENGTH_UPPER_LIMIT = 'The highest wavelength the Matisse is capable of producing.'

SCAN_LIMIT = 'The number of scans allowed before giving up and restarting the wavelength-setting process.'

BIFI_SCAN_RANGE = 'Total amount of motor steps to move (left and right) when doing a BiFi scan.'
BIFI_SCAN_RANGE_SMALL = 'Total amount of motor steps to move (left and right) when doing a small BiFi scan.'
BIFI_SCAN_STEP = 'Amount of motor steps to increment when doing a BiFi scan.'
BIFI_SCAN_SHOW_PLOTS = 'Should we open matplotlib windows after a BiFi scan?'
BIFI_SMOOTHING_FILTER_WINDOW = 'Smaller -> more accurate, less smooth. Larger -> less accurate, more smooth. See scipy.signal.savgol_filter.'
BIFI_SMOOTHING_FILTER_POLYORDER = 'Savitzky-Golay filter parameter for BiFi scan. See scipy.signal.savgol_filter.'

THIN_ETA_SCAN_RANGE = 'Total amount of motor steps to move (left and right) when doing a thin etalon scan.'
THIN_ETA_SCAN_RANGE_SMALL = 'Total amount of motor steps to move (left and right) when doing a small thin etalon scan.'
THIN_ETA_RAND_RANGE = 'Limit for range of thin etalon randomization away from the reset position when starting the wavelength-setting process.'
THIN_ETA_SCAN_STEP = 'Amount of motor steps to increment when doing a thin etalon scan.'
THIN_ETA_NUDGE = 'Amount of motor steps to move after a thin etalon scan has finished.'
THIN_ETA_SHOW_PLOTS = 'Should we open matplotlib windows after a thin etalon scan?'
THIN_ETA_SMOOTHING_FILTER_WINDOW = 'Smaller -> more accurate, less smooth. Larger -> less accurate, more smooth. See scipy.signal.savgol_filter.'
THIN_ETA_SMOOTHING_FILTER_POLYORDER = 'Savitzky-Golay filter parameter for thin etalon scan. See scipy.signal.savgol_filter.'
THIN_ETA_MAX_ALLOWED_STDDEV = 'Maximum normalized RMS deviation from smoothed curve allowed before restarting the wavelength-setting process.'

REFCELL_SCAN_RISING_SPEED = "The speed at which the RefCell increases when using 'Scan Device Up'"
REFCELL_SCAN_FALLING_SPEED = "The speed at which the RefCell decreases when using 'Scan Device Down'"

LARGE_WAVELENGTH_DRIFT = 'Definition of large drift, in nanometers. The BiFi is primarily used to correct this drift.'
MEDIUM_WAVELENGTH_DRIFT = 'Definition of medium drift, in nanometers. The thin etalon is primarily used to correct this drift.'
SMALL_WAVELENGTH_DRIFT = 'Definition of small drift, in nanometers. The RefCell is primarily used to correct this drift.'

LOCKING_TIMEOUT = 'How long to wait, in seconds, before giving up on locking the laser.'
FAST_PZ_SETPOINT_SCAN_LOWER_LIMIT = 'Lower limit for the RefCell scan performed when measuring the input to the fast piezo.'
FAST_PZ_SETPOINT_SCAN_UPPER_LIMIT = 'Upper limit for the RefCell scan performed when measuring the input to the fast piezo.'
FAST_PZ_SETPOINT_NUM_POINTS = 'Number of points to sample during the RefCell scan performed when measuring the input to the fast piezo.'
FAST_PZ_SETPOINT_NUM_SCANS = 'Number of RefCell scans to average together when finding the recommended fast piezo setpoint.'

STABILIZATION_RISING_SPEED = 'The speed at which the RefCell increases when using auto-stabilization.'
STABILIZATION_FALLING_SPEED = 'The speed at which the RefCell decreases when using auto-stabilization.'
STABILIZATION_DELAY = 'How long to wait, in seconds, between each auto-stabilization loop.'
STABILIZATION_TOLERANCE = 'How much drift is tolerated, in nanometers, when auto-stabilizing.'

CORRECTION_LIMIT = 'Number of auto-corrections allowed during stabilization before restarting the wavelength-setting process.'

PLE_TARGET_TEMPERATURE = 'Default target temperature at which to cool down the CCD camera.'
PLE_TEMPERATURE_TOLERANCE = 'When cooling down the CCD, the temperature still fluctuates several degrees. How many degrees should we allow the CCD to drift before waiting to cool again?'
