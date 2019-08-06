"""A module providing functions to report wavelength drift and other important events to a CSV file."""

import csv
import os.path
from datetime import datetime
from enum import Enum

FILE_NAME = 'matisse_event_report.csv'
FIELDS = ['timestamp', 'event_type', 'current_wavelength', 'bifi_pos', 'thin_etalon_pos', 'refcell_pos',
          'piezo_etalon_pos', 'slow_piezo_pos', 'is_stabilizing', 'is_locked', 'other_comments']


class EventType(Enum):
    """An enumeration of different event types. The assigned value goes in each row of the CSV report."""
    SCAN_LIMIT_EXCEEDED = 'scan_limit_exceeded'
    LOCK_CORRECTION = 'lock_correction'
    STABILIZATION_CORRECTION = 'stabilization_correction'
    STABILIZATION_LIMIT_EXCEEDED = 'stabilization_correction_limit_exceeded'
    WAVELENGTH_DRIFT = 'wavelength_drift'


def log_event(event_type: EventType, matisse, current_wavelength: float, other_comments=''):
    """
    Write an event to the Matisse event report CSV file.

    Parameters
    ----------
    event_type : EventType
        a member of `EventType` describing the type of event that occurred
    matisse : matisse_controller.matisse.matisse.Matisse
    current_wavelength : float
        the wavelength at which this event occurred
    other_comments : str
        additional information to include with the event
    """
    with open(FILE_NAME, 'a', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, FIELDS)
        if os.path.getsize(FILE_NAME) == 0:
            writer.writeheader()
        bifi_pos = matisse.query('MOTBI:POS?', numeric_result=True)
        thin_eta_pos = matisse.query('MOTTE:POS?', numeric_result=True)
        refcell_pos, pz_eta_pos, slow_pz_pos = matisse.get_stabilizing_piezo_positions()
        event_details = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'event_type': event_type.value,
            'current_wavelength': current_wavelength,
            'bifi_pos': bifi_pos,
            'thin_etalon_pos': thin_eta_pos,
            'refcell_pos': refcell_pos,
            'piezo_etalon_pos': pz_eta_pos,
            'slow_piezo_pos': slow_pz_pos,
            'is_stabilizing': matisse.is_stabilizing(),
            'is_locked': matisse.laser_locked(),
            'other_comments': other_comments
        }
        writer.writerow(event_details)
