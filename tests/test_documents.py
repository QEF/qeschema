#!/usr/bin/env python3
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato
#
import os
import unittest
import xml.etree.ElementTree as ElementTree
from xmlschema import XMLSchemaConverter

from qeschema import PwDocument, PhononDocument, NebDocument, TdDocument, \
    TdSpectrumDocument, XmlDocumentError
from qeschema.documents import XmlDocument

class TestDocuments(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.pkg_folder = os.path.dirname(cls.test_dir)
        cls.schemas_dir = os.path.join(cls.pkg_folder, 'qeschema/schemas')

    def test_document_init(self):
        xsd_file = os.path.join(self.schemas_dir, 'qes.xsd')

        self.assertIsInstance(XmlDocument(xsd_file), XmlDocument)
        self.assertIsInstance(XmlDocument(xsd_file, converter=XMLSchemaConverter), XmlDocument)

        self.assertIsInstance(PwDocument(), PwDocument)
        self.assertIsInstance(PwDocument(xsd_file=xsd_file), PwDocument)

        xsd_file = os.path.join(self.schemas_dir, 'ph_temp.xsd')
        self.assertIsInstance(PhononDocument(), PhononDocument)
        self.assertIsInstance(PhononDocument(xsd_file=xsd_file), PhononDocument)

        xsd_file = os.path.join(self.schemas_dir, 'qes_neb.xsd')
        self.assertIsInstance(NebDocument(), NebDocument)
        self.assertIsInstance(NebDocument(xsd_file=xsd_file), NebDocument)

        xsd_file = os.path.join(self.schemas_dir, 'tddfpt.xsd')
        self.assertIsInstance(TdDocument(), TdDocument)
        self.assertIsInstance(TdDocument(xsd_file=xsd_file), TdDocument)

        xsd_file = os.path.join(self.schemas_dir, 'qes_spectrum.xsd')
        self.assertIsInstance(TdSpectrumDocument(), TdSpectrumDocument)
        self.assertIsInstance(TdSpectrumDocument(xsd_file=xsd_file), TdSpectrumDocument)

        xml_filename = os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml')

if __name__ == '__main__':
    unittest.main()
