from contextlib import AbstractContextManager


class ControlLoopsOn(AbstractContextManager):
    def __init__(self, matisse):
        """
        :param matisse:
        :type matisse: matisse.Matisse
        """
        self.matisse = matisse

    def __enter__(self):
        print('Starting control loops... ', end='')
        self.matisse.set_slow_piezo_control(True)
        self.matisse.set_thin_etalon_control(True)
        self.matisse.set_piezo_etalon_control(True)
        self.matisse.set_fast_piezo_control(True)
        assert self.matisse.all_control_loops_on()
        print('Done.')

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Stopping control loops... ', end='')
        self.matisse.set_fast_piezo_control(False)
        self.matisse.set_piezo_etalon_control(False)
        self.matisse.set_thin_etalon_control(False)
        self.matisse.set_slow_piezo_control(False)
        print('Done.')