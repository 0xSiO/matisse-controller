# TODO: Check the 'small' scan ranges
class Constants:
    # Scanning ################################################################

    BIREFRINGENT_SCAN_RANGE = 300
    BIREFRINGENT_SCAN_RANGE_SMALL = 150
    BIREFRINGENT_SCAN_STEP = 3

    THIN_ETALON_SCAN_RANGE = 1000
    THIN_ETALON_SCAN_RANGE_SMALL = 500
    THIN_ETALON_SCAN_STEP = 10

    # Approximate change in wavelength per unit motor movement
    THIN_ETALON_NM_PER_STEP = 7.08589e-05

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
