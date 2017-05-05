# -*- coding: utf-8 -*-
#
# Copyright (c), 2015-2016, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato
#
import logging
import os.path
from xml.etree import ElementTree
import xmlschema
from xmlschema.exceptions import XMLSchemaValidationError

from .converters import PwInputConverter, PhononInputConverter, NebInputConverter
from .exceptions import ConfigError
from .utils import etree_iter_path

logger = logging.getLogger('qespresso')


class XmlDocument(object):
    """
    Generic XML schema based document.

    A XSD schema is needed for checking types, validation of the configuration
    and for lookup of default values of the attributes. Full schema's validation
    is available only if lxml library is installed.

    Supported files data format for configuration are XML, YAML and JSON.
    """
    def __init__(self, xsd_file):
        self._document = None
        self._config_file = None
        self._file_format = None
        self._xsd_file = xsd_file

        try:
            self.schema = xmlschema.XMLSchema(xsd_file)
        except IOError as err:
            logger.error('XML Schema not available: %s' % err)
            self.schema = None
            raise
        self.namespaces = self.schema.namespaces

    def read(self, filename, data_format='XML'):
        """
        Read configuration from a text file in a specific data format.

        :param filename: Name of the text file containing the configuration
        :param data_format: Input file data format (XML, JSON or YAML)
        """
        data_format = data_format.upper()
        old_config = (self._document, self._config_file)
        try:
            if data_format == 'XML':
                self._document = self.parse_xml(filename)
            elif data_format == 'YAML':
                self._document = self.parse_yaml(filename)
            elif data_format == 'JSON':
                self._document = self.parse_json(filename)
            else:
                raise ValueError("'input_format' argument must be 'XML', 'YAML' or 'JSON'")
        except XMLSchemaValidationError:
            raise
        else:
            self._config_file = filename

        # Validation of the new ElementTree structure (valid
        try:
            self.validate()
        except XMLSchemaValidationError:
            self._document, self._config_file = old_config
            raise

    def parse_xml(self, filename):
        """
        Return an ElementTree object representing an XML file
        """
        return ElementTree.parse(filename)

    def parse_json(self, filename):
        """
        Build an ElementTree object representing a YAML file
        """
        logger.warning("JSON read is a TODO!")
        return

    def parse_yaml(self, filename):
        """
        Build an ElementTree object representing a YAML file
        """
        logger.warning("YAML read is a TODO!")
        return

    def from_dict(self):
        """
        Build an ElementTree object from a dictionary
        """
        return

    def validate(self, filename=None):
        if filename is not None:
            try:
                self.validate()
            except XMLSchemaValidationError as e:
                e.message = "Invalid XML file '%s': %s" % (filename, e.message)
                raise
            else:
                self._config_file = filename

        self.schema.validate(self._document)
        self.extra_validations(self._document)

    def extra_validations(self, xlm_tree):
        """
        Hook for ad-hoc validations of dependencies between parameters that
        are not explainable with the XSD schema.
        """
        pass

    def write(self, filename, output_format='XML'):
        """
        Write configuration to a text file in a specific data format.

        :param filename:
        :param output_format:
        :return:
        """
        if self._document is None:
            logger.error("No configuration loaded!")
            return

        output_format = output_format.upper()
        if output_format == 'XML':
            self._document.write(filename)
        elif output_format == 'YAML':
            logger.warning("YAML write is a TODO!")
        elif output_format == 'JSON':
            logger.warning("JSON write is a TODO!")
        else:
            raise ValueError("Accepted output_format are: 'XML'(default), 'YAML' and 'JSON'!")

    def read_string(self, text):
        self._document = ElementTree.fromstring(text)

    def get(self, qualified_name):
        section, _, item = qualified_name.partition(".")
        query = "./{0}/{1}".format(section, item)
        print(query)
        node = self._document.find(query)
        if node is None:
            return
        return node.text

    def __getitem__(self, section):
        query = "./{0}".format(section)
        parent = self._document.find(query)
        return dict((item.tag, item.text) for item in parent)

    def to_dict(self):
        return xmlschema.to_dict(self._document, self.schema)

    def to_json(self):
        """Converts the configuration to to json."""
        import json
        return json.dumps(self.to_dict(), sort_keys=True, indent=4)

    def to_yaml(self):
        """Converts the configuration to to json."""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False)

    # ElementTree API wrappers

    def iter(self, tag=None):
        return self._document.iter(tag)

    def find(self, path, namespaces=None):
        """
        Find first matching element by tag name or path.

        :param path: is a string having either an element tag or an XPath,
        :param namespaces: is an optional mapping from namespace prefix to full name.
        :return: the first matching element, or None if no element was found
        """
        namespaces = namespaces or {}
        namespaces.update(self.namespaces)
        return self._document.find(path, namespaces)

    def findall(self, path, namespaces=None):
        """
        Find all matching subelements by tag name or path.

        :param path: is a string having either an element tag or an XPath,
        :param namespaces: is an optional mapping from namespace prefix to full name.
        :return: the first matching element, or None if no element was found
        """
        namespaces = namespaces or {}
        namespaces.update(self.namespaces)
        return self._document.findall(path, namespaces)


class QeDocument(XmlDocument):
    """
    Abstract class for XML schema based configurations.
    """
    def __init__(self, xsd_file, input_builder):
        super(QeDocument, self).__init__(xsd_file)
        self.input_builder = input_builder

        self.default_namespace = self.schema.target_namespace

        try:
            if self.default_namespace != self.namespaces['qes']:
                raise ConfigError("Need a schema in 'qes' namespace!")
        except KeyError:
            try:
                if self.default_namespace != self.namespaces['neb']:
                    raise ConfigError("Need a schema in 'qes' or 'neb' namespace!")
            except KeyError:
                raise ConfigError("Need a schema in 'qes' of 'neb' namespace")

    def read_qe_input(self, filename):
        """
        Map from a Fortran input to XML old parameters to correspondent parameter in XML schema.

        :param filename:
        :return:
        """
        return self

    def write_qe_input(self, filename):
        """
        Write the XML configuration to a Fortran input.

        :param filename:
        :return:
        """
        with open(filename, mode='w+') as f:
            f.write(self.get_qe_input())

    def get_input_path(self):
        raise NotImplemented("This is an abstract implementation, use a subclass!")

    def get_qe_input(self, use_defaults=True):
        if self._document is None:
            raise ConfigError("Configuration not loaded!")

        qe_input = self.input_builder(xml_file=self._config_file)
        schema = self.schema
        input_path = self.get_input_path()
        input_root = self.find(input_path)

        # Extract values from input's subtree of the XML document
        for elem, path in etree_iter_path(input_root, path=input_path):
            rel_path = path.replace(input_path, '.')
            xsd_element = schema.find(path)
            # node_dict = etree_node_to_dict(elem, schema, root_path=path, use_defaults=use_defaults)
            node_dict = xsd_element.decode(elem, use_defaults=use_defaults)
            logger.debug("Add input for node '{0}' with dict '{1}'".format(elem.tag, node_dict))

            # Convert attributes
            for attr_name, value in elem.attrib.items():
                logger.debug("Convert attribute '%s' of element '%s'" % (attr_name, path))
                path_key = '%s/%s' % (rel_path, attr_name)
                if path_key not in qe_input:
                    logger.debug("Attribute's path '%s' not in converter!" % path_key)
                    continue
                qe_input.set_path(path_key, elem.tag, node_dict)

            logger.debug("Convert element '%s'" % path)
            path_key = '%s/_text' % rel_path if schema.get_attributes(path) else rel_path
            if path_key not in qe_input:
                logger.debug("Element's path '%s' not in converter!" % path_key)
                continue
            qe_input.set_path(path_key, elem.tag, node_dict)

        if use_defaults:
            # Add defaults for elements not included in input XML subtree
            for path in filter(
                    lambda x: x.startswith(input_path) and self.find(x) is None,
                    schema.elements
            ):
                rel_path = path.replace(input_path, '.')
                tag = rel_path.rsplit('/', 1)[-1]
                xsd_attributes = schema.get_attributes(path)
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

                default_value = schema.get_element_default(path)
                if default_value is not None:
                    path_key = '%s/_text' % rel_path if xsd_attributes else rel_path
                    xsd_type = schema.get_element_type(path)
                    value = xsd_type.decode(default_value)
                    defaults_dict[path_key.rsplit("/")[-1]] = value
                    defaults_path_keys.append(path_key)

                for path_key in defaults_path_keys:
                    qe_input.set_path(path_key, tag, defaults_dict)

        return qe_input.get_qe_input()

    def load_fortran_input(self, filename):
        if self._document is None:
            raise ConfigError("Configuration not loaded!")

        # fortran_input = self.input_builder()
        return None


class PwDocument(QeDocument):
    """
    Class to manage PW XML documents.
    """
    def __init__(self):
        self._input_tag = 'input'
        super(PwDocument, self).__init__(
            xsd_file='%s/scheme/qes.xsd' % os.path.dirname(os.path.abspath(__file__)),
            input_builder=PwInputConverter
        )

    def get_input_path(self):
        return './input'


class PhononDocument(QeDocument):
    """
    Class to manage Phonon XML documents.
    """
    def __init__(self):
        self._input_tag = 'input'
        super(PhononDocument, self).__init__(
            xsd_file='%s/scheme/ph_xmlschema.xsd' % os.path.dirname(os.path.abspath(__file__)),
            input_builder=PhononInputConverter
        )

    def get_input_path(self):
        return './inputPH'


class NebDocument(QeDocument):
    """
    Class to manage NEB XML documents.
    """
    def __init__(self):
        self._input_tag = 'input'
        super(NebDocument, self).__init__(
            xsd_file='%s/scheme/qes_neb_temp.xsd' % os.path.dirname(os.path.abspath(__file__)),
            input_builder=NebInputConverter
        )

    def get_input_path(self):
        return './input'
