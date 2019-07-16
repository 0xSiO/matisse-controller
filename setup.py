from setuptools import setup, find_packages

setup(name='matisse_controller',
      version='0.1',
      url='http://github.com/lucis-fluxum/matisse_controller',
      author='Luc Street',
      license='MIT',
      packages=find_packages(),
      install_requires=['pyvisa', 'pyserial', 'scipy', 'matplotlib', 'pyqt5'])
