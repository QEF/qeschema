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
Conversion functions for Quantum Espresso input options.
"""
import logging

from .exceptions import XmlDocumentError
from .utils import to_fortran

logger = logging.getLogger('qeschema')


#
# Other derived values
def get_specie_related_values(name, **kwargs):
    """
    Convert XML data for specie related options. Map single values,
    vectors and matrices. Skip 0 values for Hubbard parameters or
    negative values for starting_ns eigenvalues. Skip entire vector
    or matrix when

    :param name: parameter name
    :param kwargs: related input data
    :return: a list
    """
    related_tag = kwargs['_related_tag']
    related_data = kwargs[related_tag]
    try:
        atomic_species = kwargs['atomic_species']
        species = atomic_species['species']
    except KeyError as err:
        logger.error("Missing required argument %s when building "
                     "parameter %r", str(err), name)
        return []

    lines = []
    for value in iter(related_data if isinstance(related_data, list) else [related_data]):
        tag_specie = value['@specie']
        tag_values = value['$']
        tag_spin = value.get('@spin')
        if value.get('@label') == 'no Hubbard':
            continue

        specie_index = 1
        for specie in species:
            if specie['@name'] == tag_specie:
                break
            specie_index += 1
        else:
            raise XmlDocumentError("Unknown specie {!r} in tag {!r}".format(tag_specie, name))

        if isinstance(tag_values, list):
            for k in range(len(tag_values)):
                # starting_ns case: skip negative values
                if tag_values[k] < 0 or (name == 'Hubbard_J' and tag_values[k] == 0):
                    continue
                if tag_spin:
                    lines.append(' {0}({1},{2},{3})={4}'.format(
                        name, k + 1, tag_spin, specie_index, tag_values[k]
                    ))
                else:
                    lines.append(' {0}({1},{2})={3}'.format(
                        name, k + 1, specie_index, tag_values[k]
                    ))
        elif tag_values > 0:
            lines.append(' {0}({1})={2}'.format(name, specie_index, tag_values))
    return lines


def get_starting_magnetization(name, **kwargs):
    """
    Build starting magnetization vector from species data.
    """
    try:
        atomic_species = kwargs['atomic_species']
        species = atomic_species['species']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []

    lines = []
    try:
        lines.append(' {0}(1)={1}'.format(name, species.get('starting_magnetization', 0.0)))
    except AttributeError:
        k = 0
        for specie in species:
            k += 1
            lines.append(' {0}({1})={2}'.format(
                name, k, specie.get('starting_magnetization', 0.0)
            ))
    return lines


def get_system_nspin(name, **kwargs):
    """
    Get the value for 'nspin' parameter of the SYSTEM namelist.
    """
    try:
        lsda = kwargs['lsda']
        if lsda:
            return [' nspin=2']

        noncolin = kwargs['noncolin']
        if noncolin:
            return [' nspin=4']
        else:
            return [' nspin=1']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []


def set_ibrav_to_zero(name, **_kwargs):
    assert isinstance(name, str)
    line = ' ibrav=0'
    return [line]


def get_system_eamp(name, **kwargs):
    try:
        electric_potential = kwargs['electric_potential']
        if electric_potential in ('Berry_Phase', 'homogenous_field'):
            return []
        electric_field_amplitude = kwargs['electric_field_amplitude']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []

    if electric_potential == 'sawtooth_potential':
        return [' eamp={0}'.format(electric_field_amplitude)]
    else:
        return []


def get_electrons_efield(name, **kwargs):
    try:
        electric_potential = kwargs['electric_potential']
        if electric_potential in ('Berry_Phase', 'sawtooth_potential'):
            return []
        electric_field_amplitude = kwargs['electric_field_amplitude']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []

    if electric_potential == 'homogenous_field':
        return [' efield={0}'.format(electric_field_amplitude)]
    else:
        return []


def get_system_edir(name, **kwargs):
    try:
        electric_potential = kwargs['electric_potential']
        electric_field_direction = kwargs['electric_field_direction']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []

    if electric_potential == 'sawtooth_potential':
        return [' edir={0}'.format(electric_field_direction)]
    else:
        return []


def get_electric_potential_related(name, **kwargs):
    try:
        electric_potential = kwargs['electric_potential']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []

    if name == 'tefield':
        return [' %s=%s' % (name, to_fortran(electric_potential == 'sawtooth_potential'))]
    elif name == 'lelfield':
        return [' %s=%s' % (name, to_fortran(electric_potential == 'homogenous_field'))]
    elif name == 'lberry':
        return [' %s=%s' % (name, to_fortran(electric_potential == 'Berry_Phase'))]
    return []


def get_control_gdir(name, **kwargs):
    try:
        electric_potential = kwargs['electric_potential']
        electric_field_direction = kwargs['electric_field_direction']
    except KeyError as err:
        logger.error("Missing required arguments when building "
                     "parameter '%s'! %s" % (name, err))
        return []

    if electric_potential in ('homogenous_field', 'Berry_Phase'):
        return [' gdir={0}'.format(electric_field_direction)]
    else:
        return []


def get_cell_dofree(name, **kwargs):
    assert isinstance(name, str)
    cell_dofree_str = " cell_dofree = '%s'"
    cell_dofree_all = 'all'
    ret = [cell_dofree_str % cell_dofree_all]
    map_data = {
        'fix_volume': 'shape',
        'fix_area': '2Dshape',
        'fix_xy': '2Dxy',
        'isotropic': 'volume',
        'cell_do_free': kwargs.get("cell_do_free")
    }

    if len(set(kwargs).intersection(map_data)) > 1:
        logger.error("only one of %s can be true" % ', '.join(map_data))
        return ret

    for key, val in map_data.items():
        if kwargs.get(key):
            return [cell_dofree_str % val]

    return ret


def neb_set_system_nat(name, **kwargs):
    """
    Extract SYSTEM[nat] from the first element of the list of atomic_structure

    :param name: Variable name
    :param kwargs: list of dictionaries each containing an atomic_structure element
    :return: list containing one string to be printed in system name list nat = nat_value
    """
    assert isinstance(name, str)
    try:
        images = kwargs['atomic_structure']
    except KeyError:
        logger.error('No atomic_structure element found !!!')
        return []

    try:
        nat_value = images[0]['@nat']
    except (KeyError, IndexError):
        logger.error("error reading nat value from atomic_structure !!!")
        return []

    return [' nat = {0}'.format(nat_value)]


def ha2ry(name, **kwargs):
    related_tag = kwargs['_related_tag']
    value = kwargs[related_tag] * 2.e0
    return [' {} = {:12.8f}'.format(name, value)]


def set_one_amass_line(name, **kwargs):
    lines = []
    try:
        node = kwargs['amass']
        value = float(node['$'])
        index = node['@atom']
        lines.append(' {}({})={:7.3f}'.format(name, index, value))
    except TypeError:
        for node in kwargs['amass']:
            value = float(node['$'])
            index = node['@atom']
            lines.append(' {}({})={:7.3f}'.format(name, index, value))
    return lines


def set_lda_plus_u_flag(name, **kwargs):
    assert isinstance(name, str)
    lines = []
    related_tag = kwargs['_related_tag']
    related_data = kwargs[related_tag]

    for value in iter(related_data if isinstance(related_data, list) else [related_data]):
        if value.get('@label') != 'no Hubbard' and value['$'] > 0:
            lines.append(f" {name} = .true.")
            break
    return lines


def set_boolean_flag(name, **kwargs):
    assert isinstance(name, str)
    lines = []
    related_tag = kwargs['_related_tag']
    related_data = kwargs[related_tag]
    if related_data is True or isinstance(related_data, str) and \
            related_data.strip() in ['true', 'True', 'TRUE', '1']:
        lines.append(' %s = .true.' % related_tag)
    else:
        lines.append(' %s = .false.' % related_tag)
    return lines


def set_what_td_calculation(name, **kwargs):
    assert isinstance(name, str)
    return [kwargs['whatTD']]


def get_xspectra_component(name, **kwargs):
    value = float(kwargs[name])
    lines = []
    lines.append(f" {name[:-1]}({name[-1]})={value}")
    return lines

