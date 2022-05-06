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
import platform
import xml.etree.ElementTree as ElementTree
from xmlschema import XMLSchemaValidationError, XMLSchema, XMLResource

try:
    import yaml
except ImportError:
    yaml = None

from qeschema import QeDocument, PwDocument, PhononDocument, NebDocument, \
    TdDocument, TdSpectrumDocument, XmlDocumentError, PwInputConverter
from qeschema.documents import XmlDocument


class TestDocuments(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.pkg_folder = os.path.dirname(cls.test_dir)
        cls.schemas_dir = os.path.join(cls.pkg_folder, 'qeschema/schemas')
        cls.output_file = os.path.join(cls.test_dir, 'resources/dummy/write_test_file')

    def setUp(self):
        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        self.assertFalse(os.path.isfile(self.output_file))

    def tearDown(self):
        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        self.assertFalse(os.path.isfile(self.output_file))

    def test_document_init(self):
        with self.assertRaises(XmlDocumentError) as context:
            XmlDocument()
        self.assertEqual(str(context.exception), "missing schema for XML data!")

        schema = os.path.join(self.schemas_dir, 'qes.xsd')

        with self.assertRaises(XmlDocumentError) as context:
            XmlDocument(schema)
        self.assertEqual(str(context.exception), "source is an XSD schema")

        document = XmlDocument(schema=schema)
        self.assertIsInstance(document, XmlDocument)
        self.assertIsNone(document.root)
        self.assertIsNone(document.filename)
        self.assertIsNone(document.format)
        self.assertIsInstance(document.schema, XMLSchema)
        if platform.system() == 'Linux':
            self.assertTrue(document.schema.url.endswith(schema))
        else:
            self.assertTrue(document.schema.url.endswith('qeschema/schemas/qes.xsd'))

        document = XmlDocument(schema=XMLSchema(schema))
        self.assertIsInstance(document.schema, XMLSchema)
        if platform.system() == 'Linux':
            self.assertTrue(document.schema.url.endswith(schema))
        else:
            self.assertTrue(document.schema.url.endswith('qeschema/schemas/qes.xsd'))

    def test_qe_document_init(self):
        with self.assertRaises(XmlDocumentError) as context:
            QeDocument()
        self.assertEqual(str(context.exception), "missing schema for XML data!")

        schema = os.path.join(self.schemas_dir, 'qes.xsd')
        document = QeDocument(schema=schema)
        self.assertIsNone(document.input_builder)

        with self.assertRaises(XmlDocumentError) as context:
            QeDocument(schema=schema, input_builder='wrong')
        self.assertEqual(
            str(context.exception),
            "3rd argument must be a <class 'qeschema.converters.RawInputConverter'> subclass"
        )

        document = QeDocument(schema=schema, input_builder=PwInputConverter)
        self.assertIs(document.input_builder, PwInputConverter)

    def test_pw_document_init(self):
        document = PwDocument()
        self.assertIsInstance(PwDocument(), PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

        source = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        document = PwDocument(source)
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, source)
        else:
            self.assertTrue(document.filename.endswith('Al001_relax_bfgs.xml'))
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/releases/qes_190719.xsd"))

        document = PwDocument(source, schema='qes.xsd')
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, source)
        else:
            self.assertTrue(document.filename.endswith('Al001_relax_bfgs.xml'))
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

        source = os.path.join(self.test_dir, 'resources/pw/Al001_rlx_damp.xml')
        document = PwDocument(source)
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, source)
        else:
            self.assertTrue(document.filename.endswith('Al001_rlx_damp.xml'))
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

    def test_phonon_document_init(self):
        schema = os.path.join(self.schemas_dir, 'ph_temp.xsd')
        self.assertIsInstance(PhononDocument(), PhononDocument)
        self.assertTrue(PhononDocument().schema.url.endswith("qeschema/schemas/ph_xmlschema.xsd"))
        self.assertIsInstance(PhononDocument(schema=schema), PhononDocument)

    def test_neb_document_init(self):
        schema = os.path.join(self.schemas_dir, 'qes_neb.xsd')
        self.assertIsInstance(NebDocument(), NebDocument)
        self.assertTrue(NebDocument().schema.url.endswith("qeschema/schemas/qes_neb.xsd"))
        self.assertIsInstance(NebDocument(schema=schema), NebDocument)

    def test_td_document_init(self):
        schema = os.path.join(self.schemas_dir, 'tddfpt.xsd')
        self.assertIsInstance(TdDocument(), TdDocument)
        self.assertTrue(TdDocument().schema.url.endswith("qeschema/schemas/tddfpt.xsd"))
        self.assertIsInstance(TdDocument(schema=schema), TdDocument)

    def test_td_spectrum_document_init(self):
        schema = os.path.join(self.schemas_dir, 'qes_spectrum.xsd')
        self.assertIsInstance(TdSpectrumDocument(), TdSpectrumDocument)
        self.assertTrue(TdSpectrumDocument().schema.url.endswith("schemas/qes_spectrum.xsd"))
        self.assertIsInstance(TdSpectrumDocument(schema=schema), TdSpectrumDocument)

    def test_init_from_xml_resource(self):
        xml_file = os.path.join(self.test_dir, 'resources/pw/CO_bgfs_relax.xml')
        document = PwDocument(source=XMLResource(xml_file))
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, xml_file)
        else:
            self.assertTrue(document.filename.endswith('CO_bgfs_relax.xml'))
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

    def test_init_with_schema_only(self):
        schema = os.path.join(self.schemas_dir, 'qes.xsd')
        document = PwDocument(schema=schema)
        self.assertIsInstance(document, PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

        document = PwDocument(schema='qes.xsd')
        self.assertIsInstance(document, PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/qes.xsd"))

        document = PwDocument(schema='qes-20180511.xsd')
        self.assertIsInstance(document, PwDocument)
        self.assertTrue(document.schema.url.endswith("qeschema/schemas/releases/qes-20180511.xsd"))

    def test_init_with_schema_as_text(self):
        with open(os.path.join(self.schemas_dir, 'qes.xsd')) as fp:
            schema = fp.read()
        document = PwDocument(schema=schema)
        self.assertIsNone(document.schema.url)

    def test_fetch_schema(self):
        self.assertIsNone(XmlDocument.fetch_schema('missing.xsd'))
        self.assertIsNone(XmlDocument.fetch_schema('qes.xsd'))
        self.assertIsNone(QeDocument.fetch_schema('missing.xsd'))

        filename = QeDocument.fetch_schema('qes.xsd')
        self.assertTrue(filename.replace('\\', '/').endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('unknown-path/qes.xsd')
        self.assertTrue(filename.replace('\\', '/').endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('/unknown-path/qes.xsd')
        self.assertTrue(filename.replace('\\', '/').endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('file:///unknown-path/qes.xsd')
        self.assertTrue(filename.replace('\\', '/').endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('releases/qes.xsd')
        self.assertTrue(filename.replace('\\', '/').endswith("qeschema/schemas/qes.xsd"))

        filename = QeDocument.fetch_schema('qes_190304.xsd')
        self.assertTrue(
            filename.replace('\\', '/').endswith("qeschema/schemas/releases/qes_190304.xsd")
        )

        filename = QeDocument.fetch_schema('unknown/qes_190304.xsd')
        self.assertTrue(
            filename.replace('\\', '/').endswith("qeschema/schemas/releases/qes_190304.xsd")
        )

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
        document.read(os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml'))

        with self.assertRaises(XmlDocumentError):
            document.get_fortran_input()

    def test_read_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')

        with open(filename) as f:
            with self.assertRaises(TypeError):
                document.read(f)

        with self.assertRaises(ValueError):
            document.read(os.path.join(self.test_dir, 'resources/unknown.xml'))

        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.format, 'xml')
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, filename)
        else:
            self.assertTrue(document.filename.endswith('instance.xml'))

        filename = os.path.join(self.test_dir, 'resources/dummy/instance_xml')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.format, 'xml')
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, filename)
        else:
            self.assertTrue(document.filename.endswith('instance_xml'))

        filename = os.path.join(self.test_dir, 'resources/dummy/instance.json')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.format, 'json')
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, filename)
        else:
            self.assertTrue(document.filename.endswith('instance.json'))

        filename = os.path.join(self.test_dir, 'resources/dummy/instance_json')
        document.read(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertEqual(document.format, 'json')
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, filename)
        else:
            self.assertTrue(document.filename.endswith('instance_json'))

        if yaml is not None:
            filename = os.path.join(self.test_dir, 'resources/dummy/instance.yaml')
            document.read(filename)
            self.assertTrue(hasattr(document.root, 'tag'))
            self.assertEqual(document.root.tag, 'root')
            self.assertEqual(document.format, 'yaml')
            if platform.system() == 'Linux':
                self.assertEqual(document.filename, filename)
            else:
                self.assertTrue(document.filename.endswith('instance.yaml'))

            filename = os.path.join(self.test_dir, 'resources/dummy/instance_yaml')
            document.read(filename)
            self.assertTrue(hasattr(document.root, 'tag'))
            self.assertEqual(document.root.tag, 'root')
            self.assertEqual(document.format, 'yaml')
            if platform.system() == 'Linux':
                self.assertEqual(document.filename, filename)
            else:
                self.assertTrue(document.filename.endswith('instance_yaml'))

            filename = os.path.join(self.test_dir, 'resources/dummy/instance.csv')
            with self.assertRaises(ValueError):
                document.read(filename)

    def test_from_xml_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')

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
        document = XmlDocument(schema=os.path.join(self.test_dir, 'resources/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.json')

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

    @unittest.skipIf(yaml is None, "PyYAML library is not installed")
    def test_from_yaml_method(self):
        document = XmlDocument(schema=os.path.join(self.test_dir, 'resources/dummy/schema.xsd'))
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.yaml')

        document.from_yaml(filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, 'root')
        self.assertListEqual(document.errors, [])

        document.from_yaml(filename, path='root')
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
        document = XmlDocument(schema=os.path.join(self.test_dir, 'resources/dummy/schema.xsd'))

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
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')
        document = XmlDocument(schema=schema)

        with self.assertRaises(RuntimeError):
            document.write(self.output_file)
        document.read(filename)
        self.assertFalse(os.path.isfile(self.output_file))

        document.write(self.output_file)
        self.assertIsInstance(ElementTree.parse(self.output_file), ElementTree.ElementTree)

    def test_write_method_from_unbound(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')

        with open(filename) as fp:
            xml_data = fp.read()
        document = XmlDocument(xml_data, schema=schema)
        self.assertIsNone(document.filename)

        document.write(self.output_file)
        self.assertIsInstance(ElementTree.parse(filename), ElementTree.ElementTree)
        self.assertEqual(document.format, 'xml')
        if platform.system() == 'Linux':
            self.assertEqual(document.filename, self.output_file)
        else:
            self.assertTrue(document.filename.endswith('write_test_file'))

    def test_write_other_formats(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')

        document = XmlDocument(filename, schema)
        document.write(self.output_file, output_format='json')
        with open(self.output_file) as f:
            self.assertEqual(f.read().replace(' ', '').replace('\n', ''),
                             '{"root":{"node":[{"@a":10},"value",null]}}')

        if yaml is not None:
            document.write(self.output_file, output_format='yaml')
            with open(self.output_file) as f:
                self.assertEqual(f.read(), "root:\n  node:\n  - '@a': 10\n  - value\n  - null\n")

        with self.assertRaises(TypeError):
            with open(self.output_file, mode='w+') as f:
                document.write(f)

        with self.assertRaises(ValueError):
            document.write(self.output_file, output_format='csv')

    def test_to_dict_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.to_dict(keep_unknown=True),
                         {'root': {'node': [{"@a":10}, "value", None]}})
        self.assertEqual(document.to_dict(preserve_root=False),
                         {'node': [{"@a":10}, "value", None]})

    def test_to_json_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')

        document.read(filename)
        self.assertEqual(document.to_json().replace(' ', '').replace('\n', ''),
                         '{"root":{"node":[{"@a":10},"value",null]}}')
        self.assertFalse(os.path.isfile(self.output_file))

        document.to_json(filename=self.output_file)
        with open(self.output_file) as f:
            self.assertEqual(f.read().replace(' ', '').replace('\n', ''),
                             '{"root":{"node":[{"@a":10},"value",null]}}')

        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        self.assertFalse(os.path.isfile(self.output_file))

        with open(filename) as f:
            xml_data = f.read()
        document = XmlDocument(xml_data, schema)
        self.assertIsNone(document.filename)

        document.to_json(filename=self.output_file)
        with open(self.output_file) as f:
            self.assertEqual(f.read().replace(' ', '').replace('\n', ''),
                             '{"root":{"node":[{"@a":10},"value",null]}}')

    @unittest.skipIf(yaml is None, "PyYAML library is not installed")
    def test_to_yaml_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')
        document = XmlDocument(filename, schema)

        self.assertEqual(document.to_yaml(), "root:\n  node:\n  - '@a': 10\n  - value\n  - null\n")
        self.assertFalse(os.path.isfile(self.output_file))

        document.to_yaml(filename=self.output_file)
        with open(self.output_file) as f:
            self.assertEqual(f.read(), "root:\n  node:\n  - '@a': 10\n  - value\n  - null\n")

        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        self.assertFalse(os.path.isfile(self.output_file))

        with open(filename) as f:
            xml_data = f.read()
        document = XmlDocument(xml_data, schema)
        self.assertIsNone(document.filename)

        document.to_yaml(filename=self.output_file)
        with open(self.output_file) as f:
            self.assertEqual(f.read(), "root:\n  node:\n  - '@a': 10\n  - value\n  - null\n")

    def test_iter_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')
        document.read(filename)

        root = document.root
        self.assertEqual(list(document.iter()), [root, root[0], root[1], root[2]])

    def test_find_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.find('.'), document.root)
        self.assertEqual(document.find('/node'), document.root[0])

    def test_findall_method(self):
        schema = os.path.join(self.test_dir, 'resources/dummy/schema.xsd')
        document = XmlDocument(schema=schema)
        filename = os.path.join(self.test_dir, 'resources/dummy/instance.xml')
        document.read(filename)

        self.assertEqual(document.findall('.'), [document.root])
        self.assertEqual(document.findall('/node'), document.root[:])

    def test_unsupported_schema(self):
        with self.assertRaises(NotImplementedError):
            PwDocument(schema=os.path.join(self.test_dir, 'resources/dummy/schema.xsd'))

    def test_incomplete_schema(self):
        schema_path = os.path.join(self.test_dir, 'resources/dummy/incomplete.xsd')
        document = PwDocument(schema=schema_path)

        xml_filename = os.path.join(self.test_dir, 'resources/dummy/incomplete.xml')
        document.read(xml_filename)

        with self.assertRaises(XmlDocumentError) as ctx:
            document.get_fortran_input()
        self.assertEqual(str(ctx.exception), "Missing input './input' in XML data!")

        document.root.append(ElementTree.Element('input'))
        with self.assertRaises(XmlDocumentError) as ctx:
            document.get_fortran_input()
        self.assertEqual(str(ctx.exception), "Missing input element in XSD schema!")

    def test_pw_document(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        document = PwDocument(source=xml_filename)

        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes-1.0}espresso')

        if platform.system() == 'Linux':
            self.assertEqual(document.filename, xml_filename)
        else:
            self.assertTrue(document.filename.endswith('Al001_relax_bfgs.xml'))

        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_pw_output_get_forces(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Si.xml')
        document = PwDocument(source=xml_filename)

        self.assertIsNone(document.get_forces())

        # TODO: add a case with ./output/forces/ section

    def test_pw_output_get_k_points(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Ni.xml')
        document = PwDocument(source=xml_filename)

        k_points = document.get_k_points()
        expected = [
            [-0.1666666666666667, 0.1666666666666667, 0.1666666666666667],
            [0.5, -0.5, 0.8333333333333333],
            [0.1666666666666667, -0.1666666666666667, 0.5],
            [-0.1666666666666666, -1.166666666666667, 0.1666666666666666],
            [-0.4999999999999999, -0.8333333333333334, -0.1666666666666666],
            [0.5, -0.5, -0.5]
        ]
        self.assertListEqual(k_points, expected)

    def test_pw_output_get_ks_eigenvalues(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Ni.xml')
        document = PwDocument(source=xml_filename)

        ks_eigenvalues = document.get_ks_eigenvalues()

        self.assertEqual(len(ks_eigenvalues), 6)
        for row in ks_eigenvalues:
            self.assertEqual(len(row), 18)
            for value in row:
                self.assertIsInstance(value, float)

    def test_pw_output_get_total_energy(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Ni.xml')
        document = PwDocument(source=xml_filename)

        total_energy = document.get_total_energy()
        self.assertEqual(total_energy, -30.44558256272531)

    def test_phonon_document(self):
        xml_filename = os.path.join(self.test_dir, 'resources/ph/al.elph.xml')
        document = PhononDocument(xml_filename)

        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes_ph_1.0}espressoph')

        if platform.system() == 'Linux':
            self.assertEqual(document.filename, xml_filename)
        else:
            self.assertTrue(document.filename.endswith('al.elph.xml'))

        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'inputPH')
        self.assertEqual(document.output_path, 'outputPH')

    def test_neb_document(self):
        xml_filename = os.path.join(self.test_dir, 'resources/neb/Al001_plus_H_bc3.xml')
        document = NebDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag, '{http://www.quantum-espresso.org/ns/neb}nebRun')

        if platform.system() == 'Linux':
            self.assertEqual(document.filename, xml_filename)
        else:
            self.assertTrue(document.filename.endswith('Al001_plus_H_bc3.xml'))

        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_td_document(self):
        xml_filename = os.path.join(self.test_dir, 'resources/tddfpt/Ag.tddfpt-eels.xml')
        document = TdDocument(source=xml_filename)

        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes_lr-1.0}tddfpt')

        if platform.system() == 'Linux':
            self.assertEqual(document.filename, xml_filename)
        else:
            self.assertTrue(document.filename.endswith('Ag.tddfpt-eels.xml'))

        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'input')
        self.assertEqual(document.output_path, 'output')

    def test_td_spectrum_document(self):
        xml_filename = os.path.join(self.test_dir, 'resources/tddfpt/CH4.tddfpt_pp.xml')
        document = TdSpectrumDocument()

        document.read(xml_filename)
        self.assertTrue(hasattr(document.root, 'tag'))
        self.assertEqual(document.root.tag,
                         '{http://www.quantum-espresso.org/ns/qes/qes_spectrum-1.0}spectrumDoc')

        if platform.system() == 'Linux':
            self.assertEqual(document.filename, xml_filename)
        else:
            self.assertTrue(document.filename.endswith('CH4.tddfpt_pp.xml'))

        self.assertEqual(document.format, 'xml')
        self.assertEqual(document.input_path, 'spectrumIn')
        self.assertEqual(document.output_path, 'output')

    def test_fortran_input_generator(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        document = PwDocument()
        document.read(xml_filename)

        self.assertFalse(os.path.isfile(self.output_file))

        document.write_fortran_input(self.output_file)
        with open(self.output_file) as f:
            fortran_input = f.read()

        if os.path.isfile(self.output_file):
            os.unlink(self.output_file)
        self.assertFalse(os.path.isfile(self.output_file))

        self.assertEqual(fortran_input[:9], '&CONTROL\n')
        self.assertEqual(fortran_input, document.get_fortran_input())

    def test_pw_get_atomic_positions(self):
        source = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        document = PwDocument(source)
        positions = document.get_atomic_positions()
        self.assertIsNone(positions)

        source = os.path.join(self.test_dir, 'resources/pw/Ni.xml')
        document = PwDocument(source)
        positions = document.get_atomic_positions()
        self.assertEqual(positions, (['Ni'], [[0.0, 0.0, 0.0]]))

    def test_pw_get_cell_parameters(self):
        source = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        document = PwDocument(source)
        cells = document.get_cell_parameters()
        self.assertIsNone(cells)

        source = os.path.join(self.test_dir, 'resources/pw/Ni.xml')
        document = PwDocument(source)
        cells = document.get_cell_parameters()
        self.assertListEqual(
            cells, [[-3.325, 0.0, 3.325], [0.0, 3.325, 3.325], [-3.325, 3.325, 0.0]]
        )

    def test_pw_get_stress(self):
        source = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        document = PwDocument(source)
        stress = document.get_stress()
        self.assertIsNone(stress)

        source = os.path.join(self.test_dir, 'resources/pw/Si.xml')
        document = PwDocument(source)
        stress = document.get_stress()
        self.assertListEqual(
            stress,
            [[-1.825058728527109e-06, 1.058791184067875e-22, -1.058791184067875e-22],
             [1.058791184067875e-22, -1.825058728527109e-06, 0.0],
             [-1.058791184067875e-22, 1.058791184067875e-22, -1.825058728527109e-06]]
        )


if __name__ == '__main__':
    unittest.main()
