# -*- coding: utf-8 -*-
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# Authors: Davide Brunato
#
import logging
import os.path
import json
from abc import ABCMeta
from functools import wraps
from xml.etree import ElementTree
import xmlschema
from xmlschema.etree import etree_tostring

try:
    import yaml
except ImportError:
    yaml = None

from .namespaces import *
from .converters import RawInputConverter, PwInputConverter, PhononInputConverter, \
    NebInputConverter, TdInputConverter, TdSpectrumInputConverter
from .exceptions import XmlDocumentError
from .utils import etree_iter_path

logger = logging.getLogger('qeschema')

SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schemas')


def requires_xml_data(method):
    """A decorator for XML document methods that require XML data to be loaded."""
    @wraps(method)
    def check_xml_data(self, *args, **kwargs):
        if self.root is None:
            raise XmlDocumentError("No XML data loaded!")
        return method(self, *args, **kwargs)
    return check_xml_data


def removeprefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s


class XmlDocument(object):
    """
    Base class for a generic XML document based on an XSD schema. The schema
    associated is used for checking types, validation of the XML data and for
    lookup of default values. XML data is loaded into memory into an ElementTree
    structure. Data files can be also in JSON or YAML format, in these cases the
    data source is converted to XML when loading.

    :param source: can be a :class:`xmlschema.XMLResource` instance or a file-like \
    object or a file path or an URL of a resource or a string containing the XML data.
    :param schema: can be a :class:`xmlschema.XMLSchema` instance or a file-like \
    object or a file path or an URL of a resource or a string containing the XSD schema.

    :cvar SEARCH_PATHS: the sequence of search paths used by :meth:`fetch_schema` \
    for fetching schemas.
    :ivar root: the root element of the XML tree.
    :ivar filename: the filepath of the data source file.
    :ivar format: the format of the data source file (XML, JSON, YAML).
    :ivar errors: the list of detected validation errors.
    :ivar schema: the :class:`XMLSchema` instance associated with the document.
    """
    SEARCH_PATHS = ('.',)
    DEFAULT_SCHEMA = None

    def __init__(self, source=None, schema=None):
        self.root = None
        self.filename = None
        self.format = None
        self.errors = []
        self._namespaces = {}

        if source is None:
            source_schema = None
        else:
            if not isinstance(source, xmlschema.XMLResource):
                source = xmlschema.XMLResource(source)

            if source.namespace == XSD_NAMESPACE:
                raise XmlDocumentError("source is an XSD schema")

            for ns, location in source.iter_location_hints():
                if ns == source.namespace:
                    source_schema = self.fetch_schema(location)
                    if source_schema is not None:
                        break
            else:
                source_schema = None

        if isinstance(schema, xmlschema.XMLSchemaBase):
            self.schema = schema
        elif isinstance(schema, str) and '\n' not in schema \
                and not schema.lstrip().startswith('<'):
            self.schema = xmlschema.XMLSchema(self.fetch_schema(schema) or schema)
        elif schema is not None:
            self.schema = xmlschema.XMLSchema(schema)
        elif source_schema is not None:
            self.schema = xmlschema.XMLSchema(source_schema)
        elif self.DEFAULT_SCHEMA is not None:
            default_schema = self.fetch_schema(self.DEFAULT_SCHEMA)
            self.schema = xmlschema.XMLSchema(default_schema)
        else:
            raise XmlDocumentError("missing schema for XML data!")

        if source is not None:
            self.from_xml(source, validation='lax')

    @property
    def namespaces(self):
        """
        XML data namespaces map, a dictionary that maps prefixes to URI. An empty
        dictionary if the XML data file is not loaded or it doesn't contain any
        namespace declaration.
        """
        return {k: v for k, v in self._namespaces.items()}

    @classmethod
    def fetch_schema(cls, filename):
        filename = filename.strip()
        if os.path.isfile(filename):
            return filename

        if not filename.startswith('/'):
            for base_path in cls.SEARCH_PATHS:
                if os.path.isfile(os.path.join(base_path, filename)):
                    return os.path.join(base_path, filename)

        base_name = os.path.basename(filename)
        for base_path in cls.SEARCH_PATHS:
            if os.path.isfile(os.path.join(base_path, base_name)):
                return os.path.join(base_path, base_name)

    def read(self, filename, validation='strict', **kwargs):
        """
        Reads XML data from a file encoded in XML, JSON or YAML format.

        :param filename: filepath of the data source file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options to pass to the encoding method of the schema \
        instance in case of a non-XML data source.
        """
        if not isinstance(filename, str):
            raise TypeError("wrong type for argument 'filename'")
        elif not os.path.isfile(filename):
            raise ValueError("{!r} is not a file".format(filename))

        ext = filename.strip().lower().rpartition('.')[2] if '.' in filename else None

        if ext == 'xml':
            self.from_xml(filename, validation)
        elif ext == 'json':
            self.from_json(filename, validation, **kwargs)
        elif ext in ('yml', 'yaml'):
            self.from_yaml(filename, validation, **kwargs)
        else:
            try:
                self.from_xml(filename, validation)
            except (ElementTree.ParseError, SyntaxError):
                try:
                    self.from_json(filename, validation, **kwargs)
                except json.JSONDecodeError:
                    try:
                        self.from_yaml(filename, validation, **kwargs)
                    except yaml.YAMLError:
                        raise ValueError(
                            "input file is not in neither of XML, JSON or YAML formats"
                        )

    def from_xml(self, source, validation='strict', **kwargs):
        """
        Load XML data. Data is validated against the schema.

        :param source: a filepath to an XML file or a string containing XML data.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options for creating the :class:`xmlschema.XMLResource` \
        instance used for reading the XML data.
        :return: a couple with the root element of the XML ElementTree a list \
        containing the detected errors.
        """
        if not isinstance(source, xmlschema.XMLResource):
            source = xmlschema.XMLResource(source, **kwargs)

        errors = []
        if validation == 'strict':
            self.schema.validate(source)
        elif validation == 'lax':
            errors.extend(e for e in self.schema.iter_errors(source))

        self.root = source.root
        self.errors = errors
        self._namespaces = source.get_namespaces()

        if source.url is None:
            self.filename = None
            self.format = None
        else:
            self.filename = removeprefix(source.url, 'file://')
            self.format = 'xml'

    def from_json(self, source, validation='strict', **kwargs):
        """
        Load JSON encoded data. Data is converted to an XML ElementTree structure
        and validated against the schema.

        :param source: a filepath to a JSON file or a string containing JSON data.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options to pass to the encoding method of the schema instance.
        :return: the root element of the XML ElementTree data structure and a list \
        containing the detected errors.
        :raise: an :class:`xmlschema.XMLSchemaValidationError` if validation is strict \
        and at least an error is found.
        """
        if not isinstance(source, str):
            raise TypeError("the source argument must be a string!")

        preserve_root = kwargs.pop('preserve_root', True)
        try:
            json.loads(source)
        except ValueError:
            with open(source) as f:
                obj = xmlschema.from_json(f, self.schema, validation=validation,
                                          preserve_root=preserve_root)
            filename = source.strip()
        else:
            obj = xmlschema.from_json(source, self.schema, validation=validation,
                                      preserve_root=preserve_root)
            filename = None

        if isinstance(obj, tuple):
            self.root, self.errors = obj
        else:
            self.root, self.errors = obj, []
        self.filename = filename
        self.format = 'json' if filename else None

    def from_yaml(self, source, validation='strict', **kwargs):
        """
        Converts a YAML encoded file to an XML ElementTree structure.
        Data is validated against the schema during conversion.

        :param source: a filepath to a YAML file or a string containing YAML data.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options to pass to the encoding method of the schema instance.
        :return: a couple with the root element of the XML ElementTree and a list \
        containing the detected errors.
        """
        if yaml is None:
            raise RuntimeError("PyYAML library is not installed!")
        elif not isinstance(source, str):
            raise TypeError("the source argument must be a string!")
        elif '\n' not in source and not source.strip().startswith('<'):
            with open(source) as f:
                data = yaml.load(f, Loader=yaml.Loader)
            filename = source.strip()
        else:
            data = yaml.load(source, Loader=yaml.Loader)
            filename = None

        preserve_root = kwargs.pop('preserve_root', True)
        converter = kwargs.pop('converter', xmlschema.UnorderedConverter)
        if 'path' not in kwargs and isinstance(data, dict) and len(data) == 1:
            kwargs['path'] = list(data.keys())[0]

        obj = self.schema.encode(data, validation=validation, converter=converter,
                                 preserve_root=preserve_root, **kwargs)

        if isinstance(obj, tuple):
            self.root, self.errors = obj
        else:
            self.root, self.errors = obj, []
        self.filename = filename
        self.format = 'yaml' if filename else None

    def from_dict(self, data, validation='strict', **kwargs):
        """
        Converts a Python object to an XML ElementTree structure.
        Object data is validated against the schema during conversion.

        :param data: filepath of the data source file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options to pass to the encoding method of the schema instance.
        :return: a couple with the root element of the XML ElementTree and a list \
        containing the detected errors.
        """
        preserve_root = kwargs.pop('preserve_root', True)
        obj = self.schema.encode(data, validation=validation, preserve_root=preserve_root, **kwargs)
        if isinstance(obj, tuple):
            self.root, self.errors = obj
        else:
            self.root, self.errors = obj, []
        self.filename = self.format = None

    @requires_xml_data
    def write(self, filename, output_format='xml', validation='strict', **kwargs):
        """
        Write loaded XML data to a file. Binds the document to saved file if
        it's not already bound to another file.

        :param filename: filepath of the destination file.
        :param output_format: the data format of the output file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options for the decoding method of the schema instance.
        """
        if not isinstance(filename, str):
            raise TypeError("the filename argument must be a string!")

        output_format = output_format.strip().lower()
        if output_format == 'xml':
            with open(filename, 'w+') as f:
                f.write(etree_tostring(self.root))

        elif output_format == 'json':
            obj = self.to_dict(validation, **kwargs)
            with open(filename, 'w+') as f:
                return json.dump(obj, f, sort_keys=True, indent=4)

        elif output_format == 'yaml':
            if yaml is None:
                raise RuntimeError("PyYAML library is not installed!")

            obj = self.to_dict(validation, **kwargs)
            with open(filename, 'w+') as f:
                yaml.dump(obj, stream=f, default_flow_style=False)
        else:
            raise ValueError("Accepted output_format are 'xml', 'json' or 'yaml'!")

        if self.filename is None:
            self.filename = filename
            self.format = output_format

    @requires_xml_data
    def to_dict(self, validation='strict', **kwargs):
        """
        Converts loaded XML data to a nested dictionary.

        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options for the decoding method of the schema instance.
        :returns: a dictionary.
        """
        obj = self.schema.to_dict(
            source=self.root,
            validation=validation,
            namespaces=kwargs.get('namespaces') or self.namespaces,
            preserve_root=kwargs.pop('preserve_root', True),
            **kwargs
        )
        return obj[0] if isinstance(obj, tuple) else obj

    def to_json(self, filename=None, validation='strict', **kwargs):
        """
        Converts loaded XML data to a JSON string or file.

        :param filename: filepath of the destination file. Binds the document to \
        this file if it's not already bound to another file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options for the decoding method of the schema instance.
        """
        data = self.to_dict(validation, **kwargs)
        if filename is None:
            return json.dumps(data, sort_keys=True, indent=4)

        with open(filename, mode='w+') as f:
            json.dump(data, f, sort_keys=True, indent=4)

        if filename is not None and self.filename is None:
            self.filename = filename
            self.format = 'json'

    def to_yaml(self, filename=None, validation='strict', **kwargs):
        """
        Converts loaded XML data to YAML string or file.

        :param filename: filepath of the destination file. Binds the document to \
        this file if it's not already bound to another file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param kwargs: other options for the decoding method of the schema instance.
        """
        if yaml is None:
            raise RuntimeError("PyYAML library is not installed!")

        data = self.to_dict(validation, **kwargs)
        if filename is None:
            return yaml.dump(data, default_flow_style=False)

        with open(filename, mode='w+') as f:
            yaml.dump(data, stream=f, default_flow_style=False)

        if filename is not None and self.filename is None:
            self.filename = filename
            self.format = 'yaml'

    # ElementTree API wrappers

    def iter(self, tag=None):
        return self.root.iter(tag)

    def find(self, path, namespaces=None):
        """
        Find first matching element by tag name or path.

        :param path: is a string having either an element tag or an XPath,
        :param namespaces: is an optional mapping from namespace prefix to full name.
        :return: the first matching element, or None if no element was found
        """
        if path[:1] == "/":
            path = "." + path
        return self.root.find(path, namespaces)

    def findall(self, path, namespaces=None):
        """
        Find all matching subelements by tag name or path.

        :param path: is a string having either an element tag or an XPath,
        :param namespaces: is an optional mapping from namespace prefix to full name.
        :return: the first matching element, or None if no element was found
        """
        if path[:1] == "/":
            path = "." + path
        return self.root.findall(path, namespaces)


class QeDocument(XmlDocument, metaclass=ABCMeta):
    """
    Abstract base class for schema-based XML documents of Quantum ESPRESSO applications.
    """
    SEARCH_PATHS = (SCHEMAS_DIR, os.path.join(SCHEMAS_DIR, 'releases'), '.')
    DEFAULT_INPUT_BUILDER = None

    def __init__(self, source=None, schema=None, input_builder=None):
        super(QeDocument, self).__init__(source, schema)

        if input_builder is None:
            self.input_builder = self.DEFAULT_INPUT_BUILDER
        elif not isinstance(input_builder, type) or \
                not issubclass(input_builder, RawInputConverter):
            msg = "3rd argument must be a {!r} subclass"
            raise XmlDocumentError(msg.format(RawInputConverter))
        else:
            self.input_builder = input_builder

        self.default_namespace = self.schema.target_namespace
        qe_prefixes = ['qes', 'neb', 'qes_ph', 'qes_lr', 'qes_spectrum']
        qe_nslist = list(map(self.schema.namespaces.get, qe_prefixes))
        if self.default_namespace not in qe_nslist:
            raise NotImplementedError(
                "Converter not implemented for this schema {}".format(self.default_namespace)
            )

    @property
    def input_path(self):
        """The path to XML input section."""
        return 'input'

    @property
    def output_path(self):
        """The path to XML input section."""
        return 'output'

    def write_fortran_input(self, filename):
        """
        Converts the XML input data to a Fortran namelist input and writes it to a file.

        :param filename: the pathname of the file to use to save the Fortran namelist.
        """
        with open(filename, mode='w+') as f:
            f.write(self.get_fortran_input())

    @requires_xml_data
    def get_fortran_input(self, use_defaults=True):
        """
        Converts the XML input data to a Fortran namelist input.

        :param use_defaults: use the defaults of the XSD schema to fill missing values.
        :returns: a string.
        """
        qe_input = self.input_builder(xml_file=self.filename)
        input_path = './%s' % self.input_path

        input_root = self.find(input_path)
        if input_root is None:
            raise XmlDocumentError("Missing input {!r} in XML data!".format(input_path))

        for schema_root in self.schema.elements.values():
            if schema_root.find(input_path):
                break
        else:
            raise XmlDocumentError("Missing input element in XSD schema!")

        # Extract values from input's subtree of the XML document
        for elem, path in etree_iter_path(input_root, path=input_path):
            rel_path = path.replace(input_path, '.')
            xsd_element = schema_root.find(path)
            if xsd_element is None:
                logger.error("%r doesn't match any element!" % path)
                continue
            else:
                value = xsd_element.decode(elem, use_defaults=use_defaults)
                if isinstance(value, str):
                    value = value.strip()
                node_dict = {elem.tag: value}
            logger.debug("Add input for node '{0}' with dict '{1}'".format(elem.tag, node_dict))

            # Convert attributes
            for attr_name, value in elem.attrib.items():
                logger.debug("Convert attribute '%s' of element '%s'" % (attr_name, path))
                path_key = '%s/@%s' % (rel_path, attr_name)
                if path_key not in qe_input:
                    logger.debug("Attribute's path '%s' not in converter!" % path_key)
                    continue
                qe_input.set_path(path_key, elem.tag, node_dict)

            logger.debug("Convert element '%s'" % path)
            path_key = '%s/$' % rel_path if xsd_element.attributes else rel_path
            if path_key not in qe_input:
                logger.debug("Element's path '%s' not in converter!" % path_key)
                continue
            qe_input.set_path(path_key, elem.tag, node_dict)

        return qe_input.get_qe_input()


class PwDocument(QeDocument):
    """
    Class to manage PW XML documents.
    """
    DEFAULT_SCHEMA = 'qes.xsd'
    DEFAULT_INPUT_BUILDER = PwInputConverter

    @requires_xml_data
    def get_atomic_positions(self):
        """
        Gets atomic symbols and atomic positions from XML output data.

        :return: the list of atomic symbols and a nested list containing the coordinates
        """
        path = './/output//atomic_positions'
        elem = self.find(path)
        if elem is not None:
            atomic_positions = self.schema.find(path).decode(elem)
            atoms = atomic_positions.get('atom')
            if not isinstance(atoms, list):
                atoms = [atoms]
            symbols = [a['@name'] for a in atoms]
            positions = [a['$'] for a in atoms]
            return symbols, positions

    @requires_xml_data
    def get_cell_parameters(self):
        """
        Gets cell parameters from an XML output data.

        :return: a nested list containing the cell vectors in Bohr atomic units
        """
        path = './/output//cell'
        elem = self.find(path)
        if elem is not None:
            cell = self.schema.find(path).decode(elem)
            return [cell['a1'], cell['a2'], cell['a3']]

    @requires_xml_data
    def get_stress(self):
        """
        Gets stress tensor from the XML output data, if present.

        :return: nested list containing the stress tensor in C order
        """
        path = './/output//stress'
        elem = self.find(path)
        if elem is not None:
            stress = self.schema.find(path).decode(elem)
            try:
                stress = stress['$']
            except TypeError:
                pass
            return [stress[::3], stress[1::3], stress[2::3]]

    @requires_xml_data
    def get_forces(self):
        """
        Gets forces from the XML output data, if present.

        :return: the list of atomic symbols plus a nested list with the forces \
        in atomic units
        """
        path = './/output/forces'
        elem = self.find(path)
        if elem is not None:
            forces = self.schema.find(path).decode(elem)
            path = './/output//atomic_positions'
            atomic_positions = self.schema.find(path).decode(self.find(path))
            atoms = atomic_positions.get('atom', [])
            if not isinstance(atoms, list):
                atoms = [atoms]
            symbols = [a['@name'] for a in atoms]
            i0 = range(3 * len(atoms))[::3]
            i1 = range(3 * len(atoms) + 1)[3::3]
            forces = [forces['$'][i:j] for i, j in zip(i0, i1)]
            return symbols, forces

    @requires_xml_data
    def get_k_points(self):
        """
        Extracts the k_points list from the XML output data.

        :return: nested list with k_points
        """
        path = './/output//k_point'
        return [self.schema.find(path).decode(e)['$'] for e in self.findall(path)]

    @requires_xml_data
    def get_ks_eigenvalues(self):
        """
        Extracts the eigenvalues from the XML output data.

        :return: nested list of KS eigenvalues for each k_point in Hartree Units
        """
        path = './/output//ks_energies/eigenvalues'
        return [self.schema.find(path).decode(e)['$'] for e in self.findall(path)]

    @requires_xml_data
    def get_total_energy(self):
        """
        Extracts the total energy from the  XML output data.

        :return: total energy in Hartree Units
        """
        path = './/output//etot'
        return self.schema.find(path).decode(self.find(path))


class PhononDocument(QeDocument):
    """
    Class to manage Phonon XML documents.
    """
    DEFAULT_SCHEMA = 'ph_xmlschema.xsd'
    DEFAULT_INPUT_BUILDER = PhononInputConverter

    @property
    def input_path(self):
        return 'inputPH'

    @property
    def output_path(self):
        return 'outputPH'

    def get_fortran_input(self, use_defaults=False):
        """
        Overrides get_fortran_input() setting *use_defaults* optional argument to False.

        :param use_defaults:
        :return: the input as obtained from its input builder
        """
        return super(PhononDocument, self).get_fortran_input(use_defaults=use_defaults)


class NebDocument(QeDocument):
    """
    Class to manage NEB XML documents.
    """
    DEFAULT_SCHEMA = 'qes_neb.xsd'
    DEFAULT_INPUT_BUILDER = NebInputConverter


class TdDocument(QeDocument):
    """
    Class to manage TDDFPT XML documents.
    """
    DEFAULT_SCHEMA = 'tddfpt.xsd'
    DEFAULT_INPUT_BUILDER = TdInputConverter

    @property
    def input_path(self):
        return 'input'


class TdSpectrumDocument(QeDocument):
    """
    Class to manage turbo-spectrum XML inputs
    """
    DEFAULT_SCHEMA = 'qes_spectrum.xsd'
    DEFAULT_INPUT_BUILDER = TdSpectrumInputConverter

    @property
    def input_path(self):
        return 'spectrumIn'
