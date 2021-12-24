#
# Copyright (c), 2021, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
"""
A collection of functions for reading different files and quantities.
"""
import numpy as np
from xml.etree import ElementTree

__all__ = ['read_pseudo_file']


def read_pseudo_file(xml_file):
    """
    Reads a pseudo-potential XML-like file in the QE UPF format (text), returning
    the content of each tag in a dictionary. The file is read in strings and
    completed with a root UPF tag when it lacks, to avoids an XML syntax error.

    TODO: add support for UPF-schema files
    """
    def iter_upf_file():
        """
        Creates an iterator over the lines of an UPF file,
        inserting the root <UPF> tag when missing.
        """
        with open(xml_file, 'r') as f:
            fake_root = None
            for line in f:
                if fake_root is not None:
                    line = line.replace('&input', '&amp;input')
                    line = line.replace('&inputp', '&amp;inputp')
                    yield line
                else:
                    line = line.strip()
                    if line.startswith("<UPF") and line[4] in ('>', ' '):
                        yield line
                        fake_root = False
                    elif line:
                        yield "<UPF>"
                        yield line
                        fake_root = True
        if fake_root is True:
            yield "</UPF>"

    pseudo = {}
    psroot = ElementTree.fromstringlist(list(iter_upf_file()))

    # PP_INFO
    try:
        pp_info = psroot.find('PP_INFO').text
    except AttributeError:
        pp_info = ""
    try:
        pp_input = psroot.find('PP_INFO/PP_INPUTFILE').text
    except AttributeError:
        pp_input = ""
    pseudo.update(PP_INFO=dict(INFO=pp_info, PP_INPUT=pp_input))

    # PP_HEADER
    pseudo.update(PP_HEADER=dict(psroot.find('PP_HEADER').attrib))

    # PP_MESH
    pp_mesh = dict(psroot.find('PP_MESH').attrib)
    pp_r = np.array([float(x) for x in psroot.find('PP_MESH/PP_R').text.split()])
    pp_rab = np.array([float(x) for x in psroot.find('PP_MESH/PP_RAB').text.split()])
    pp_mesh.update(PP_R=pp_r, PP_RAB=pp_rab)
    pseudo.update(PP_MESH=pp_mesh)

    # PP_LOCAL
    node = psroot.find('PP_LOCAL')
    if node is not None:
        pp_local = np.array([x for x in map(float, node.text.split())])
    else:
        pp_local = None
    pseudo.update(PP_LOCAL=pp_local)

    # PP_RHOATOM
    node = psroot.find('PP_RHOATOM')
    if node is not None:
        pp_rhoatom = np.array([v for v in map(float, node.text.split())])
    else:
        pp_rhoatom = None
    pseudo.update(PP_RHOATOM=pp_rhoatom)

    # PP_NONLOCAL
    node = psroot.find('PP_NONLOCAL')
    if node is not None:
        betas = list()
        dij = None
        pp_aug = None
        pp_q = None
        for el in node:
            if 'PP_BETA' in el.tag:
                beta = dict(el.attrib)
                val = np.array(x for x in map(float, el.text.split()))
                beta.update(beta=val)
                betas.append(beta)
            elif 'PP_DIJ' in el.tag:
                text = '\n'.join(el.text.strip().split('\n')[1:])
                dij = np.array([x for x in map(float, text.split())])
            elif 'PP_AUGMENTATION' in el.tag:
                pp_aug = dict(el.attrib)
                pp_qijl = list()
                pp_qij = list()
                for q in el:
                    if 'PP_QIJL' in q.tag:
                        qijl = dict(q.attrib)
                        val = np.array(x for x in map(float, q.text.split()))
                        qijl.update(qijl=val)
                        pp_qijl.append(qijl)
                    elif 'PP_QIJ' in q.tag:
                        qij = dict(q.attrib)
                        val = np.array(x for x in map(float, q.text.split()))
                        qij.update(qij=val)
                        pp_qij.append(qij)
                    elif q.tag == 'PP_Q':
                        pp_q = np.array(x for x in map(float, q.text.split()))
                pp_aug.update(PP_QIJL=pp_qijl, PP_QIJ=pp_qij, PP_Q=pp_q)
        pp_nonlocal = dict(PP_BETA=betas, PP_DIJ=dij, PP_AUGMENTATION=pp_aug)
    else:
        pp_nonlocal = None

    pseudo.update(PP_NONLOCAL=pp_nonlocal)
    return pseudo
