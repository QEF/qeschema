# -*- coding: utf-8 -*-
#
# Copyright (C) 2001-2016 Quantum ESPRESSO group
# This file is distributed under the terms of the
# GNU General Public License. See the file `License'
# in the root directory of the present distribution,
# or http://www.gnu.org/copyleft/gpl.txt .
#
import logging
import os.path

from .converters import PwInputConverter, PhononInputConverter
from .exceptions import ConfigError
# from .namelist_reader import namelists_to_dict
from .xsdtypes import etree_node_to_dict, get_etree_node_path, XmlDocument
from .utils.logger import set_logger

logger = logging.getLogger('qespresso')


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
            raise ConfigError("Need a schema in 'qes' namespace!")

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

        qe_input = self.input_builder()
        schema = self.schema
        input_path = self.get_input_path()
        input_root = self.find(self.get_input_path())
        input_filter = lambda x: x.startswith(input_path) and self.find(x) is None

        # Extract values from input's subtree of the XML document
        for elem in input_root.iter():
            path = get_etree_node_path(elem)
            rel_path = path.replace(input_path, '.')
            node_dict = etree_node_to_dict(elem, schema, use_defaults=use_defaults)
            logger.debug("Add input for node '{0}' with dict '{1}'".format(elem.tag, node_dict))

            # Convert attributes
            for attr_name, value in elem.attrib.items():
                logger.debug("Convert attribute '%s' of element '%s'" % (attr_name, path))
                xsd_type = schema.get_attribute_type(attr_name, path)
                path_key = '%s/%s' % (rel_path, attr_name)
                if path_key not in qe_input:
                    logger.debug("Attribute's path '%s' not in converter!" % path_key)
                    continue

                qe_input.set_path(path_key, xsd_type.decode(value))

            logger.debug("Convert element '%s'" % path)
            path_key = '%s/_text' % rel_path if elem.attrib else rel_path
            if path_key not in qe_input:
                logger.debug("Element's path '%s' not in converter!" % path_key)
                continue

            value = node_dict[elem.tag]['_text'] if elem.attrib else node_dict[elem.tag]
            if value is None:
                logger.debug("Skip element '%s': None value!" % path)
                continue
            qe_input.set_path(path_key, value)

        if use_defaults:
            # Add defaults for elements not included in input XML subtree
            for path in filter(input_filter, schema.elements):
                rel_path = path.replace(input_path, '.')
                xsd_attributes = schema.get_attributes(path)
                try:
                    # Add default value for attributes
                    for attr_name, xsd_attribute in xsd_attributes.items():
                        default_value = xsd_attribute.get_default()
                        if default_value is not None:
                            path_key = '%s/%s' % (rel_path, attr_name)
                            xsd_type = xsd_attribute.xsd_type
                            value = xsd_type.decode(default_value)
                            qe_input.set_path(path_key, value)

                except AttributeError:
                    pass

                default_value = schema.get_element_default(path)
                if default_value is not None:
                    path_key = '%s/_text' % rel_path if xsd_attributes else rel_path
                    xsd_type = schema.get_element_type(path)
                    value = xsd_type.decode(default_value)
                    qe_input.set_path(path_key, value)

        return qe_input.get_qe_input()

    def load_fortran_input(self, filename):
        if self._document is not None:
            raise ConfigError("Configuration not loaded!")

        fortran_input = self.input_builder()
        return None
        # return namelists_to_dict(filename)


class PwDocument(QeDocument):
    """
    Class to manage PW XML documents.
    """
    def __init__(self):
        self._input_tag = 'input'
        super(PwDocument, self).__init__(
            xsd_file='%s/schema/qes.xsd' % os.path.dirname(os.path.abspath(__file__)),
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
            xsd_file='%s/schema/ph_xmlschema.xsd' % os.path.dirname(os.path.abspath(__file__)),
            input_builder=PhononInputConverter
        )

    def get_input_path(self):
        return './inputPH'
