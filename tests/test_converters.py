#!/usr/bin/env python3
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato
#
"""
Test classes for Quantum Espresso input converters.
"""
import unittest
import os
import glob
import platform
import xml.etree.ElementTree as ElementTree

try:
    import yaml
except ImportError:
    yaml = None

import qeschema


def make_test_function(xml_file, ref_in_file):
    def test(self):
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()

        element_name = root.tag.split('}')[-1]

        if element_name == 'espresso':
            xml_conf = qeschema.PwDocument(source=xml_file)
        elif element_name == 'nebRun':
            xml_conf = qeschema.NebDocument(source=xml_file)
        elif element_name == 'espressoph':
            xml_conf = qeschema.PhononDocument(source=xml_file)
        elif element_name == 'tddfpt':
            xml_conf = qeschema.TdDocument(source=xml_file)
        elif element_name == 'spectrumDoc':
            xml_conf = qeschema.TdSpectrumDocument(source=xml_file)
        elif element_name == 'xspectra':
            xml_conf = qeschema.XSpectraDocument(source=xml_file)
        else:
            raise ValueError("XML file %r is not a Quantum ESPRESSO document!" % xml_file)

        xml_conf.read(xml_file)
        qe_input = xml_conf.get_fortran_input().split('\n')
        with open(ref_in_file, 'r') as qe_input_file:
            k = 0
            are_equals = True
            for ref_line in qe_input_file:
                ref_line = ref_line.rstrip('\n').strip(' \t')
                in_line = qe_input[k].strip(' \t')
                if ref_line != in_line:
                    print("Unmatched lines: '%s' != '%s'" % (in_line, ref_line))
                    are_equals = False
                    break
                else:
                    k += 1
        self.assertTrue(are_equals, xml_file)
    return test


class ConverterTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.pkg_folder = os.path.dirname(cls.test_dir)

    def test_xml2qeinput_script(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.xml')
        in_filename = xml_filename[:-4] + '.in'
        py_filename = os.path.join(self.pkg_folder, 'scripts/xml2qeinput.py')
        if os.path.isfile(in_filename):
            os.remove(in_filename)

        if platform.system() == 'Windows':
            os.system("python %s -in %s" % (py_filename, xml_filename))
            self.assertTrue('Al001_relax_bfgs.in' in os.listdir(os.path.dirname(xml_filename)))
        else:
            if platform.system() == 'Linux':
                command = 'python %s -in %s 1> /dev/null 2> /dev/null'
            else:
                command = 'python3 %s -in %s 1> /dev/null 2> /dev/null'

            os.system(command % (py_filename, xml_filename))
            self.assertTrue(os.path.isfile(in_filename),
                            'Test output file %r missing!' % in_filename)

    @unittest.skipIf(yaml is None, "PyYAML library is not installed")
    def test_yaml2qeinput_script(self):
        xml_filename = os.path.join(self.test_dir, 'resources/pw/Al001_relax_bfgs.yml')
        in_filename = xml_filename[:-4] + '.in'
        py_filename = os.path.join(self.pkg_folder, 'scripts/yaml2qeinput.py')
        if os.path.isfile(in_filename):
            os.remove(in_filename)

        if platform.system() == 'Windows':
            os.system("python %s -in %s" % (py_filename, xml_filename))
            self.assertTrue('Al001_relax_bfgs.in' in os.listdir(os.path.dirname(xml_filename)))
        else:
            if platform.system() == 'Linux':
                command = 'python %s -in %s 1> /dev/null 2> /dev/null'
            else:
                command = 'python3 %s -in %s 1> /dev/null 2> /dev/null'

            os.system(command % (py_filename, xml_filename))
            self.assertTrue(os.path.isfile(in_filename),
                            'Test output file %r missing!' % in_filename)


##
# Create test classes for examples
#
test_dir = os.path.dirname(os.path.abspath(__file__))

for filename in glob.glob(os.path.join(test_dir, "resources/*/*.xml")):
    qe_input_filename = '%s.in.test' % filename[:-4]
    if not os.path.isfile(qe_input_filename):
        continue

    test_func = make_test_function(filename, qe_input_filename)
    test_name = os.path.relpath(filename)
    klassname = 'Test_{0}'.format(test_name.replace('/', '__'))
    globals()[klassname] = type(
        klassname, (unittest.TestCase,),
        {'test_converter_{0}'.format(test_name): test_func, 'longMessage': True}
    )


if __name__ == '__main__':
    unittest.main()
