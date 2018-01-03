from setuptools import setup
from setuptools.extension import Extension

import numpy

extensions = [
    Extension('solver_cython', ['solver_cython.c'], include_dirs=[numpy.get_include()])
]

setup(ext_modules=extensions)
