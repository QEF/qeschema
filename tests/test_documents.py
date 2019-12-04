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
from xmlschema import XMLSchemaValidationError, XMLSchema

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
        schema = os.path.join(self.schemas_dir, 'qes.xsd')

        document = XmlDocument(schema)
        self.assertIsInstance(document, XmlDocument)
        self.assertIsNone(document.root)
        self.assertIsNone(document.filename)
        self.assertIsNone(document.format)
        self.assertTrue(document.schema.url.endswith(schema))
        self.assertIsInstance(document.schema, XMLSchema)

        document = XmlDocument(schema=XMLSchema(schema))
        self.assertTrue(document.schema.url.endswith(schema))
        self.assertIsInstance(document.schema, XMLSchema)

        self.assertIsInstance(PwDocument(), PwDocument)
        self.assertIsInstance(PwDocument(schema=schema), PwDocument)

        schema = os.path.join(self.schemas_dir, 'ph_temp.xsd')
        self.assertIsInstance(PhononDocument(), PhononDocument)
        self.assertIsInstance(PhononDocument(schema=schema), PhononDocument)

        schema = os.path.join(self.schemas_dir, 'qes_neb.xsd')
        self.assertIsInstance(NebDocument(), NebDocument)
        self.assertIsInstance(NebDocument(schema=schema), NebDocument)

        schema = os.path.join(self.schemas_dir, 'tddfpt.xsd')
        self.assertIsInstance(TdDocument(), TdDocument)
        self.assertIsInstance(TdDocument(schema=schema), TdDocument)

        schema = os.path.join(self.schemas_dir, 'qes_spectrum.xsd')
        self.assertIsInstance(TdSpectrumDocument(), TdSpectrumDocument)
        self.assertIsInstance(TdSpectrumDocument(schema=schema), TdSpectrumDocument)

    def test_namespaces_property(self):
        schema = os.path.join(self.schemas_dir, 'qes.xsd')
        document = XmlDocument(schema)
        self.assertEqual(document.namespaces, {
            '': 'http://www.w3.org/2001/XMLSchema',
            'qes': 'http://www.quantum-espresso.org/ns/qes/qes-1.0',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        })

    def test_exception_class(self):
        document = PwDocument()

        with self.assertRaises(XmlDocumentError):
            document.get_fortran_input()

        schema = os.path.join(self.schemas_dir, 'qes.xsd')
        document = TdSpectrumDocument(schema=schema)
        document.read(os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml'))

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
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'json')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance_json')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'json')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance.yaml')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'yaml')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance_yaml')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.filename, filename)
        self.assertEqual(document.format, 'yaml')

        filename = os.path.join(self.test_dir, 'examples/dummy/instance.csv')
        with self.assertRaises(ValueError):
            document.read(filename)

    def test_from_xml_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')

        root, errors = document.from_xml(filename)
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertListEqual(errors, [])

        root, errors = document.from_xml(filename, validation='skip')
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertListEqual(errors, [])

        root = ElementTree.parse(filename).getroot()
        with self.assertRaises(TypeError):
            document.from_xml(root)

        with self.assertRaises(XMLSchemaValidationError):
            document.from_xml("<root><node/><unknown/></root>")

        root, errors = document.from_xml("<root><node/><unknown/></root>", validation='lax')
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertEqual(len(errors), 1)

    def test_from_json_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.json')

        root, errors = document.from_json(filename)
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertListEqual(errors, [])

        with self.assertRaises(TypeError):
            with open(filename) as f:
                document.from_json(f)

        with self.assertRaises(XMLSchemaValidationError):
            document.from_json('{"root": {"node": null, "unknown": null}}')

        root, errors = document.from_json('{"root": {"node": null, "unknown": null}}', validation='lax')
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertGreaterEqual(len(errors), 1)

    def test_from_yaml_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.yaml')

        root, errors = document.from_yaml(filename)
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertListEqual(errors, [])

        with self.assertRaises(TypeError):
            with open(filename) as f:
                document.from_yaml(f)

        with self.assertRaises(XMLSchemaValidationError):
            document.from_yaml('root:\n  node: null\n  unknown: null\n')

        root, errors = document.from_yaml('root:\n  node: null\n  unknown: null\n', validation='lax')
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertGreaterEqual(len(errors), 1)

    def test_from_dict_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))

        root, errors = document.from_dict({'root': {'node': [None, None, None]}})
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertListEqual(errors, [])

        with self.assertRaises(XMLSchemaValidationError):
            document.from_dict({'root': {'node': None, 'unknown': None}})

        root, errors = document.from_dict({'root': {'node': None, 'unknown': None}}, validation='lax')
        self.assertTrue(hasattr(root, 'tag'))
        self.assertEqual(root.tag, 'root')
        self.assertGreaterEqual(len(errors), 1)

    def test_write_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')

        with self.assertRaises(RuntimeError):
            document.write(filename)
        document.read(filename)

        filename = os.path.join(self.test_dir, 'examples/dummy/write_test_file')
        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        document.write(filename)
        self.assertIsInstance(ElementTree.parse(filename), ElementTree.ElementTree)

        document.write(filename, output_format='json')
        with open(filename) as f:
            self.assertEqual(f.read().replace(' ', '').replace('\n', ''),
                             '{"root":{"node":[null,null,null]}}')

        document.write(filename, output_format='yaml')
        with open(filename) as f:
            self.assertEqual(f.read(), 'root:\n  node:\n  - null\n  - null\n  - null\n')

        with self.assertRaises(TypeError):
            with open(filename, mode='w+') as f:
                document.write(f)

        with self.assertRaises(ValueError):
            document.write(filename, output_format='csv')

        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

    def test_to_dict_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_dict(), {'root': {'node': [None, None, None]}})
        self.assertEqual(document.to_dict(preserve_root=False), {'node': [None, None, None]})

    def test_to_json_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_json().replace(' ', '').replace('\n', ''),
                         '{"root":{"node":[null,null,null]}}')

        filename = os.path.join(self.test_dir, 'examples/dummy/write_test_file')
        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        document.to_json(filename=filename)
        with open(filename) as f:
            self.assertEqual(f.read().replace(' ', '').replace('\n', ''),
                             '{"root":{"node":[null,null,null]}}')

    def test_to_yaml_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_yaml(), 'root:\n  node:\n  - null\n  - null\n  - null\n')

        filename = os.path.join(self.test_dir, 'examples/dummy/write_test_file')
        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        document.to_yaml(filename=filename)
        with open(filename) as f:
            self.assertEqual(f.read(), 'root:\n  node:\n  - null\n  - null\n  - null\n')

    def test_iter_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        root = document.root
        self.assertEqual(list(document.iter()), [root, root[0], root[1], root[2]])

    def test_find_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.find('.'), document.root)
        self.assertEqual(document.find('/node'), document.root[0])

    def test_findall_method(self):
        document = XmlDocument(os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.findall('.'), [document.root])
        self.assertEqual(document.findall('/node'), document.root[:])

    def test_unsupported_schema(self):
        with self.assertRaises(NotImplementedError):
            PwDocument(schema=os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))

    def test_pw_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml')
        document = PwDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, '{http://www.quantum-espresso.org/ns/qes/qes-1.0}espresso')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_phonon_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/ph/al.elph.xml')
        document = PhononDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, '{http://www.quantum-espresso.org/ns/qes/qes_ph_1.0}espressoph')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'inputPH')
        self.assertEqual(document.output_path, 'outputPH')

    def test_neb_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/neb/Al001+H_bc3.xml')
        document = NebDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, '{http://www.quantum-espresso.org/ns/neb}nebRun')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_td_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/tddfpt/Ag.tddfpt-eels.xml')
        document = TdDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, '{http://www.quantum-espresso.org/ns/qes/qes_lr-1.0}tddfpt')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_td_spectrum_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/tddfpt/CH4.tddfpt_pp.xml')
        document = TdSpectrumDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, '{http://www.quantum-espresso.org/ns/qes/qes_spectrum-1.0}spectrumDoc')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'spectrumIn')
        self.assertEqual(document.output_path, 'output')

    def test_fortran_input_generator(self):
        xml_filename = os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml')
        document = PwDocument()
        document.read(xml_filename)

        filename = os.path.join(self.test_dir, 'examples/dummy/write_test_file')
        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        document.write_fortran_input(filename)
        with open(filename) as f:
            fortran_input = f.read()

        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        self.assertEqual(fortran_input[:9], '&CONTROL\n')
        self.assertEqual(fortran_input, document.get_fortran_input())


if __name__ == '__main__':
    unittest.main()
