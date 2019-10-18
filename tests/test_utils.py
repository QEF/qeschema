#!/usr/bin/env python3
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato, Giovanni Borghi
#
import unittest
import tempfile
import logging
from io import StringIO

from qeschema.utils import set_logger, BiunivocalMap


class TestHelperFunctions(unittest.TestCase):

    def test_set_logger(self):
        logger = logging.getLogger('qeschema')
        loglevel = logger.getEffectiveLevel()
        handlers = logger.handlers

        set_logger(4)
        self.assertEqual(logger.getEffectiveLevel(), logging.DEBUG)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        self.assertNotIsInstance(logger.handlers[0], logging.FileHandler)
        logger.handlers = []

        set_logger(3)
        self.assertEqual(logger.getEffectiveLevel(), logging.INFO)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        self.assertNotIsInstance(logger.handlers[0], logging.FileHandler)
        logger.handlers = []

        set_logger(2)
        self.assertEqual(logger.getEffectiveLevel(), logging.WARNING)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        self.assertNotIsInstance(logger.handlers[0], logging.FileHandler)
        self.assertEqual(len(logger.handlers), 1)
        logger.handlers = []

        f = tempfile.mkstemp()
        set_logger(1, logfile=f[1])
        self.assertEqual(logger.getEffectiveLevel(), logging.ERROR)
        self.assertIsInstance(logger.handlers[0], logging.FileHandler)
        logger.handlers[0].close()
        
        logger.setLevel(loglevel)
        logger.handlers = handlers


class TestBiunivocalMap(unittest.TestCase):

    def test_initialization(self):
        bimap = BiunivocalMap()
        self.assertFalse(bimap)
        self.assertFalse(getattr(bimap, '_BiunivocalMap__map'))
        self.assertFalse(getattr(bimap, '_BiunivocalMap__inverse'))

        bimap = BiunivocalMap([('a', 1), ('b', 2)])
        self.assertTrue(bimap)
        self.assertEqual(bimap, {'a': 1, 'b': 2})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__map'), {'a': 1, 'b': 2})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__inverse'), {1: 'a', 2: 'b'})

        bimap = BiunivocalMap({'a': 1, 'b': 2})
        self.assertTrue(bimap)
        self.assertEqual(bimap, {'a': 1, 'b': 2})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__map'), {'a': 1, 'b': 2})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__inverse'), {1: 'a', 2: 'b'})

    def test_setitem(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2})
        bimap['c'] = 3
        bimap['d'] = 4

        result = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        self.assertEqual(bimap, result)
        self.assertEqual(getattr(bimap, '_BiunivocalMap__map'), result)
        self.assertEqual(getattr(bimap, '_BiunivocalMap__inverse'),
                         {1: 'a', 2: 'b', 3: 'c', 4: 'd'})

    def test_delitem(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})

        del bimap['c']
        bimap.pop('d')
        self.assertEqual(bimap, {'a': 1, 'b': 2})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__map'), {'a': 1, 'b': 2})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__inverse'), {1: 'a', 2: 'b'})

    def test_duplicates(self):
        with self.assertRaises(ValueError):
            BiunivocalMap([('a', 1), ('b', 1)])

        bimap = BiunivocalMap({'a': 1, 'b': 2})
        with self.assertRaises(ValueError):
            bimap['c'] = 1

        bimap['a'] = 1
        with self.assertRaises(ValueError):
            bimap['a'] = 2

        bimap['b'] = 2.0
        with self.assertRaises(ValueError):
            bimap['a'] = 2

        bimap['b'] = 2.1
        bimap['a'] = 2

    def test_iter(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        self.assertListEqual(list(x for x in bimap), ['a', 'b', 'c', 'd'])

    def test_len(self):
        self.assertEqual(len(BiunivocalMap()), 0)
        self.assertEqual(len(BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})), 4)

    def test_repr(self):
        bimap = BiunivocalMap()
        self.assertEqual(repr(bimap), "BiunivocalMap()")

        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        self.assertEqual(repr(bimap), "BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})")

    def test_copy(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3})
        bimap2 = bimap.copy()
        self.assertEqual(bimap, bimap2)

        self.assertEqual(bimap, {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__map'), {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(getattr(bimap, '_BiunivocalMap__inverse'), {1: 'a', 2: 'b', 3: 'c'})

    def test_inverse(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(bimap.inverse(), {1: 'a', 2: 'b', 3: 'c'})

    def test_getkey(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(bimap.getkey(1), 'a')
        self.assertEqual(bimap.getkey(2), 'b')
        self.assertEqual(bimap.getkey(3), 'c')

        self.assertIsNone(bimap.getkey(4))
        self.assertEqual(bimap.getkey(4, 'unknown'), 'unknown')


if __name__ == '__main__':
    unittest.main()
