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
from xmlschema import XMLSchema, XMLSchemaConverter, ParkerConverter

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

        document = XmlDocument(xsd_file)
        self.assertIsInstance(document, XmlDocument)
        self.assertIsNone(document.root)
        self.assertIsNone(document.filename)
        self.assertIsNone(document.format)
        self.assertEqual(document.xsd_file, xsd_file)
        self.assertIsInstance(document.schema, XMLSchema)

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

    def test_converted_property(self):
        xsd_file = os.path.join(self.schemas_dir, 'qes.xsd')
        document = XmlDocument(xsd_file, ParkerConverter)
        self.assertIsInstance(document.converter, ParkerConverter)

    def test_namespaces_property(self):
        xsd_file = os.path.join(self.schemas_dir, 'qes.xsd')
        document = XmlDocument(xsd_file)
        self.assertEqual(document.namespaces, {
            '': 'http://www.w3.org/2001/XMLSchema',
            'qes': 'http://www.quantum-espresso.org/ns/qes/qes-1.0',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        })

    def test_exception_class(self):
        document = PwDocument()

        with self.assertRaises(XmlDocumentError):
            document.get_fortran_input()

    def test_read_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')

        with open(filename) as f:
            with self.assertRaises(TypeError):
                document.read(f)

        with self.assertRaises(ValueError):
            document.read(os.path.join(self.test_dir, 'examples/unknown.xml'))

        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'xml')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance_xml')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'xml')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance.json')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'json')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance_json')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'json')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance.yaml')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'yaml')

    def test_pw_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml')
        document = PwDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')





if __name__ == '__main__':
    unittest.main()
