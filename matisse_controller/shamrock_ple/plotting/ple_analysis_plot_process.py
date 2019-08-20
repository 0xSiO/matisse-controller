"""Provides a class to plot wavelengths and counts for PLE scans."""

import multiprocessing
from multiprocessing.connection import Connection

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


class PLEAnalysisPlotProcess(multiprocessing.Process):
    def __init__(self, analysis_data=None, pipe: Connection = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if analysis_data:
            self.wavelengths = list(analysis_data.keys())
            self.counts = list(analysis_data.values())
        else:
            self.wavelengths = []
            self.counts = []
        self.pipe = pipe
        self.figure: Figure = plt.figure(f"PLE Scan Analysis")
        self.axes: Axes = plt.gca()
        self.setup_axes()

    def setup_axes(self):
        self.axes.set_title('Total Counts vs. Laser Wavelength')
        self.axes.set_xlabel('Wavelength (nm)')
        self.axes.set_ylabel('Counts')

    def run(self):
        if self.pipe:
            try:
                while self.pipe.poll(timeout=None):
                    data = self.pipe.recv()
                    if data:
                        self.add_point_to_plot(*data)
                    else:
                        break
            except BrokenPipeError:
                pass
            except EOFError:
                pass
        else:
            self.plot_data(self.wavelengths, self.counts)
        plt.show()

    def plot_data(self, wavelengths, counts):
        self.axes.set_xlim(wavelengths[0], wavelengths[-1])
        self.axes.plot(wavelengths, counts)
        plt.pause(0.001)

    def add_point_to_plot(self, wavelength, counts):
        self.wavelengths.append(wavelength)
        self.counts.append(counts)
        self.axes.cla()
        self.setup_axes()
        self.plot_data(self.wavelengths, self.counts)
