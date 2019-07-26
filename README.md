# matisse-controller

A Python package to control the Matisse 2 TS laser for the University of Washington's Optical Spintronics and Sensing Lab.

Requirements: Python 3.7+, NI VISA, PyVISA, pySerial, SciPy, matplotlib, PyQt5

## Installation

    $ pip install matisse-controller

## Usage

To launch the GUI, connect the Matisse and a supported wavemeter, and then run:

    $ matisse-controller

The GUI uses a Python API to control the Matisse. If you only care about using the API, just `import matisse_controller`.
The `matisse` and `wavemeter` subpackages contain the APIs you'll want.

## Development

After checking out the repo, run `pipenv install --dev` to install dependencies. Using a virtual environment is recommended.

To install this package onto your local machine, run `pip install -e .`.

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/lucis-fluxum/matisse-controller.

## License

The package is available as open source under the terms of the [MIT License](http://opensource.org/licenses/MIT).
