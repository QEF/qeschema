# -*- coding: utf-8 -*-
#
# Copyright (c), 2015-2016, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# Authors: Davide Brunato
#
"""Python 2/3 compatibility imports and definitions."""
import sys

PY3 = sys.version_info >= (3,)

if PY3:
    unicode_type = str
else:
    unicode_type = unicode
