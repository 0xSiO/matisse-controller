from os import path

from setuptools import setup, find_packages

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as readme:
    long_description = readme.read()

setup(name='matisse-controller',
      version='0.2.0',
      description="A Python package to control the Matisse 2 TS.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://github.com/lucis-fluxum/matisse-controller',
      author='Luc Street',
      license='MIT',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering :: Physics',

      ],
      keywords='ni-visa matisse laser',
      # TODO: Documentation URL
      packages=find_packages(exclude=['docs', 'tests*']),
      install_requires=['pyvisa >=1, <2', 'pyserial >=3, <4', 'scipy >=1, <2', 'matplotlib >=3, <4', 'pyqt5 >=5'],
      # TODO: Test other python versions
      python_requires='~=3.7',
      entry_points={
            'gui_scripts': [
                  'matisse-controller = matisse_controller:main'
            ]
      })
