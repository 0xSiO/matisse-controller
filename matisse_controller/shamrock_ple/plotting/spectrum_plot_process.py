from multiprocessing import Process

import matplotlib.pyplot as plt


class SpectrumPlotProcess(Process):
    def __init__(self, wavelengths, counts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wavelengths = wavelengths
        self.counts = counts

    def run(self):
        plt.figure('CCD Acquisition')
        plt.cla()
        plt.title('Counts vs. Wavelength')
        plt.xlim(self.wavelengths[0], self.wavelengths[-1])
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Counts')
        plt.plot(self.wavelengths, self.counts)
        plt.show()

    # TODO: This can't run because plt.show() blocks. Use some kind of communication channel instead
    def add_data(self, wavelengths, counts):
        plt.plot(wavelengths, counts)
        plt.draw()
