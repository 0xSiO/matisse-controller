import matplotlib.pyplot as plt


# TODO: See https://matplotlib.org/api/animation_api.html for real-time plotting
class ScanPlots:
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
