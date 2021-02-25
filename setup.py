#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev
# TODO Only for local and CI usage. The installer does not use this package.

import io
import os
import sys
from shutil import rmtree
from os.path import splitext
from glob import glob
from os.path import basename

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'piweather'
DESCRIPTION = 'Weather Air Quality Device - base package'
URL = 'https://github.com/goszpeti/piWeather'
EMAIL = 'peter.gosztolya@gmail.com'
AUTHOR = 'Peter Gosztolya'
REQUIRES_PYTHON = '>=3.6.0'

# What packages are required for this module to be executed?
REQUIRED = [
    "PyQt5==5.12.3",
    "PyQtChart==5.12.0",
    "gTTS>=2.2.1",
    "python-vlc>=3.0.11115",
    "PyGithub>=1.45",
    "packaging>=20.8",
    "multiprocessing-logging>=0.3.1",
    "getrpimodel>=0.1.17",
    "jsonschema>=3.2.0",
    "APScheduler>=3.6.3",
    "python-dateutil>=2.8.1",
    "debugpy >= 1.2.1"
]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
with open(os.path.join(here, "src", project_slug, '__init__.py')) as f:
    exec(f.read(), about)


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages("src"),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],

    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',  # TODO
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    entry_points={
        'gui_scripts': [
            'piweather=main:main',
        ]
    }
)
