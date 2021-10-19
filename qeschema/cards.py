#
# Copyright (c), 2015-2020, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# Authors: Davide Brunato, Giovanni Borghi
#
"""
Conversion functions for Quantum Espresso cards.
"""
import logging
from typing import Union, List

logger = logging.getLogger('qeschema')


#
# Functions for QE cards
#
def get_atomic_species_card(name, **kwargs):
    """
    Convert XML data to ATOMIC_SPECIES card

    :param name: Card name
    :param kwargs: Dictionary with converted data from XML file
    :return: List of strings
    """
    try:
        atomic_species = kwargs['atomic_species']
        species = atomic_species['species']
    except KeyError as err:
        logger.error("Missing required arguments when building ATOMIC_SPECIES card! %s" % err)
        return []

    lines = [name]
    try:
        lines.append(
            ' {0} {1} {2}'.format(species['@name'], species['mass'], species['pseudo_file'])
        )
    except TypeError:
        for specie in species:
            lines.append(
                ' {0} {1} {2}'.format(specie['@name'], specie['mass'], specie['pseudo_file'])
            )
    return lines


def get_positions_units(item):
    """
    Read different type of positions and return them together with units.

    :param item: Data item
    :return: Atomic positions dict and unit, empty dict and None if not found
    """

    ptypes = ('atomic_positions', 'crystal_positions', 'wyckoff_positions')
    units = ('bohr', 'crystal', 'crystal_sg')
    for ptype, unit in zip(ptypes, units):
        if ptype in item:
            return item[ptype], unit

    return {}, None


def get_atomic_positions_cell_card(name, **kwargs):
    """
    Convert XML data to ATOMIC_POSITIONS card

    :param name: Card name
    :param kwargs: Dictionary with converted data from XML file
    :return: List of strings
    """
    try:
        atomic_structure = kwargs['atomic_structure']
    except KeyError:
        logger.error("Missing required arguments when building ATOMIC_POSITIONS card!")
        return []

    # Find atoms
    positions, units = get_positions_units(atomic_structure)
    try:
        atoms = positions['atom']
    except KeyError:
        logger.error("Cannot find any atoms for building ATOMIC_POSITIONS!")
        return []

    if not isinstance(atoms, list):
        atoms = [atoms]

    # Check atoms with position constraints
    free_positions = kwargs.get('free_positions')
    if free_positions:
        free_positions = free_positions.get('$', [])

    if free_positions and len(free_positions) != 3 * len(atoms):
        logger.error("ATOMIC_POSITIONS: incorrect number of position constraints!")

    # Add atomic positions
    lines = ['%s %s' % (name, units)]
    for k in range(len(atoms)):
        try:
            line = '{:4}'.format(atoms[k].get('@name'))
            line += ' {:12.8f}  {:12.8f}  {:12.8f}'.format(*atoms[k].get('$'))
        except (ValueError, TypeError):
            logger.error("ATOMIC_POSITIONS: incorrect datatype in positions!")
            continue

        if free_positions:
            try:
                if free_positions[3 * k] + \
                        free_positions[3 * k + 1] + \
                        free_positions[3 * k + 2] != 3:
                    line += ' {:4d}{:4d}{:4d}'.format(*map(int, free_positions[3 * k:3 * k + 3]))
            except IndexError:
                pass

        lines.append(line)

    return lines


def get_atomic_constraints_card(name, **kwargs):
    """
    Convert XML data to CONSTRAINTS card

    :param name: Card name
    :param kwargs: Dictionary with converted data from XML file
    :return: List of strings
    """
    try:
        num_of_constraints = kwargs['num_of_constraints']
        tolerance = kwargs['tolerance']
        atomic_constraints = kwargs['atomic_constraints']
    except KeyError:
        logger.error("Missing required arguments when building CONSTRAINTS card!")
        return []

    lines = [name, '{0} {1}'.format(num_of_constraints, tolerance)]
    for constraint in atomic_constraints:
        constr_parms = constraint['constr_parms']  # list with 4 float items
        constr_parms.extend([0] * max(0, 4 - len(constr_parms)))
        constr_type = constraint['constr_type']  # string
        constr_target = constraint['constr_target']  # float
        lines.append('{0} {1} {2}'.format(
            constr_type,
            ' '.join([str(item) for item in constr_parms]),
            constr_target
        ))
    return lines


def get_k_points_card(name, **kwargs):
    """
    Convert XML data to K_POINTS card

    :param name: Card name
    :param kwargs: Dictionary with converted data from XML file
    :return: List of strings
    """
    k_point = {}  # type: Union[dict, List[dict]]
    nk = monkhorst_pack = None
    gamma_only = kwargs.get('gamma_only', False)
    try:
        if not gamma_only:
            k_points_ibz = kwargs['k_points_IBZ']
            monkhorst_pack = k_points_ibz.get('monkhorst_pack', {})
            if monkhorst_pack:
                k_attrib = 'automatic'
            else:
                k_attrib = None
                k_point = k_points_ibz['k_point']
                nk = k_points_ibz['nk']
        else:
            k_attrib = 'gamma'

    except KeyError as err:
        logger.error("Missing required arguments when building K_POINTS card! %s" % err)
        return []
    else:
        if not isinstance(k_point, list):
            k_point = [k_point]

    lines = [name] if k_attrib is None else ['%s %s' % (name, k_attrib)]
    if k_attrib is None:
        lines.append(' {}'.format(nk))
        for point in k_point:
            lines.append(' {0} {1}'.format(
                ' '.join([str(value) for value in point['$']]), point['@weight'])
            )
    elif k_attrib == 'automatic':
        lines.append(' %(@nk1)s %(@nk2)s %(@nk3)s %(@k1)s %(@k2)s %(@k3)s' % monkhorst_pack)

    return lines


def get_atomic_forces_card(name, **kwargs):
    """
    Convert XML data to ATOMIC_FORCES card

    :param name: Card name
    :param kwargs: Dictionary with converted data from XML file
    :return: List of strings
    """
    try:
        external_atomic_forces = kwargs['external_atomic_forces']
    except KeyError:
        logger.debug("Missing required arguments when building ATOMIC_FORCES card!")
        return []

    # Warning if number of atoms in atomic positions differ with forces
    atomic_positions = kwargs.get('atomic_positions', {})
    atoms = atomic_positions.get('atom', [])
    if atoms and len(atoms) != len(external_atomic_forces) / 3:
        logger.error("incorrect number of atomic forces")

    # Build input card text lines
    lines = [name]
    f = external_atomic_forces
    for at in atoms:
        try:
            line = '{:<3s}  {:14.8f} {:14.8f} {:14.8f}'.format(at["@name"], f[0], f[1], f[2])
        except IndexError:
            pass
        else:
            lines.append(line)
            f = f[3:]
    return lines


def get_cell_parameters_card(name, **kwargs):
    """
    Convert XML data to CELL_PARAMETERS card

    :param name: Card name
    :param kwargs: Dictionary with converted data from XML file
    :return: List of strings
    """
    try:
        atomic_structure = kwargs['atomic_structure']
    except KeyError:
        logger.error("Missing required arguments when building CELL_PARAMETERS card!")
        return []
    # Add cell parameters card
    cells = atomic_structure.get('cell', {})
    if cells:
        lines = ['%s bohr' % name]
        for key in sorted(cells):
            if key not in ['a1', 'a2', 'a3']:
                continue
            lines.append((3 * '{:12.8f} ').format(*cells[key]))
        return lines
    return []


#
# Phonon Cards
#
def get_qpoints_card(name, **kwargs):
    assert isinstance(name, str)
    try:
        ldisp = kwargs['ldisp']
    except KeyError:
        ldisp = False
    else:
        if ldisp:
            return []

    qplot = kwargs.get('qplot', False)
    if not qplot and not ldisp:
        try:
            xq = kwargs['xq']
        except KeyError:
            xq = [0.e0, 0.e0, 0.e0]
        line = "{:6.4f}  {:8.4f}  {:8.4f}".format(xq[0], xq[1], xq[2])
        return [line]

    lines = []
    try:
        nqs = kwargs['nqs']
    except KeyError:
        nqs = 1
        logger.warning("qplot was set to true in input but no value "
                       "for nqs was provided: assuming nqs=1")

    lines.append('{:4d}'.format(nqs))
    q_points_list = kwargs['q_points_list']['q_point']
    for q_point in q_points_list:
        vector = ' '.join([str(coord) for coord in q_point['$']])
        lines.append(' %s %s' % (vector, q_point['@weight']))
    return lines


def get_nat_todo_card(name, **kwargs):
    assert kwargs['nat_todo']['@natom'] == len(kwargs['nat_todo']['atom'])

    return [' '.join(map(str, kwargs['nat_todo']['atom']))]


def get_climbing_images(name, **kwargs):
    assert isinstance(name, str)
    try:
        manual_images = kwargs['climbingImage'] == 'manual' or kwargs['climbingImage'] == 'MANUAL'
    except KeyError:
        manual_images = False

    if not manual_images:
        return ['']

    if isinstance(kwargs['climbingImageIndex'], list):
        line = [int(x) for x in kwargs['climbingImageIndex']]
        fmt = len(line) * ' %d, '
        line = fmt % tuple(line)
    else:
        line = ' %d ' % int(kwargs['climbingImageIndex'])
    return [line]


def get_neb_images_positions_card(name, **kwargs):
    """
    Extract atomic positions for each image provided in engine with an atomic_structure element

    :param name: Card name
    :param kwargs: List of dictionaries each containing an atomic_structure element.
    :return: List of lines
    """
    assert isinstance(name, str)
    images = kwargs.get('atomic_structure', [])
    try:
        assert isinstance(images, list)
    except AssertionError:
        images = [images]

    if len(images) < 2:
        logger.error("at least the atomic structures for first and last image should be provided")
        return []

    free_positions = kwargs.get('free_positions', None)
    if free_positions:
        free_positions = free_positions.get('$')
    else:
        free_positions = []

    first_nat = 0
    lines = ['BEGIN_POSITIONS ', 'FIRST_IMAGE ']

    for pos, item in enumerate(images):
        positions, units = get_positions_units(item)
        atoms = positions.get('atom', [])

        if pos == 0:
            first_nat = len(atoms)
            if first_nat <= 0:
                logger.error("no atomic coordinates provided for first image")
                return ''
            if first_nat != int(item.get('@nat', 0)):
                logger.error("nat provided in first image differs from number "
                             "of atoms in atomic_positions!!!")
                return ''
            if free_positions and len(free_positions) != 3 * first_nat:
                logger.error("ATOMIC_POSITIONS: incorrect number of position constraints!")
                return ''
        else:
            if len(atoms) != first_nat:
                logger.error('found images with differing number of atoms !!!')
                return ''

            if pos < len(images) - 1:
                lines.append('INTERMEDIATE_IMAGE ')
            else:
                lines.append('LAST_IMAGE ')

        lines.append('ATOMIC_POSITIONS { %s }' % units)

        # reshape to 3x3
        free_positions_sq = [free_positions[i:i + 3]
                             for i in range(0, len(free_positions), 3)]

        for k, atom in enumerate(atoms):
            sp_name = '{:4}'.format(atom['@name'])
            coords = '{:12.8f}  {:12.8f}  {:12.8f}'.format(*atom['$'])

            if free_positions_sq and sum(free_positions_sq[k]) < 3:
                free_pos = '{:4d}{:4d}{:4d}'.format(*free_positions_sq[k])
                lines.append('%s %s %s' % (sp_name, coords, free_pos))
            else:
                lines.append('%s %s' % (sp_name, coords))

    lines.append('END_POSITIONS ')
    return lines


def get_neb_cell_parameters_card(name, **kwargs):
    """
    Extract cell parameter from the first of the atomic_structure elements provided in engine

    :param name: card name
    :param kwargs: list of the atomic_structure dictionaries translate for xml element engine
    :return: list of text lines for the cell parameters card
    """
    assert isinstance(name, str)
    images = kwargs.get('atomic_structure', [])
    if not isinstance(images, list):
        images = [images]

    if len(images) < 1:
        logger.error(" No atomic_structure element found in kwargs !!!")
        return []

    atomic_structure = images[0]
    cells = atomic_structure.get('cell', {})
    if cells:
        lines = ['%s bohr' % name]
        for key in sorted(cells):
            if key not in ['a1', 'a2', 'a3']:
                continue
            lines.append((3 * '{:12.8f}').format(*cells[key]))
        return lines
    return []


def get_neb_atomic_forces_card(name, **kwargs):
    # TODO
    assert isinstance(name, str)
    assert isinstance(kwargs, dict)
