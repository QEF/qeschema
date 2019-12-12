#!/usr/bin/env python3
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato
#
import unittest
import tempfile
import logging
import sys
from types import MethodType
from xml.etree import ElementTree

from qeschema.utils import set_logger, etree_iter_path, to_fortran, BiunivocalMap


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

    def test_etree_iterpath(self):
        root = ElementTree.XML('<A><B1><C1/></B1><B2><C2/><C3/></B2></A>')

        values = iter(etree_iter_path(root))
        self.assertEqual(next(values), (root, '.'))
        self.assertEqual(next(values), (root[0], './B1'))
        self.assertEqual(next(values), (root[0][0], './B1/C1'))
        self.assertEqual(next(values), (root[1], './B2'))
        self.assertEqual(next(values), (root[1][0], './B2/C2'))
        self.assertEqual(next(values), (root[1][1], './B2/C3'))
        self.assertRaises(StopIteration, next, values)

        values = iter(etree_iter_path(root, tag='C2'))
        self.assertEqual(next(values), (root[1][0], './B2/C2'))
        self.assertRaises(StopIteration, next, values)

        values = iter(etree_iter_path(root, tag="*"))
        self.assertEqual(next(values), (root, '.'))
        self.assertEqual(next(values), (root[0], './B1'))
        self.assertEqual(next(values), (root[0][0], './B1/C1'))
        self.assertEqual(next(values), (root[1], './B2'))
        self.assertEqual(next(values), (root[1][0], './B2/C2'))
        self.assertEqual(next(values), (root[1][1], './B2/C3'))
        self.assertRaises(StopIteration, next, values)

        values = iter(etree_iter_path(root, path='/A'))
        self.assertEqual(next(values), (root, '/A'))
        self.assertEqual(next(values), (root[0], '/A/B1'))
        self.assertEqual(next(values), (root[0][0], '/A/B1/C1'))
        self.assertEqual(next(values), (root[1], '/A/B2'))
        self.assertEqual(next(values), (root[1][0], '/A/B2/C2'))
        self.assertEqual(next(values), (root[1][1], '/A/B2/C3'))
        self.assertRaises(StopIteration, next, values)

    def test_to_fortran(self):
        self.assertEqual(to_fortran(True), '.true.')
        self.assertEqual(to_fortran(False), '.false.')
        self.assertEqual(to_fortran(' a string '), repr('a string'))
        self.assertEqual(to_fortran(b' a byte string '), repr('a byte string'))
        self.assertEqual(to_fortran(10), '10')
        self.assertEqual(to_fortran(999.1), '999.1')


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

    def test_getitem(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(bimap['a'], 1)
        self.assertEqual(bimap['b'], 2)
        self.assertEqual(bimap['c'], 3)
        with self.assertRaises(KeyError):
            _ = bimap['d']

        bimap.__missing__ = MethodType(lambda x, y: 0, bimap)
        self.assertEqual(bimap['d'], 0)

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

        if sys.version_info >= (3, 6):
            self.assertListEqual(list(x for x in bimap), ['a', 'b', 'c', 'd'])
        else:
            self.assertEqual(set(x for x in bimap), {'a', 'd', 'b', 'c'})

    def test_len(self):
        self.assertEqual(len(BiunivocalMap()), 0)
        self.assertEqual(len(BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})), 4)

    def test_contains(self):
        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        self.assertTrue('a' in bimap)
        self.assertTrue('c' in bimap)
        self.assertTrue('d' in bimap)
        self.assertFalse('e' in bimap)
        self.assertFalse(4 in bimap)

    def test_repr(self):
        bimap = BiunivocalMap()
        self.assertEqual(repr(bimap), "BiunivocalMap()")

        bimap = BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        if sys.version_info >= (3, 6):
            self.assertEqual(repr(bimap), "BiunivocalMap({'a': 1, 'b': 2, 'c': 3, 'd': 4})")
        else:
            s = repr(bimap)
            self.assertTrue(s.startswith("BiunivocalMap({"))
            self.assertTrue(s.endswith('})'))
            self.assertListEqual(sorted(s[15:-2].split(', ')),
                                 ["'a': 1", "'b': 2", "'c': 3", "'d': 4"])

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
