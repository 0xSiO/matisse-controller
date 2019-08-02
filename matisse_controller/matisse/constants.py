class Constants:
    """Important Matisse-related non-configurable constants."""

    # Scanning ################################################################

    SCAN_MODE_UP = 0
    SCAN_MODE_DOWN = 1

    # Approximate change in wavelength per thin etalon mode
    THIN_ETALON_NM_PER_MODE = 0.033

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
