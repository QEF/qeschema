#!/usr/bin/env python
#
# Copyright (c), 2015-2016, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato, Giovanni Borghi
#
"""
Convert from XML input to Fortran input
"""
import sys


def parse_args():
    """Command arguments parsing"""
    import argparse

    parser = argparse.ArgumentParser(
            description="This program converts a YAML formatted input to the an equivalent "
                        "input file written in a format that is natively readable "
                        "by Fortran's codes of Quantum Espresso"
    )
    parser.add_argument("-v", "--verbosity", action="count", default=1,
                        help="Increase output verbosity.")
    parser.add_argument('-in', metavar='FILE', required=True, help="YAML input filename.")
    return parser.parse_args()


if __name__ == '__main__':

    # Python 2.7+ is required. For old versions 'argparse' is available
    # only with extra package: https://pypi.python.org/pypi/argparse.
    if sys.version_info < (2, 7, 0):
        sys.stderr.write("You need python 2.7 or later to run this program\n")
        sys.exit(1)

    args = parse_args()
    print("Create Fortran input from YAML file %r ...\n" % getattr(args, 'in'))

    if __package__ is None:
        from os import path
        sys.path.append(path.abspath(path.dirname(__file__)+'/../'))

    import qeschema
    import xmlschema
    import os
    import xml.etree.ElementTree as Etree
    import yaml

    qeschema.set_logger(args.verbosity)

    print(args)
    input_fn = getattr(args, 'in')

    with open(input_fn) as f:
        data = yaml.load(f, Loader=yaml.Loader)
    print(data)

    print()
    breakpoint()
    tree = xmlschema.parse(input_fn)
    root = tree.getroot()
    elementName = root.tag.split('}')[-1]
    if elementName == 'espresso':
        tree
        xml_conf = qeschema.PwDocument()
    elif elementName == 'nebRun':
        xml_conf = qeschema.NebDocument()
    elif elementName == 'espressoph':
        xml_conf = qeschema.PhononDocument()
    elif elementName == 'tddfpt':
        xml_conf = qeschema.TdDocument()
    elif elementName == 'spectrumDoc':
        xml_conf = qeschema.TdSpectrumDocument()
    else:
        sys.stderr.write("Could not find correct XML in %s, exiting...\n" % input_fn)
        sys.exit(1)

    root = None
    tree = None

    xml_conf.read(input_fn)
    qe_in = xml_conf.get_fortran_input()

    input_fn_name, input_fn_ext = os.path.splitext(input_fn)
    outfile = input_fn_name + '.in'

    breakpoint()

    with open(outfile, mode='w') as f:
        f.write(qe_in)
        print("Input configuration written to file '%s' ..." % outfile)
