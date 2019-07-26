import multiprocessing

import matplotlib.pyplot as plt


class ThinEtalonScanPlotProcess(multiprocessing.Process):
    def __init__(self, positions, voltages, smoothed_data, minima, best_pos, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = positions
        self.voltages = voltages
        self.smoothed_data = smoothed_data
        self.minima = minima
        self.best_pos = best_pos

    def run(self):
        self.plot_thin_etalon_scan(self.positions, self.voltages, self.smoothed_data)
        self.plot_thin_etalon_selection(self.best_pos)
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

    def plot_thin_etalon_selection(self, position):
        plt.axvline(position, 0, 1, color='r', linestyle='--')

    def add_thin_etalon_scan_legend(self):
        plt.legend(['Raw', 'Smoothed', 'Selection'], loc='upper left')
