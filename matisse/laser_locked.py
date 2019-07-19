from contextlib import AbstractContextManager


class LaserLocked(AbstractContextManager):
    def __init__(self, matisse):
        """
        :param matisse:
        :type matisse: matisse.Matisse
        """
        self.matisse = matisse

    def __enter__(self):
        print('Locking laser... ', end='')
        self.matisse.set_slow_piezo_lock(True)
        self.matisse.set_thin_etalon_lock(True)
        self.matisse.set_piezo_etalon_lock(True)
        self.matisse.set_fast_piezo_lock(True)
        self.matisse.assert_locked()
        print('Done.')

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Unlocking laser... ', end='')
        self.matisse.set_fast_piezo_lock(False)
        self.matisse.set_piezo_etalon_lock(False)
        self.matisse.set_thin_etalon_lock(False)
        self.matisse.set_slow_piezo_lock(False)
        print('Done.')
