#!/usr/bin/env python
#
# Copyright (c), 2015-2020, Quantum Espresso Foundation and SISSA (Scuola
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

    if sys.version_info < (3, 5, 0):
        sys.stderr.write("You need python 3.5 or later to run this program\n")
        sys.exit(1)

    args = parse_args()
    print("Create Fortran input from YAML file %r ...\n" % getattr(args, 'in'))

    if __package__ is None:
        from os import path
        sys.path.append(path.abspath(path.dirname(__file__)+'/../'))

    import qeschema
    import os
    import yaml

    qeschema.set_logger(args.verbosity)

    input_fn = getattr(args, 'in')

    with open(input_fn) as f:
        data = yaml.load(f, Loader=yaml.Loader)

    for key in data:
        element_name = key.split('}')[-1]
        if element_name == 'espresso':
            xml_document = qeschema.PwDocument()
        elif element_name == 'nebRun':
            xml_document = qeschema.NebDocument()
        elif element_name == 'espressoph':
            xml_document = qeschema.PhononDocument()
        elif element_name == 'tddfpt':
            xml_document = qeschema.TdDocument()
        elif element_name == 'spectrumDoc':
            xml_document = qeschema.TdSpectrumDocument()
        else:
            continue
        break
    else:
        sys.stderr.write("Could not find correct document root in %r, exiting...\n" % input_fn)
        sys.exit(1)

    xml_document.read(input_fn)
    qe_in = xml_document.get_fortran_input()

    input_fn_name, input_fn_ext = os.path.splitext(input_fn)
    outfile = input_fn_name + '.in'

    with open(outfile, mode='w') as f:
        f.write(qe_in)
        print("Input configuration written to file '%s' ..." % outfile)
