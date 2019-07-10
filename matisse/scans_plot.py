from matplotlib.axes import Axes
import matplotlib.pyplot as plt


class ScansPlot:
    def __init__(self):
        self.birefringent_scan_plot: Axes = plt.subplot(3, 1, 1)
        self.thin_etalon_scan_plot: Axes = plt.subplot(3, 1, 2)
        self.piezo_etalon_scan_plot: Axes = plt.subplot(3, 1, 3)

    def plot_birefringent_scan(self, positions, powers):
        bsp = self.birefringent_scan_plot
        bsp.set_title('Power Diode Voltage vs. BiFi Motor Position')
        bsp.set_xlim(positions[0], positions[-1])
        bsp.set_xlabel('Position')
        bsp.set_ylabel('Voltage (V)')
        bsp.plot(positions, powers)
