#!/usr/bin/env python
#
# Copyright (c), 2015-2016, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# @author Davide Brunato
#
from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name='qeschema',
    version='0.5.0',
    install_requires=['xmlschema==0.9.30'],
    packages=['qeschema'],
    package_data={'qeschema': ['schemas/*.xsd']},
    scripts = ['scripts/xml2qeinput.py'],
    url='https://github.com/QEF/qeschema',
    license='MIT',
    description='Quantum Espresso tools for XML Schema based documents.',
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Utilities',
    ]
)
