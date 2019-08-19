import time
from multiprocessing import Pipe

from matisse_controller.shamrock_ple.plotting import *

if __name__ == '__main__':
    pipe_in, pipe_out = Pipe()
    p = SpectrumPlotProcess(pipe=pipe_out)
    p.start()
    p2 = SpectrumPlotProcess([1, 2, 3], [10, 9, 8])
    p2.start()
    print('started plot')
    time.sleep(1)
    pipe_in.send(((1, 2, 3), [4, 5, 6]))
    time.sleep(1)
    pipe_in.send(([1, 2, 3], (6, 5, 4)))
    time.sleep(1)
    pipe_in.send(([1, 2, 3], [7, 6, 5]))
    print('done')
    pipe_in.send(None)
