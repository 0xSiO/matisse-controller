from multiprocessing import Process

import matplotlib.pyplot as plt


class SingleAcquisitionPlotProcess(Process):
    def __init__(self, wavelengths, counts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wavelengths = wavelengths
        self.counts = counts
        self.figure = plt.figure('CCD Acquisition')
        self.axes = self.figure.subplots()

    def run(self):
        self.axes.set_title('Counts vs. Wavelength')
        self.axes.set_xlim(self.wavelengths[0], self.wavelengths[-1])
        self.axes.set_xlabel('Wavelength (nm)')
        self.axes.set_ylabel('Counts')
        self.axes.plot(self.wavelengths, self.counts)
        self.figure.show()

    def add_data(self, wavelengths, counts):
        self.axes.plot(wavelengths, counts)
