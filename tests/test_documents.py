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

from qeschema import QeDocument, PwDocument, PhononDocument, NebDocument, \
    TdDocument, TdSpectrumDocument, XmlDocumentError
from qeschema.documents import XmlDocument


class TestDocuments(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.pkg_folder = os.path.dirname(cls.test_dir)
        cls.schemas_dir = os.path.join(cls.pkg_folder, 'qeschema/schemas')

    def test_document_init(self):
        schema = os.path.join(self.schemas_dir, 'qes.xsd')

        with self.assertRaises(XmlDocumentError) as context:
            XmlDocument(schema)
        self.assertEqual(str(context.exception), "source is an XSD schema")

        document = XmlDocument(schema=schema)
        self.assertIsInstance(document, XmlDocument)
        self.assertIsNone(document.root)
        self.assertIsNone(document.filename)
        self.assertIsNone(document.format)
        self.assertTrue(document.schema.url.endswith(schema))
        self.assertIsInstance(document.schema, XMLSchema)

        document = XmlDocument(schema=XMLSchema(schema))
        self.assertTrue(document.schema.url.endswith(schema))
        self.assertIsInstance(document.schema, XMLSchema)

    def test_pw_document_init(self):
        document = PwDocument()
        self.assertIsInstance(PwDocument(), PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/qeschema/schemas/qes.xsd"))

        schema = os.path.join(self.schemas_dir, 'qes.xsd')
        document = PwDocument(schema=schema)
        self.assertIsInstance(document, PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/qeschema/schemas/qes.xsd"))

        document = PwDocument(schema='qes.xsd')
        self.assertIsInstance(document, PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/qeschema/schemas/qes.xsd"))

        document = PwDocument(schema='qes-20180511.xsd')
        self.assertIsInstance(document, PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/releases/qes-20180511.xsd"))

        source = os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml')
        document = PwDocument(source)
        self.assertEqual(document.filename, source)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/releases/qes_190719.xsd"))

        document = PwDocument(source, schema='qes.xsd')
        self.assertEqual(document.filename, source)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

        source = os.path.join(self.test_dir, 'examples/pw/Al001_rlx_damp.xml')
        document = PwDocument(source)
        self.assertEqual(document.filename, source)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

        source = os.path.join(self.test_dir, 'examples/pw/CO_bgfs_relax.xml')
        document = PwDocument(source)
        self.assertEqual(document.filename, source)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

    def test_phonon_document_init(self):
        schema = os.path.join(self.schemas_dir, 'ph_temp.xsd')
        self.assertIsInstance(PhononDocument(), PhononDocument)
        self.assertTrue(PhononDocument().schema.url.endswith("qeschema/schemas/ph_temp.xsd"))
        self.assertIsInstance(PhononDocument(schema=schema), PhononDocument)

    def test_neb_document_init(self):
        schema = os.path.join(self.schemas_dir, 'qes_neb.xsd')
        self.assertIsInstance(NebDocument(), NebDocument)
        self.assertTrue(NebDocument().schema.url.endswith("qeschema/schemas/qes_neb.xsd"))
        self.assertIsInstance(NebDocument(schema=schema), NebDocument)

    def test_td_document_init(self):
        schema = os.path.join(self.schemas_dir, 'tddfpt.xsd')
        self.assertIsInstance(TdDocument(), TdDocument)
        self.assertTrue(TdDocument().schema.url.endswith("qeschema/qeschema/schemas/tddfpt.xsd"))
        self.assertIsInstance(TdDocument(schema=schema), TdDocument)

    def test_td_spectrum_document_init(self):
        schema = os.path.join(self.schemas_dir, 'qes_spectrum.xsd')
        self.assertIsInstance(TdSpectrumDocument(), TdSpectrumDocument)
        self.assertTrue(TdSpectrumDocument().schema.url.endswith("schemas/qes_spectrum.xsd"))
        self.assertIsInstance(TdSpectrumDocument(schema=schema), TdSpectrumDocument)

    def test_fetch_schema(self):
        self.assertIsNone(XmlDocument.fetch_schema('missing.xsd'))
        self.assertIsNone(XmlDocument.fetch_schema('qes.xsd'))
        self.assertIsNone(QeDocument.fetch_schema('missing.xsd'))

        filename = QeDocument.fetch_schema('qes.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('unknown-path/qes.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('/unknown-path/qes.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('file:///unknown-path/qes.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('releases/qes.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('qes_190304.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/releases/qes_190304.xsd"))

        filename = QeDocument.fetch_schema('unknown/qes_190304.xsd')
        self.assertTrue(filename.endswith("qeschema/schemas/releases/qes_190304.xsd"))

    def test_schema_namespaces(self):
        schema = os.path.join(self.schemas_dir, 'qes.xsd')
        document = XmlDocument(schema=schema)
        self.assertEqual(document.schema.namespaces, {
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
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
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
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')

        document.from_xml(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertListEqual(document.errors, [])

        document.from_xml(filename, validation='skip')
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertListEqual(document.errors, [])

        root = ElementTree.parse(filename).getroot()
        document.from_xml(root)
        self.assertIs(root, document.root)

        with self.assertRaises(XMLSchemaValidationError):
            document.from_xml("<root><node/><unknown/></root>")

        document.from_xml("<root><node/><unknown/></root>", validation='lax')
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(len(document.errors), 1)

    def test_from_json_method(self):
        document = XmlDocument(schema=os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.json')

        document.from_json(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertListEqual(document.errors, [])

        with self.assertRaises(TypeError):
            with open(filename) as f:
                document.from_json(f)

        with self.assertRaises(XMLSchemaValidationError):
            document.from_json('{"root": {"node": null, "unknown": null}}')

        document.from_json('{"root": {"node": null, "unknown": null}}', validation='lax')
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertGreaterEqual(len(document.errors), 1)

    def test_from_yaml_method(self):
        document = XmlDocument(schema=os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.yaml')

        document.from_yaml(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertListEqual(document.errors, [])

        with self.assertRaises(TypeError):
            with open(filename) as f:
                document.from_yaml(f)

        with self.assertRaises(XMLSchemaValidationError):
            document.from_yaml('root:\n  node: null\n  unknown: null\n')

        document.from_yaml('root:\n  node: null\n  unknown: null\n', validation='lax')
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertGreaterEqual(len(document.errors), 1)

    def test_from_dict_method(self):
        document = XmlDocument(schema=os.path.join(self.test_dir, 'examples/dummy/schema.xsd'))

        document.from_dict({'root': {'node': [None, None, None]}})
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertListEqual(document.errors, [])

        with self.assertRaises(XMLSchemaValidationError):
            document.from_dict({'root': {'node': None, 'unknown': None}})

        document.from_dict({'root': {'node': None, 'unknown': None}}, validation='lax')
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertGreaterEqual(len(document.errors), 1)

    def test_write_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
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
                             '{"root":{"node":[null,{"$":"value"},null]}}')

        document.write(filename, output_format='yaml')
        with open(filename) as f:
            self.assertEqual(f.read(), 'root:\n  node:\n  - null\n  - $: value\n  - null\n')

        with self.assertRaises(TypeError):
            with open(filename, mode='w+') as f:
                document.write(f)

        with self.assertRaises(ValueError):
            document.write(filename, output_format='csv')

        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

    def test_to_dict_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_dict(keep_unknown=True),
                         {'root': {'node': [None, {'$': 'value'}, None]}})
        self.assertEqual(document.to_dict(preserve_root=False),
                         {'node': [None, {'$': 'value'}, None]})

    def test_to_json_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_json().replace(' ', '').replace('\n', ''),
                         '{"root":{"node":[null,{"$":"value"},null]}}')

        filename = os.path.join(self.test_dir, 'examples/dummy/write_test_file')
        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        document.to_json(filename=filename)
        with open(filename) as f:
            self.assertEqual(f.read().replace(' ', '').replace('\n', ''),
                             '{"root":{"node":[null,{"$":"value"},null]}}')

    def test_to_yaml_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_yaml(), 'root:\n  node:\n  - null\n  - $: value\n  - null\n')

        filename = os.path.join(self.test_dir, 'examples/dummy/write_test_file')
        if os.path.isfile(filename):
            os.unlink(filename)
        self.assertFalse(os.path.isfile(filename))

        document.to_yaml(filename=filename)
        with open(filename) as f:
            self.assertEqual(f.read(), 'root:\n  node:\n  - null\n  - $: value\n  - null\n')

    def test_iter_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        root = document.root
        self.assertEqual(list(document.iter()), [root, root[0], root[1], root[2]])

    def test_find_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'examples/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.find('.'), document.root)
        self.assertEqual(document.find('/node'), document.root[0])

    def test_findall_method(self):
        schema = os.path.join(self.test_dir, 'examples/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
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
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes-1.0}espresso')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_phonon_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/ph/al.elph.xml')
        document = PhononDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes_ph_1.0}espressoph')
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
        document = TdDocument(source=xml_filename)

        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes_lr-1.0}tddfpt')
        self.assertEqual(document.filename, xml_filename)
        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_td_spectrum_document(self):
        xml_filename = os.path.join(self.test_dir, 'examples/tddfpt/CH4.tddfpt_pp.xml')
        document = TdSpectrumDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes_spectrum-1.0}spectrumDoc')
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
