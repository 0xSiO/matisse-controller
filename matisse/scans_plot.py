import matplotlib.pyplot as plt
from matplotlib.axes import Axes


class ScansPlot:
    def __init__(self):
        self._birefringent_scan_plot: Axes = plt.subplot(2, 1, 1)
        self._thin_etalon_scan_plot: Axes = plt.subplot(2, 1, 2)

    def plot_birefringent_scan(self, positions, voltages, smoothed_voltages):
        axes = self._birefringent_scan_plot
        axes.cla()
        axes.set_title('Power Diode Voltage vs. BiFi Motor Position')
        axes.set_xlim(positions[0], positions[-1])
        axes.set_xlabel('Position')
        axes.set_ylabel('Voltage (V)')
        axes.plot(positions, voltages)
        axes.plot(positions, smoothed_voltages)

    def plot_birefringent_maxima(self, positions, voltages):
        axes = self._birefringent_scan_plot
        axes.plot(positions, voltages, 'r*')

    def plot_birefringent_selection(self, position):
        axes = self._birefringent_scan_plot
        axes.axvline(position, 0, 1, color='r', linestyle='--')

    def add_bifi_scan_legend(self):
        self._birefringent_scan_plot.legend(['Raw', 'Smoothed', 'Selection'], loc='upper left')

    def plot_thin_etalon_scan(self, positions, voltages, smoothed_voltages):
        axes = self._thin_etalon_scan_plot
        axes.cla()
        axes.set_title('Thin Etalon Reflex Voltage vs. Thin Etalon Motor Position')
        axes.set_xlim(positions[0], positions[-1])
        axes.set_xlabel('Position')
        axes.set_ylabel('Voltage (V)')
        axes.plot(positions, voltages)
        axes.plot(positions, smoothed_voltages)

    def plot_thin_etalon_minima(self, positions, voltages):
        axes = self._thin_etalon_scan_plot
        axes.plot(positions, voltages, 'r*')

    def plot_thin_etalon_selection(self, position):
        axes = self._thin_etalon_scan_plot
        axes.axvline(position, 0, 1, color='r', linestyle='--')

    def add_thin_etalon_scan_legend(self):
        self._thin_etalon_scan_plot.legend(['Raw', 'Smoothed', 'Selection'], loc='upper left')
