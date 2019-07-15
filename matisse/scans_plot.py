from matplotlib.axes import Axes
import matplotlib.pyplot as plt


class ScansPlot:
    def __init__(self):
        self._birefringent_scan_plot: Axes = plt.subplot(2, 1, 1)
        self._thin_etalon_scan_plot: Axes = plt.subplot(2, 1, 2)

    def plot_birefringent_scan(self, positions, voltages):
        axes = self._birefringent_scan_plot
        axes.cla()
        axes.set_title('Power Diode Voltage vs. BiFi Motor Position')
        axes.set_xlim(positions[0], positions[-1])
        axes.set_xlabel('Position')
        axes.set_ylabel('Voltage (V)')
        axes.plot(positions, voltages)
        print(positions)
        print(voltages)

    def plot_thin_etalon_scan(self, positions, voltages):
        axes = self._thin_etalon_scan_plot
        axes.cla()
        axes.set_title('Thin Etalon Reflex Voltage vs. Thin Etalon Motor Position')
        axes.set_xlim(positions[0], positions[-1])
        axes.set_xlabel('Position')
        axes.set_ylabel('Voltage (V)')
        axes.plot(positions, voltages)
        print(positions)
        print(voltages)
