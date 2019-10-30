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
from xml.etree import ElementTree
import xmlschema
from xmlschema.etree import etree_tostring

try:
    import yaml
except ImportError:
    yaml = None

from .converters import PwInputConverter, PhononInputConverter, NebInputConverter, \
    TdInputConverter, TdSpectrumInputConverter
from .exceptions import XmlDocumentError
from .utils import etree_iter_path

logger = logging.getLogger('qeschema')


class XmlDocument(object):
    """
    Generic XML schema based document. The XSD schema file associated is used for
    checking types, validation of the XML data and for lookup of default values.
    Loaded XML data is loader into memory into an ElementTree structure.
    Data files can be also in JSON or YAML format. In these cases the data source
    is converted to XML when loading.

    :param xsd_file: the filesystem path of the XSD reference schema.
    :param converter: an alternative converter class or instance used for convert \
    the XML document to other formats (JSON and YAML). If nothing is passed the \
    default converter of the *xmlschema* library is created and used.

    :ivar root: the root element of the XML tree.
    :ivar filename: the filepath of the data source file.
    :ivar format: the format of the data source file (XML, JSON, YAML).
    :ivar errors: the list of detected validation errors.
    """
    def __init__(self, xsd_file, converter=None):
        self.root = None
        self.filename = None
        self.format = None
        self.errors = []

        self.xsd_file = xsd_file
        self.schema = xmlschema.XMLSchema(xsd_file, converter=converter)

    @property
    def converter(self):
        """The default converter applied to data format conversions."""
        return self.schema.converter

    @property
    def namespaces(self):
        """Schema namespaces, that is a dictionary that maps prefixes to URI."""
        return self.schema.namespaces

    def read(self, filename, validation='strict', converter=None):
        """
        Read configuration from a text file in a specific data format. Input
        data files can be XML, JSON or YAML.

        :param filename: filepath of the data source file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param converter: the class used for converting non-XML data sources. \
        If left to `None` the default converter of the xmlschema library is used.
        """
        if not isinstance(filename, str):
            raise TypeError("wrong type for argument 'filename'")
        elif not os.path.isfile(filename):
            raise ValueError("{!r} is not a file".format(filename))

        ext = filename.strip().lower().rpartition('.')[2] if '.' in filename else None

        if ext == 'xml':
            self.root, self.errors = self.from_xml(filename, validation)
            self.format = 'xml'
        elif ext == 'json':
            self.root, self.errors = self.from_json(filename, validation, converter)
            self.format = 'json'
        elif ext in ('yml', 'yaml'):
            self.root, self.errors = self.from_yaml(filename, validation, converter)
            self.format = 'yaml'
        else:
            try:
                self.root, self.errors = self.from_xml(filename, validation)
                self.format = 'xml'
            except ElementTree.ParseError:
                try:
                    self.root, self.errors = self.from_json(filename, validation, converter)
                    self.format = 'json'
                except json.JSONDecodeError:
                    try:
                        self.root, self.errors = self.from_yaml(filename, validation, converter)
                        self.format = 'yaml'
                    except yaml.YAMLError:
                        raise ValueError("input file is not in neither of XML, JSON or YAML formats")

        self.filename = filename

    def from_xml(self, source, validation='strict'):
        """
        Load source data from an XML file. Data is validated against the schema.

        :param source: a filepath to an XML file or a string containing XML data.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :return: a couple with the root element of the XML ElementTree a list \
        containing the detected errors.
        """
        if not isinstance(source, str):
            raise TypeError("the source argument must be a string!")
        elif '\n' not in source and not source.strip().startswith('<'):
            root = ElementTree.parse(source).getroot()
        else:
            root = ElementTree.XML(source)

        if validation == 'lax':
            return root, [e for e in self.schema.iter_errors(source)]
        elif validation != 'skip':
            self.schema.validate(source)
        return root, []

    def from_json(self, source, validation='strict', converter=None, **kwargs):
        """
        Converts a JSON encoded file to an XML ElementTree structure.
        Data is validated against the schema during conversion.

        :param source: a filepath to a JSON file or a string containing JSON data.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param converter: the class used for converting non-XML data sources. \
        If left to `None` the default converter of the xmlschema library is used.
        :return: a couple with the root element of the XML ElementTree a list \
        containing the detected errors.
        """
        preserve_root = kwargs.pop('preserve_root', True)
        try:
            json.loads(source)
        except ValueError:
            with open(source) as f:
                obj = xmlschema.from_json(f, self.schema, validation=validation,
                                          converter=converter, preserve_root=preserve_root)
        else:
            obj = xmlschema.from_json(source, self.schema, validation=validation,
                                      converter=converter, preserve_root=preserve_root)

        return obj if isinstance(obj, tuple) else obj, []

    def from_yaml(self, source, validation='strict', converter=None, **kwargs):
        """
        Converts a YAML encoded file to an XML ElementTree structure.
        Data is validated against the schema during conversion.

        :param source: a filepath to a YAML file or a string containing YAML data.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param converter: the class used for converting non-XML data sources. \
        If left to `None` the default converter of the xmlschema library is used.
        :return: a couple with the root element of the XML ElementTree and a list \
        containing the detected errors.
        """
        preserve_root = kwargs.pop('preserve_root', True)
        if yaml is None:
            raise RuntimeError("PyYAML library is not installed!")
        elif not isinstance(source, str):
            raise TypeError("the source argument must be a string!")
        elif '\n' not in source and not source.strip().startswith('<'):
            with open(source) as f:
                data = yaml.load(f, Loader=yaml.Loader)
        else:
            data = yaml.load(source, Loader=yaml.Loader)

        obj = self.schema.encode(data, validation=validation, converter=converter,
                                 preserve_root=preserve_root)
        return obj if isinstance(obj, tuple) else obj, []

    def from_dict(self, data, validation='strict', converter=None):
        """
        Converts a Python object to an XML ElementTree structure.
        Object data is validated against the schema during conversion.

        :param data: filepath of the data source file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param converter: the class used for converting the object to XML. \
        If left to `None` the default converter of the xmlschema library is used.
        :return: a couple with the root element of the XML ElementTree and a list \
        containing the detected errors.
        """
        obj = self.schema.encode(data, validation=validation, converter=converter)
        return obj if isinstance(obj, tuple) else obj, []

    def write(self, filename, output_format='xml', validation='strict', converter=None):
        """
        Write XML data to a file.

        :param filename: filepath of the destination file.
        :param output_format: the data format of the output file.
        :param validation: validation mode, can be 'strict', 'lax' or 'skip'.
        :param converter: the class used for converting the object to XML. \
        If left to `None` the default converter of the xmlschema library is used.
        """
        if not isinstance(filename, str):
            raise TypeError("the filename argument must be a string!")
        elif self.root is None:
            raise RuntimeError("No XML data loaded!")

        output_format = output_format.strip().lower()
        if output_format == 'XML':
            with open(filename, 'w+') as f:
                f.write(etree_tostring(self.root))

        elif output_format == 'json':
            obj = self.to_dict(validation, converter)
            with open(filename, 'w+') as f:
                return json.dump(f, obj, sort_keys=True, indent=4)

        elif output_format == 'yaml':
            if yaml is None:
                raise RuntimeError("PyYAML library is not installed!")

            obj = self.to_dict(validation, converter)
            with open(filename, 'w+') as f:
                yaml.dump(obj, stream=f, default_flow_style=False)
        else:
            raise ValueError("Accepted output_format are: 'XML'(default), 'YAML' and 'JSON'!")

    def to_dict(self, validation='strict', converter=None, **kwargs):
        obj = self.schema.to_dict(
            source=self.root,
            validation=validation,
            converter=converter,
            preserve_root=kwargs.pop('preserve_root', True),
            **kwargs
        )
        return obj[0] if isinstance(obj, tuple) else obj

    def to_json(self, filename=None, validation='strict', converter=None, **kwargs):
        """Converts the XML data to a JSON string."""
        if filename is None:
            return json.dumps(self.to_dict(validation, converter, **kwargs), sort_keys=True, indent=4)

        with open(filename) as f:
            json.dump(self.to_dict(validation, converter, **kwargs), f, sort_keys=True, indent=4)

    def to_yaml(self, filename=None, validation='strict', converter=None, **kwargs):
        """Converts the configuration to YAML string."""
        if yaml is None:
            raise RuntimeError("PyYAML library is not installed!")
        elif filename is None:
            return yaml.dump(self.to_dict(validation, converter, **kwargs), default_flow_style=False)

        with open(filename) as f:
            yaml.dump(self.to_dict(validation, converter, **kwargs), stream=f, default_flow_style=False)

    def get(self, qualified_name):
        section, _, item = qualified_name.partition(".")
        query = "./{0}/{1}".format(section, item)
        node = self.root.find(query)
        if node is None:
            return
        return node.text

    def __getitem__(self, section):
        query = "./{0}".format(section)
        parent = self.root.find(query)
        return dict((item.tag, item.text) for item in parent)

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
        namespaces = namespaces or {}
        namespaces.update(self.namespaces)
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
        namespaces = namespaces or {}
        namespaces.update(self.namespaces)
        if path[:1] == "/":
            path = "." + path
        return self.root.findall(path, namespaces)


class QeDocument(XmlDocument):
    """
    Base class for schema based data for Quantum ESPRESSO applications.
    """
    SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schemas')

    def __init__(self, xsd_file, input_builder):
        super(QeDocument, self).__init__(xsd_file)
        self.input_builder = input_builder

        self.default_namespace = self.schema.target_namespace
        qe_nslist = list(map(self.namespaces.get, ['qes', 'neb', 'qes_ph', 'qes_lr', 'qes_spectrum']))
        if self.default_namespace not in qe_nslist:
            raise NotImplementedError(
                "Converter not implemented for this schema {}".format(self.default_namespace)
            )

    def read_fortran_input(self, filename):
        """
        Reads a Fortran namelist input from file and converts to XML input.

        :param filename: a filepath to the namelist file containing the Fortran input.
        :return: the input XML Element.
        """
        raise NotImplementedError

    def write_fortran_input(self, filename):
        """
        Converts the XML input data to a Fortran namelist input and writes it to a file.

        :param filename:
        """
        with open(filename, mode='w+') as f:
            f.write(self.get_fortran_input())

    @property
    def input_path(self):
        return 'input'

    @property
    def output_path(self):
        return 'output'

    def get_fortran_input(self, use_defaults=True):

        if self.root is None:
            raise XmlDocumentError("XML data is not loaded!")

        qe_input = self.input_builder(xml_file=self.filename)
        input_path = '//%s' % self.input_path

        input_root = self.find(input_path)
        # Extract values from input's subtree of the XML document
        for elem, path in etree_iter_path(input_root, path=input_path):

            rel_path = path.replace(input_path, '.')
            xsd_element = self.schema.find(path)
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

        if use_defaults:
            # Add defaults for elements not included in input XML subtree
            for path in filter(
                    lambda x: x.startswith(input_path) and self.find(x) is None,
                    self.schema.elements
            ):
                rel_path = path.replace(input_path, '.')
                tag = rel_path.rsplit('/', 1)[-1]
                xsd_attributes = self.schema.get_attributes(path)
                defaults_dict = {}
                defaults_path_keys = []

                try:
                    # Add default values for attributes
                    for attr_name, xsd_attribute in xsd_attributes.items():
                        default_value = xsd_attribute.get_default()
                        if default_value is not None:
                            path_key = '%s/%s' % (rel_path, attr_name)
                            xsd_type = xsd_attribute.xsd_type
                            value = xsd_type.decode(default_value)
                            defaults_dict[attr_name] = value
                            defaults_path_keys.append(path_key)
                except AttributeError:
                    pass

                default_value = self.schema.get_element_default(path)
                if default_value is not None:
                    path_key = '%s/$' % rel_path if xsd_attributes else rel_path
                    xsd_type = self.schema.get_element_type(path)
                    value = xsd_type.decode(default_value)
                    defaults_dict[path_key.rsplit("/")[-1]] = value
                    defaults_path_keys.append(path_key)

                for path_key in defaults_path_keys:
                    qe_input.set_path(path_key, tag, defaults_dict)

        return qe_input.get_fortran_input()


class PwDocument(QeDocument):
    """
    Class to manage PW XML documents.
    """
    def __init__(self, xsd_file=None):
        if xsd_file is None:
            xsd_file = os.path.join(self.SCHEMAS_DIR, 'qes.xsd')
        super(PwDocument, self).__init__(xsd_file, input_builder=PwInputConverter)


class PhononDocument(QeDocument):
    """
    Class to manage Phonon XML documents.
    """
    def __init__(self, xsd_file=None):
        if xsd_file is None:
            xsd_file = os.path.join(self.SCHEMAS_DIR, 'ph_temp.xsd')
        super(PhononDocument, self).__init__(xsd_file, input_builder=PhononInputConverter)

    @property
    def input_path(self):
        return 'inputPH'

    @property
    def output_path(self):
        return 'outputPH'

    def get_fortran_input(self, use_defaults=False):
        """
        overrides get_qe_input calling super get_qe_input with use_defaults set to False. 
        :param use_defaults: 
        :return: the input as obtained from its input builder
        """
        return super(PhononDocument, self).get_fortran_input(use_defaults=use_defaults)


class NebDocument(QeDocument):
    """
    Class to manage NEB XML documents.
    """
    def __init__(self, xsd_file=None):
        if xsd_file is None:
            xsd_file = os.path.join(self.SCHEMAS_DIR, 'qes_neb.xsd')
        super(NebDocument, self).__init__(xsd_file, input_builder=NebInputConverter)


class TdDocument(QeDocument):
    """
    Class to manage TDDFPT XML documents.
    """
    def __init__(self, xsd_file=None):
        if xsd_file is None:
            xsd_file = os.path.join(self.SCHEMAS_DIR, 'tddfpt.xsd')
        super(TdDocument, self).__init__(xsd_file, input_builder=TdInputConverter)

    @property
    def input_path(self):
        return 'input'


class TdSpectrumDocument(QeDocument):
    """
    Class to manage turbo-spectrum inputs
    """
    def __init__(self, xsd_file=None):
        if xsd_file is None:
            xsd_file = os.path.join(self.SCHEMAS_DIR, 'qes_spectrum.xsd')
        super(TdSpectrumDocument, self).__init__(xsd_file, input_builder=TdSpectrumInputConverter)

    @property
    def input_path(self):
        return 'spectrumIn'
