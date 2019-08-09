"""Provides a class to plot wavelengths and counts for PLE scans."""

import multiprocessing

import matplotlib.pyplot as plt


class PLEAnalysisPlotProcess(multiprocessing.Process):
    def __init__(self, analysis_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wavelengths = list(analysis_data.keys())
        self.counts = list(analysis_data.values())

    def run(self):
        plt.figure(f"PLE Scan: {self.wavelengths[0]} to {self.wavelengths[-1]}")
        plt.cla()
        plt.title('Total Counts vs. Laser Wavelength')
        plt.xlim(self.wavelengths[0], self.wavelengths[-1])
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Counts')
        plt.plot(self.wavelengths, self.counts)
        plt.show()
