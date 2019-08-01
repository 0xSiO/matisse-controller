import multiprocessing

import matplotlib.pyplot as plt


class ThinEtalonScanPlotProcess(multiprocessing.Process):
    def __init__(self, positions, voltages, smoothed_data, minima, old_pos, best_pos, using_new_pos, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = positions
        self.voltages = voltages
        self.smoothed_data = smoothed_data
        self.minima = minima
        self.old_pos = old_pos
        self.best_pos = best_pos
        self.using_new_pos = using_new_pos

    def run(self):
        self.plot_thin_etalon_scan(self.positions, self.voltages, self.smoothed_data)
        self.plot_thin_etalon_selection(self.old_pos, self.best_pos)
        self.plot_thin_etalon_minima(self.positions[self.minima], self.smoothed_data[self.minima])
        self.add_thin_etalon_scan_legend()
        plt.show()

    def plot_thin_etalon_scan(self, positions, voltages, smoothed_voltages):
        plt.figure()
        plt.cla()
        plt.title('Thin Etalon Reflex Voltage vs. Thin Etalon Motor Position')
        plt.xlim(positions[0], positions[-1])
        plt.xlabel('Position')
        plt.ylabel('Voltage (V)')
        plt.plot(positions, voltages)
        plt.plot(positions, smoothed_voltages)

    def plot_thin_etalon_minima(self, positions, voltages):
        plt.plot(positions, voltages, 'r*')

    def plot_thin_etalon_selection(self, old_pos, new_pos):
        plt.axvline(old_pos, 0, 1, color='r', linestyle='--')
        if self.using_new_pos:
            plt.axvline(new_pos, 0, 1, color='r', linestyle='-')

    def add_thin_etalon_scan_legend(self):
        names = ['Raw', 'Smoothed', 'Old Pos']
        if self.using_new_pos:
            names.append('New Pos')
        plt.legend(names, loc='upper left')
