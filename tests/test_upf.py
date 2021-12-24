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

from qeschema.upf import read_pseudo_file


class TestUpfUtils(unittest.TestCase):

    def test_read_pseudo_file(self):
        upf_file = Path(__file__).parent.joinpath('resources/upf/N.pz-vbc.UPF')

        obj = read_pseudo_file(str(upf_file))
        self.assertIsInstance(obj, dict)
        self.assertListEqual(list(obj), ['PP_INFO', 'PP_HEADER', 'PP_MESH',
                                         'PP_LOCAL', 'PP_RHOATOM', 'PP_NONLOCAL'])

        self.assertIsInstance(obj['PP_INFO'], dict)
        self.assertIsInstance(obj['PP_HEADER'], dict)
        self.assertIsInstance(obj['PP_MESH'], dict)
        self.assertIsInstance(obj['PP_MESH']['PP_R'], np.ndarray)
        self.assertIsInstance(obj['PP_LOCAL'], np.ndarray)
        self.assertIsInstance(obj['PP_RHOATOM'], np.ndarray)
        self.assertIsInstance(obj['PP_NONLOCAL'], dict)


if __name__ == '__main__':
    unittest.main()
