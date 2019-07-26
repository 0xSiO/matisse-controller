# matisse-controller

A Python package to control the Matisse 2 TS laser for the University of Washington's Optical Spintronics and Sensing Lab.

Requirements: Python 3.7+, NI VISA, PyVISA, pySerial, SciPy, matplotlib, PyQt5

## Installation

    $ pip install matisse-controller

## Usage

To launch the GUI, connect the Matisse and a supported wavemeter, and then run:

    $ matisse-controller

The GUI uses a Python API to control the Matisse. If you only care about using the API, just
`import matisse_controller`. The `matisse` and `wavemeter` subpackages contain the APIs you'll want.

## Development

After checking out the repo, run `pipenv install --dev` to install dependencies. Using a virtual environment is
recommended.

To install this package onto your local machine, run `pip install -e .`.

### Adding features to the Matisse class
The standard way of interacting with the Matisse outside of the existing API is to use the Matisse.query method. The
Matisse implements several commands that run asynchronously, like motor movements, so if you want to run these
synchronously, you must do it on your own (like checking the motor status until it's idle again).

Long-running tasks should be executed in a thread that can be started and gracefully stopped from the Matisse class.
Currently, fetching a measurement from the wavemeter is a relatively expensive process, so avoid doing this too much if
possible.

### Adding another wavemeter
Currently I've implemented an interface for the WaveMaster, but any class will do, as long as it implements the
`get_raw_value` and `get_wavelength` functions. The `get_raw_value` function should return a value representing exactly
what is seen on the wavemeter display (this might not be a measurement), and the `get_wavelength` function should always
return a floating-point number representing the latest measurement from the wavemeter. The WaveMaster implementation
blocks the thread until a value is returned from the instrument. Additionally, please ensure any code you write that
communicates with instruments is thread-safe.

### Adding features to the GUI
Logging and UI updates should have top priority, so take care not to block the UI thread. Here's the process I use:
- Add a menu action under `setup_menus` and connect it to a Qt slot under `setup_slots`, to be executed on the main
thread later.
- Do UI updates in this slot, if you need a long-running task that also updates the UI, use a subclass of QThread with a
slot (see LoggingThread, StatusUpdateThread for examples).
- For long-running tasks that do not need access to the UI, submit a runnable object to the ControlApplication's
instance of ThreadPoolExecutor. Hold a reference to the Future it gives you and call `add_done_callback` on it, passing
in `ControlApplication.raise_error_from_future` if you want to display errors from that thread in a dialog box. For an
example of a method that runs tasks one-by-one on the Matisse, see the `run_matisse_task` method.

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/lucis-fluxum/matisse-controller.

## License

The package is available as open source under the terms of the [MIT License](http://opensource.org/licenses/MIT).
