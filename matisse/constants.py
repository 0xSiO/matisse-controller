class Constants:
    # How far to each side should we scan the BiFi?
    BIREFRINGENT_SCAN_RANGE = 300
    # How far apart should each point be spaced when measuring the diode power?
    BIREFRINGENT_SCAN_STEP = 3
    THIN_ETALON_SCAN_RANGE = 1000  # TODO: Decrease this, it takes too long
    THIN_ETALON_SCAN_STEP = 10

    # TODO: Confirm this parameter is ok to use, flank seems to default to 'left'?
    THIN_ETALON_NUDGE = -50

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

    PIEZO_ETALON_CORRECTION_POS = 0
    SLOW_PIEZO_CORRECTION_POS = 0.35
    REFCELL_CORRECTION_POS = 0.35

    MOTOR_STATUS_IDLE = 0x02
