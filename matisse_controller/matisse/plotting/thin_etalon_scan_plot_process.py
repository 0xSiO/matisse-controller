"""Provides a class to plot positions and voltages for thin etalon scans."""

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
        self.plot_thin_etalon_scan()
        self.plot_thin_etalon_selection()
        self.plot_thin_etalon_minima()
        self.add_thin_etalon_scan_legend()
        plt.show()

    def plot_thin_etalon_scan(self):
        plt.figure(f"Thin Etalon Scan: {self.positions[0]} to {self.positions[-1]}")
        plt.cla()
        plt.title('Thin Etalon Reflex Voltage vs. Thin Etalon Motor Position')
        plt.xlim(self.positions[0], self.positions[-1])
        plt.xlabel('Position')
        plt.ylabel('Voltage (V)')
        plt.plot(self.positions, self.voltages)
        plt.plot(self.positions, self.smoothed_data)

    def plot_thin_etalon_minima(self):
        plt.plot(self.positions[self.minima], self.smoothed_data[self.minima], 'r*')

    def plot_thin_etalon_selection(self):
        plt.axvline(self.old_pos, 0, 1, color='r', linestyle='--')
        if self.using_new_pos:
            plt.axvline(self.best_pos, 0, 1, color='r', linestyle='-')

    def add_thin_etalon_scan_legend(self):
        names = ['Raw', 'Smoothed', 'Old Pos']
        if self.using_new_pos:
            names.append('New Pos')
        plt.legend(names, loc='upper left')
