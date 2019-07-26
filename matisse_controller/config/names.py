# These names specify keys in the configuration.CONFIGURATION dictionary. Make sure that any new entries have a default
# value set in configuration.DEFAULTS, otherwise you'll get a KeyError when trying to access them.

MATISSE_DEVICE_ID = 'matisse.device_id'

BIFI_SCAN_RANGE = 'matisse.scanning.birefringent_filter.range'
BIFI_SCAN_RANGE_SMALL = 'matisse.scanning.birefringent_filter.range_small'
BIFI_SCAN_STEP = 'matisse.scanning.birefringent_filter.step'

THIN_ETA_SCAN_RANGE = 'matisse.scanning.thin_etalon.range'
THIN_ETA_SCAN_RANGE_SMALL = 'matisse.scanning.thin_etalon.range_small'
THIN_ETA_SCAN_STEP = 'matisse.scanning.thin_etalon.step'
THIN_ETA_NUDGE = 'matisse.scanning.thin_etalon.nudge'

REFCELL_SCAN_RISING_SPEED = 'matisse.scanning.refcell.rising_speed'
REFCELL_SCAN_FALLING_SPEED = 'matisse.scanning.refcell.falling_speed'

LARGE_WAVELENGTH_DRIFT = 'matisse.scanning.wavelength_drift.large'
MEDIUM_WAVELENGTH_DRIFT = 'matisse.scanning.wavelength_drift.medium'
SMALL_WAVELENGTH_DRIFT = 'matisse.scanning.wavelength_drift.small'

LOCKING_TIMEOUT = 'matisse.locking.timeout'

STABILIZATION_RISING_SPEED = 'matisse.stabilization.rising_speed'
STABILIZATION_FALLING_SPEED = 'matisse.stabilization.falling_speed'
STABILIZATION_DELAY = 'matisse.stabilization.delay'

PIEZO_ETA_CORRECTION_POS = 'matisse.correction.piezo_etalon_pos'
SLOW_PIEZO_CORRECTION_POS = 'matisse.correction.slow_piezo_pos'
REFCELL_CORRECTION_POS = 'matisse.correction.refcell_pos'

WAVEMETER_PORT = 'wavemeter.port'
WAVEMETER_PRECISION = 'wavemeter.precision'
