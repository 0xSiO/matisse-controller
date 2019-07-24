# TODO: Check the 'small' scan ranges
# TODO: Some of these constants must stay constant, others can be optionally configured
class Constants:
    # Scanning ################################################################

    LARGE_WAVELENGTH_DRIFT = 0.4
    MEDIUM_WAVELENGTH_DRIFT = 0.2
    SMALL_WAVELENGTH_DRIFT = 0.02

    BIREFRINGENT_SCAN_RANGE = 400
    BIREFRINGENT_SCAN_RANGE_SMALL = 200
    BIREFRINGENT_SCAN_STEP = 4

    THIN_ETALON_SCAN_RANGE = 2000
    THIN_ETALON_SCAN_RANGE_SMALL = 1000
    THIN_ETALON_SCAN_STEP = 10

    # Approximate change in wavelength per unit motor movement
    THIN_ETALON_NM_PER_STEP = 5.797738e-05
    # Approximate change in wavelength per thin etalon mode
    THIN_ETALON_NM_PER_MODE = 0.033

    # TODO: Confirm this parameter is ok to use, flank seems to default to 'left'?
    THIN_ETALON_NUDGE = -50

    # Internal Matisse constant. Encoded in the result of a motor's STATUS? command
    MOTOR_STATUS_IDLE = 0x02

    # Limits ##################################################################

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

    # Locking/Correction ######################################################

    # Amount of time to wait, in seconds, before giving up on locking the laser.
    LOCKING_TIMEOUT = 7.0

    # Default correction positions when a limit is reached
    PIEZO_ETALON_CORRECTION_POS = 0
    SLOW_PIEZO_CORRECTION_POS = 0.35
    REFCELL_CORRECTION_POS = 0.35
