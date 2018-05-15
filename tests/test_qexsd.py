#!/usr/bin/env python3
#
# Copyright (c), 2015-2016, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato, Giovanni Borghi
#
"""
Test classes for Quantum Espresso input converters.
"""
import os
import unittest
import xml.etree.ElementTree as ElementTree

def make_test_function(xml_file, ref_in_file):
    def test(self):
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
        elementName = root.tag.split('}')[-1]
        if elementName == 'espresso':
            xml_conf = qexsd.PwDocument()
        elif elementName == 'nebRun':
            xml_conf = qexsd.NebDocument()
        elif elementName == 'espressoph':
            xml_conf = qexsd.PhononDocument()
        else:
            raise ValueError("XML file %r is not a Quantum ESPRESSO document!" % xml_file)

        xml_conf.read(xml_file)
        qe_input = xml_conf.get_qe_input().split('\n')
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


    @unittest.expectedFailure 
    def test_conversion_script(self):
        xml_filename = os.path.join(self.test_dir, 'examples/pw/Al001_relax_bfgs.xml')
        in_filename = xml_filename[:-4] + '.in'
        conversion_script = os.path.join(self.pkg_folder, 'scripts/xml2qeinput.py')
        if os.path.isfile(in_filename):
            os.system('rm -f %s' % in_filename)
        os.system('%s -in %s &>/dev/null' % (conversion_script, xml_filename))
        self.assertTrue(os.path.isfile(in_filename), 'Test file %r missing!' % in_filename)


if __name__ == '__main__':
    import glob
    import sys

    test_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_folder = os.path.dirname(test_dir)

    try:
        import qexsd
    except ImportError:
        sys.path.insert(0, pkg_folder)
        import qexsd

    header = "Test %r" % qexsd
    print("*" * len(header) + '\n' + header + '\n' + "*" * len(header))

    test_files = glob.glob(os.path.join(test_dir, "examples/*/*.xml"))

    for xml_filename in test_files:
        qe_input_filename = '%s.in.test' % xml_filename[:-4]
        if not os.path.isfile(qe_input_filename):
            continue
        test_func = make_test_function(xml_filename, qe_input_filename)
        test_name = os.path.relpath(xml_filename)
        klassname = 'Test_{0}'.format(test_name)
        globals()[klassname] = type(
            klassname, (unittest.TestCase,),
            {'test_converter_{0}'.format(test_name): test_func, 'longMessage': True}
        )
    unittest.main()
