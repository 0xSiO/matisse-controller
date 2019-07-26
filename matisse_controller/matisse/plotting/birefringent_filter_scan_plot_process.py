import multiprocessing

import matplotlib.pyplot as plt


class BirefringentFilterScanPlotProcess(multiprocessing.Process):
    def __init__(self, positions, voltages, smoothed_data, maxima, best_pos, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.positions = positions
        self.voltages = voltages
        self.smoothed_data = smoothed_data
        self.maxima = maxima
        self.best_pos = best_pos

    def run(self):
        self.plot_birefringent_scan(self.positions, self.voltages, self.smoothed_data)
        self.plot_birefringent_selection(self.best_pos)
        self.plot_birefringent_maxima(self.positions[self.maxima], self.smoothed_data[self.maxima])
        self.add_bifi_scan_legend()
        plt.show()

    def plot_birefringent_scan(self, positions, voltages, smoothed_voltages):
        plt.figure()
        plt.cla()
        plt.title('Power Diode Voltage vs. BiFi Motor Position')
        plt.xlim(positions[0], positions[-1])
        plt.xlabel('Position')
        plt.ylabel('Voltage (V)')
        plt.plot(positions, voltages)
        plt.plot(positions, smoothed_voltages)

    def plot_birefringent_maxima(self, positions, voltages):
        plt.plot(positions, voltages, 'r*')

    def plot_birefringent_selection(self, position):
        plt.axvline(position, 0, 1, color='r', linestyle='--')

    def add_bifi_scan_legend(self):
        plt.legend(['Raw', 'Smoothed', 'Selection'], loc='upper left')
