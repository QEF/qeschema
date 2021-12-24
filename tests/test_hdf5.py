#!/usr/bin/env python
#
# Copyright (c), 2021, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato
#
import unittest
import numpy as np
from pathlib import Path

from qeschema.hdf5 import read_charge_file, get_wavefunctions, \
    get_wf_attributes, get_wfc_miller_indices


# TODO: Fetch appropriate HDF5 files for testing

@unittest.SkipTest
class TestHdf5Utils(unittest.TestCase):

    def test_read_charge_file(self):
        hdf5_file = Path(__file__).parent.joinpath('resources/hdf5/???')

    def test_get_wf_attributes(self):
        hdf5_file = Path(__file__).parent.joinpath('resources/hdf5/???')

    def test_get_wavefunctions(self):
        hdf5_file = Path(__file__).parent.joinpath('resources/hdf5/???')

    def test_get_wfc_miller_indices(self):
        hdf5_file = Path(__file__).parent.joinpath('resources/hdf5/???')


if __name__ == '__main__':
    unittest.main()
