from multiprocessing import Process
from multiprocessing.connection import Connection

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


class SpectrumPlotProcess(Process):
    def __init__(self, wavelengths=None, counts=None, pipe: Connection = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wavelengths = wavelengths
        self.counts = counts
        self.pipe = pipe
        self.figure: Figure = plt.figure('CCD Acquisition')
        self.axes: Axes = plt.gca()
        self.axes.set_title('Counts vs. Wavelength')
        self.axes.set_xlabel('Wavelength (nm)')
        self.axes.set_ylabel('Counts')

    def run(self):
        if self.pipe:
            try:
                while self.pipe.poll(timeout=None):
                    data = self.pipe.recv()
                    if not data:
                        break
                    else:
                        self.plot_data(*data)
            except BrokenPipeError:
                pass
        else:
            self.plot_data(self.wavelengths, self.counts)
        plt.show()

    def plot_data(self, wavelengths, counts):
        self.axes.set_xlim(wavelengths[0], wavelengths[-1])
        self.axes.plot(wavelengths, counts)
        plt.pause(0.001)
