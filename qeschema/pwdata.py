# -*- coding: utf-8 -*-
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# Authors: Pietro Delugas, Davide Brunato
#



from .documents  import PwDocument


def get_atomic_positions(datafile, schema=None):
    """
    Gets atomic symbols and atomic positions from an XML datafile


    :param datafile: path to the xml file
    :param schema: optional path to the schema file
    :return: the list of atomic symbols and a nested list containing the
    coordinates
    """
    doc= PwDocument(schema=schema)
    validation = 'strict'
    if schema is None: validation = 'lax'
    doc.read(datafile, validation = validation)
    path = './/output//atomic_positions'
    atpos = doc.schema.find(path).decode(doc.find(path))
    atoms = atpos.get('atom')
    if not type(atoms)  is list:  atoms = [atoms]
    symbols = [a['@name'] for a in atoms ]
    positions = [a['$'] for a in  atoms ]
    return  symbols, positions


def get_cell_parameters(datafile,  schema=None):
    """
    gets cell parameters from an XML datafile
    
    :param datafile: path to the xml file 
    :param schema:  optional path to the schema file, default one is used if
                      not provided
    :return: a nested list containing the cell vectors in Bohr atomic units
    """
    doc =PwDocument(schema=schema) 
    validation = 'strict'
    if schema is None: validation = 'lax' 
    doc.read(datafile, validation=validation)
    path = './/output//cell' 
    cell = doc.schema.find(path).decode(doc.find(path)) 
    return [cell['a1'],cell['a2'], cell['a3']]  


def get_stress(datafile, schema=None):
    """
    gets stress tensor from the XML file, if present
    
    :param datafile: path to the xml file
    :param schema: optional path to schema file
    :return:  nested list contaning the stress tensor in C order 
    """
    doc = PwDocument(schema=schema)
    validation = 'strict'
    if schema is None: validation = 'lax'
    doc.read(datafile, validation=validation)
    path = './/output//stress'
    if doc.find(path) is None:
        return None
    stress = doc.schema.find(path).decode(doc.find(path))['$']
    return  [stress[::3],stress[1::3],stress[2::3]]


def get_forces(datafile, schema=None):
    """
    gets forces from the XML file if present
    
    :param datafile: path to the XML file
    :param schema: optional path to schema file
    :return: the list of atomic symbols plus a nested list with the forces in 
    atomic units
    """
    doc = PwDocument(schema=schema)
    validation = 'strict'
    if schema is None: validation = 'lax'
    doc.read(datafile, validation=validation)
    path = './/output/forces'
    if doc.find(path) is None:
        return None
    forces =  doc.schema.find(path).decode(doc.find(path))
    path = './/output//atomic_positions'
    atpos = doc.schema.find(path).decode(doc.find(path))
    atoms = atpos.get('atom',[])
    if not type(atoms)  is list: atoms=[atoms]
    symbols = [a['@name'] for a in atoms]
    i0 = range(3*len(atoms))[::3]
    i1 = range(3*len(atoms)+1)[3::3]
    forces=[ forces['$'][i:j] for i,j in zip(i0,i1)]
    return symbols, forces


def get_k_points(datafile, schema=None):
    """
    extracts the k_points list from the XML file
    
    :param datafile: path to the XML datafile
    :param schema:   optional, path to the XML file
    :return: nested list with k_points  
    """
    doc = PwDocument(schema=schema)
    validation = 'strict'
    if schema is None: validation = 'lax'
    doc.read(datafile, validation=validation)
    path = './/output//k_point'
    return [doc.schema.find(path).decode(e)['$'] for e in doc.findall(path)]


def  get_KS_eigenvalues(datafile, schema=None):
    """
    extracts the eigenvalues from the XML file
    
    :param datafile: path to the XML datafile
    :param schema: optional, path to the XML file
    :return: nested list of KS eigenvalues for each k_point in Hartree Units 
    """
    doc = PwDocument(schema=schema)
    validation = 'strict' 
    if schema is None: validation= 'lax'
    doc.read(datafile, validation=validation)
    path = './/output//ks_energies/eigenvalues'
    return [doc.schema.find(path).decode(e)['$'] for e in doc.findall(path)] 

def get_total_energy(datafile, schema=None):
    """
    extracts the total energy from the  XML file
    
    :param datafile: path to the XML datafile
    :param schema: optional, path to the XML file
    :return: total energy  in Hartree Units 
    """
    doc = PwDocument(schema=schema)
    validation = 'strict' 
    if schema is None: validation= 'lax'
    doc.read(datafile, validation=validation)
    path = './/output//etot' 
    return doc.schema.find(path).decode(doc.find(path)) 
