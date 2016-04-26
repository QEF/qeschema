#
# Copyright (c), 2015-2016, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato, Giovanni Borghi
#
"""
Conversion functions for Quantum Espresso input options.
"""

import logging
from .exceptions import ConfigError

# from .utils import set_logger

logger = logging.getLogger('qespresso')


#
# Other derived values
def get_specie_related_values(name, **kwargs):
    """
    Convert XML data for specie related options.
    Map single values, vectors and matrices.

    :param name: parameter name
    :param kwargs:
    :return: string
    """
    try:
        related_tag = kwargs['_related_tag']
        tag_data = kwargs[related_tag]
        tag_specie = tag_data['species']
        tag_values = tag_data['_text']
        atomic_species = kwargs['atomic_species']
        species = atomic_species['species']
    except KeyError as err:
        key = str(err).strip("'")
        if key != '_text':
            logger.error("Missing required arguments when building "
                         "parameter '%s'! %s" % (name, key))
        return []

    specie_index = 1
    for specie in species:
        if specie['name'] == tag_specie:
            break
        specie_index += 1
    else:
        raise ConfigError("Unknown specie '%s' in tag '%s'" % (tag_specie, name))

    if isinstance(tag_values, list):
        lines = []
        for k in range(len(tag_values)):
            lines.append(' {0}({1},{2})={3}'.format(
                name, k + 1, specie_index, tag_values[k]
            ))
        return lines
    else:
        return [' {0}({1})={2}'.format(name, specie_index, tag_values)]


def get_starting_magnetization(name, **kwargs):
    """
    Build starting magnetization vector from species data.

    :param name: parameter name
    :param kwargs:
    :return: string
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

    :param name:
    :param kwargs:
    :return:
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


def get_system_eamp(name, **kwargs):
    """

    :param name:
    :param kwargs:
    :return:
    """
    try:
        electric_potential = kwargs['electric_potential']
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
    """
    :param name:
    :param kwargs:
    :return:
    """
    try:
        electric_potential = kwargs['electric_potential']
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
    """
    :param name:
    :param kwargs:
    :return:
    """
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

    from .converters import to_fortran
    if name == 'tefield':
        return [' %s=%s' % (name, to_fortran(electric_potential == 'sawtooth_potential'))]
    elif name == 'lelfield':
        return [' %s=%s' % (name, to_fortran(electric_potential == 'homogenous_field'))]
    elif name == 'lberry':
        return [' %s=%s' % (name, to_fortran(electric_potential == 'Berry_Phase'))]
    return []


def get_control_gdir(name, **kwargs):
    """
    :param name:
    :param kwargs:
    :return:
    """
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
