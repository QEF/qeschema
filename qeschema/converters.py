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
Data format converters for Quantum Espresso.
"""
import copy
import logging
import re
import os.path
from collections.abc import Container

from .utils import to_fortran, BiunivocalMap
from . import cards, options

logger = logging.getLogger('qeschema')

FCP_NAMELIST = 'FCP'
PH_NAT_TODO_CARD = 'ph_nat_todo_card'
OPTIONAL_CARDS = {PH_NAT_TODO_CARD}


def conversion_maps_builder(template_map):
    """
    Build invariant and variant conversion maps from a template. The template
    is a multilevel dictionary that reproduce the structure of the input data.
    An entry maybe:

      1) a string with the list and the option names (eg: "CONTROL[calculation]").
         In this case the entry is mapped to this value, without modifications.

      2) a tuple with three items:
         - list and option names (eg: 'SYSTEM[Hubbard_U]');
         - the function that has to be used to calculate the namelist option
           value from XML value;
         - the function that has to be used to calculate to calculate the XML
           value data from namelist entry.

      3) a list of tuples when the XML entry has to be used to calculate other
         namelist or card's entries. Each tuple has the meaning of the previous
         case. The second and third elements may be None or empty if the template
         has another tuple with the same list and option names that indicate the
         transformation functions associated.

    :param template_map: Template dictionary
    :return: A couple of dictionaries, the first for invariant
    parameter mappings, se second for multi-dependent or type
    transformations.
    """
    def _check_variant(*args):
        if not args:
            raise ValueError("Empty sequence not admitted for a conversion map!")
        elif not isinstance(args[0], str):
            raise TypeError("The first element must be a string! '{0}'".format(args))
        elif len(args) == 1:
            return args[0], None, None
        elif len(args) == 2 and (callable(args[1]) or args[1] is None):
            return args[0], args[1], None
        elif len(args) == 3 and (callable(args[1]) or args[1] is None) \
                and (callable(args[2]) or args[2] is None):
            return args
        else:
            raise TypeError("Need a callable or None for 2nd and 3rd items! '{0}'".format(*args))

    def _build_maps(dict_element, path):
        for key, item in dict_element.items():
            path_key = '/'.join((path, key))
            if isinstance(item, dict):
                _build_maps(item, path_key)

            elif isinstance(item, str):
                invariant_map[path_key] = item
                logger.debug("Added one-to-one association: %r=%r", path_key, item)

            elif isinstance(item, (tuple, list)):
                try:
                    variant_map[path_key] = _check_variant(*item)
                    logger.debug("Added single-variant mapping: %r=%r",
                                 path_key, variant_map[path_key])
                except TypeError:
                    variants = []
                    for variant in item:
                        if isinstance(variant, str):
                            invariant_map[path_key] = variant
                        elif isinstance(variant, (tuple, list)):
                            variants.append(_check_variant(*variant))
                        else:
                            raise TypeError(f"Expect a tuple, list or string! {variant!r}")

                    variant_map[path_key] = tuple(variants)
                    logger.debug("Added multi-variant mapping: %r=%r",
                                 path_key, variant_map[path_key])

    invariant_map = BiunivocalMap()
    variant_map = dict()
    if not isinstance(template_map, dict):
        raise TypeError("A dictionary is needed!")
    _build_maps(template_map, '.')

    # Check inconsistencies between maps
    for items in variant_map.values():
        for value in items:
            logger.debug("Check value: %r", value)
            if isinstance(value, str) and value in invariant_map.inverse():
                raise ValueError("A variant is also in invariant map! "
                                 "'%s': '%s'" % (invariant_map.getkey(value), value))
            elif isinstance(value, tuple) and value[0] in invariant_map.inverse():
                raise ValueError("A variant is also in invariant map! "
                                 "'%s': '%s'" % (invariant_map.getkey(value[0]), value[0]))

    return invariant_map, variant_map


class RawInputConverter(Container):
    """
    A Fortran's namelist builder.
    """
    target_pattern = re.compile(r'(\w+)(?:\[((?:\w+)(?:%\w+)*)]|)')
    """RE pattern to extract Fortran input's namelist/card and name of a parameter"""

    def __init__(self, invariant_map, variant_map, input_namelists=None, input_cards=None):
        self.invariant_map = invariant_map
        """Map of parameters that are matched with one-to-one relation
        and which value is invariant from XML to QE Fortran input format."""

        self.variant_map = variant_map
        """Map of parameters that require a type conversion or are multi
        related with other inputs."""

        self.input_namelists = tuple(input_namelists) or (
            key for key in invariant_map.keys() + variant_map.keys()
        )
        """Sequence of input namelists. Use keys of the maps if not provided."""
        if input_cards:
            self.input_cards = tuple(input_cards)
        else:
            self.input_cards = ()
        """Sequence of input special cards, assuming an empty list if not provided."""

        self._input = dict(
            [(section, {}) for section in self.input_namelists + self.input_cards]
        )

    def __contains__(self, path):
        return path in self.invariant_map or path in self.variant_map

    def set_path(self, path, tag, node_dict):
        """
        Insert values for a path.

        :param path:
        :param tag:
        :param node_dict:
        :return:
        """
        if len(node_dict) != 1:
            raise ValueError("The node_dict argument must contains exactly "
                             "one element! {0}".format(node_dict))
        logger.debug("Set input with path %r and node dict %r", path, node_dict)
        _path, _, keyword = path.rpartition('/')
        value = node_dict[tag]
        if isinstance(value, dict) and keyword != tag:
            try:
                value = value[keyword]
            except KeyError:
                if keyword == '$':
                    value = node_dict[tag]
                else:
                    raise ValueError(
                        "Keyword '{0}' not found in node_dict \"{1}\"!".format(keyword, node_dict)
                    )

        if value is None:
            logger.debug("Skip element %r: None value!", path)
            return

        # Set the target parameter if the path is in invariant_map dictionary
        if not isinstance(value, dict) and path in self.invariant_map:
            self.set_parameter(path, value)

        # Add argument to variant transformations associated with the path
        if path in self.variant_map:
            self.add_kwarg(path, tag, node_dict)

    def set_parameter(self, path, value):
        target = self.invariant_map[path]
        match = self.target_pattern.match(target)
        if match is not None:
            namelist, name = match.groups()
        else:
            namelist = name = None
        if name is None:
            raise ValueError("Wrong value {!r} for invariant parameter {!r}".format(target, path))

        self._input[namelist][name] = to_fortran(value)
        logger.debug("Set %s[%s]=%s", namelist, name, self._input[namelist][name])

    def add_kwarg(self, path, tag, node_dict):
        if isinstance(self.variant_map[path][0], str):
            target_items = list([self.variant_map[path]])[:2]
        else:
            target_items = self.variant_map[path]
        for target, _get_qe_input, _ in target_items:
            logger.debug("Add argument to %r", target)
            logger.debug("Argument's conversion function: %r", _get_qe_input)
            group, name = self.target_pattern.match(target).groups()
            if name is not None:
                try:
                    name_dict = self._input[group][name]
                except KeyError:
                    self._input[group][name] = node_dict.copy()
                else:
                    try:
                        name_dict[tag].append(node_dict[tag])
                    except AttributeError:
                        name_dict[tag] = [self._input[group][name][tag], node_dict[tag]]
                    except KeyError:
                        name_dict.update(node_dict.copy())
                if _get_qe_input is not None:
                    self._input[group][name].update({
                        '_get_qe_input': _get_qe_input,
                        '_related_tag': tag
                    })
            else:
                try:
                    self._input[group][tag].append(node_dict[tag])
                except AttributeError:
                    self._input[group][tag] = [self._input[group][tag], node_dict[tag]]
                except KeyError:
                    self._input[group].update(node_dict.copy())
                if _get_qe_input is not None:
                    self._input[group].update({'_get_qe_input': _get_qe_input})

    def get_qe_input(self):
        if all([not section for section in self._input.values()]):
            logger.error("Empty input!")
        _input = self._input
        lines = []
        for namelist in self.input_namelists:

            if namelist == FCP_NAMELIST and not len(_input[namelist]):
                # Skip empty &FCP/ section
                continue

            lines.append('&%s' % namelist)
            for name, value in sorted(_input[namelist].items(), key=lambda x: x[0].lower()):
                logger.debug("Add input for parameter %s[%r] with value %r",
                             namelist, name, value)

                if isinstance(value, dict):
                    # Variant conversion: apply to_fortran_input function with saved arguments
                    try:
                        to_fortran_input = value['_get_qe_input']
                    except KeyError:
                        logger.debug('No conversion function for parameter %s[%r], skip ... ',
                                     namelist, name)
                        continue

                    if callable(to_fortran_input):
                        lines.extend(to_fortran_input(name, **value))
                    else:
                        logger.error('Parameter %s[%r] conversion function is not callable!',
                                     namelist, name)
                else:
                    # Simple invariant conversion
                    lines.append(' {0}={1}'.format(name, value))
            lines.append('/')

        for card in self.input_cards:
            logger.debug("Add card %r", card)
            card_args = _input[card]
            logger.debug("Card arguments: %r", card_args)

            if card not in OPTIONAL_CARDS and \
                    ('_get_qe_input' not in card_args or
                     not callable(card_args['_get_qe_input'])):
                logger.error("Missing conversion function for card %r", card)

            _get_qe_input = card_args.get('_get_qe_input', None)

            if callable(_get_qe_input):
                lines.extend(_get_qe_input(card, **card_args))
            elif card not in OPTIONAL_CARDS:
                logger.error('Card conversion function not found!')

        return '\n'.join(lines)

    def clear_input(self):
        del self._input
        self._input = dict(
            [(section, {}) for section in self.input_namelists + self.input_cards]
        )


class PwInputConverter(RawInputConverter):
    """
    Builds a Fortran's namelist input for PWscf.
    """
    PW_TEMPLATE_MAP = {
        'control_variables': {
            'title': "CONTROL[title]",
            'calculation': "CONTROL[calculation]",
            'restart_mode': "CONTROL[restart_mode]",
            'prefix': "CONTROL[prefix]",
            'pseudo_dir': "CONTROL[pseudo_dir]",
            'outdir': "CONTROL[outdir]",
            'stress': "CONTROL[tstress]",
            'forces': "CONTROL[tprnfor]",
            'wf_collect': "CONTROL[wf_collect]",
            'disk_io': "CONTROL[disk_io]",
            'max_seconds': "CONTROL[max_seconds]",
            'etot_conv_thr': "CONTROL[etot_conv_thr]",
            'forc_conv_thr': "CONTROL[forc_conv_thr]",
            'press_conv_thr': "CELL[press_conv_thr]",
            'verbosity': "CONTROL[verbosity]",
            'print_every': "CONTROL[iprint]",
            'nstep': "CONTROL[nstep]",
        },
        # Card ATOMIC species with attributes
        'atomic_species': {
            '@ntyp': 'SYSTEM[ntyp]',
            '$': [
                ("ATOMIC_SPECIES", cards.get_atomic_species_card, None),
                ('SYSTEM[Hubbard_U]',),
                ('SYSTEM[Hubbard_J0]',),
                ('SYSTEM[Hubbard_alpha]',),
                ('SYSTEM[Hubbard_beta]',),
                ('SYSTEM[Hubbard_J]',),
                ('SYSTEM[starting_ns_eigenvalue]',),
                ('SYSTEM[starting_magnetization]', options.get_starting_magnetization, None),
            ]
        },
        'atomic_structure': {
            '@nat': 'SYSTEM[nat]',
            '$': [
                ('SYSTEM[ibrav]', options.set_ibrav_to_zero, None),
                ("ATOMIC_POSITIONS", cards.get_atomic_positions_cell_card, None),
                ("CELL_PARAMETERS", cards.get_cell_parameters_card,  None)
            ],
            'atomic_positions': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None),
            'crystal_positions': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None),
            'wyckoff_positions': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None)
        },
        'dft': {
            'functional': "SYSTEM[input_dft]",
            'hybrid': {
                'qpoint_grid': {
                    '@nqx1': 'SYSTEM[nqx1]',
                    '@nqx2': 'SYSTEM[nqx2]',
                    '@nqx3': 'SYSTEM[nqx3]'
                },
                'ecutfock': ('SYSTEM[ecutfock]', options.ha2ry, None),
                'exx_fraction': 'SYSTEM[exx_fraction]',
                'screening_parameter': 'SYSTEM[screening_parameter]',
                'exxdiv_treatment': 'SYSTEM[exxdiv_treatment]',
                'x_gamma_extrapolation': 'SYSTEM[x_gamma_extrapolation]',
                'ecutvcut': ('SYSTEM[ecutvcut]', options.ha2ry, None)
            },
            'dftU': ('HUBBARD', cards.get_hubbard_card, None),
            'vdW': {
                'vdw_corr': 'SYSTEM[vdw_corr]',
                'london_s6': 'SYSTEM[london_s6]',
                'ts_vdw_econv_thr': 'SYSTEM[ts_vdw_econv_thr]',
                'ts_vdw_isolated': 'SYSTEM[ts_vdw_isolated]',
                'london_rcut': 'SYSTEM[london_rcut]',
                'xdm_a1': 'SYSTEM[xdm_a1]',
                'xdm_a2': 'SYSTEM[xdm_a2]',
                'dftd3_version': 'SYSTEM[dftd3_version]',
                'dftd3_threebody': 'SYSTEM[dftd3_threebody]',
                'london_c6': {
                    '$': ('SYSTEM[london_c6]', options.get_specie_related_values, None),
                }
            }
        },
        'spin': {
            'lsda': ("SYSTEM[nspin]", options.get_system_nspin, None),
            'noncolin': [
                ("SYSTEM[nspin]", options.get_system_nspin, None),
                "SYSTEM[noncolin]"
            ],
            'spinorbit': "SYSTEM[lspinorb]"
        },
        'bands': {
            'nbnd': "SYSTEM[nbnd]",
            'smearing': {
                '$': "SYSTEM[smearing]",
                '@degauss': "SYSTEM[degauss]"
            },
            'tot_charge': "SYSTEM[tot_charge]",
            'tot_magnetization': "SYSTEM[tot_magnetization]",
            'occupations': {
                '$': "SYSTEM[occupations]"
            }
        },
        'basis': {
            'gamma_only': ('K_POINTS', cards.get_k_points_card, None),
            'ecutwfc': "SYSTEM[ecutwfc]",
            'ecutrho': "SYSTEM[ecutrho]",
            'fft_grid': {
                'nr1': "SYSTEM[nr1]",
                'nr2': "SYSTEM[nr2]",
                'nr3': "SYSTEM[nr3]",
            },
            'fft_smooth': {
                'nr1': "SYSTEM[nr1s]",
                'nr2': "SYSTEM[nr2s]",
                'nr3': "SYSTEM[nr3s]",
            },
            'fft_box': {
                'nr1': "SYSTEM[nr1b]",
                'nr2': "SYSTEM[nr2b]",
                'nr3': "SYSTEM[nr3b]",
            },
            'spline_ps': "SYSTEM[spline_ps]"
        },
        'electron_control': {
            'diagonalization': "ELECTRONS[diagonalization]",
            'mixing_mode': "ELECTRONS[mixing_mode]",
            'mixing_beta': "ELECTRONS[mixing_beta]",
            'conv_thr': "ELECTRONS[conv_thr]",
            'mixing_ndim': "ELECTRONS[mixing_ndim]",
            'max_nstep': "ELECTRONS[electron_maxstep]",
            'real_space_q': "ELECTRONS[tqr]",
            'tq_smoothing': "ELECTRONS[tq_smoothing]",
            'tbeta_smoothing': "ELECTRONS[tbeta_smoothing]",
            'diago_thr_init': "ELECTRONS[diago_thr_init]",
            'diago_full_acc': "ELECTRONS[diago_full_acc]",
            'diago_cg_maxiter': "ELECTRONS[diago_cg_maxiter]"
        },
        'k_points_IBZ': ('K_POINTS', cards.get_k_points_card, None),
        'ion_control': {
            'ion_dynamics': "IONS[ion_dynamics]",
            'upscale': "IONS[upscale]",
            'remove_rigid_rot': "IONS[remove_rigid_rot]",
            'refold_pos': "IONS[refold_pos]",
            'bfgs': {
                'trust_radius_min': "IONS[trust_radius_min]",
                'trust_radius_max': "IONS[trust_radius_max]",
                'trust_radius_init': "IONS[trust_radius_ini]",
                'w1': "IONS[w_1]",
                'w2': "IONS[w_2]",
                'ndim': "IONS[bfgs_ndim]"
            },
            'md': {
                'pot_extrapolation': "IONS[pot_extrapolation]",
                'wfc_extrapolation': "IONS[wfc_extrapolation]",
                'ion_temperature': "IONS[ion_temperature]",
                'timestep': "CONTROL[dt]",
                'tempw': "IONS[tempw]",
                'tolp': "IONS[tolp]",
                'deltaT': "IONS[delta_t]",
                'nraise': "IONS[nraise]"
            }
        },
        'cell_control': {
            'cell_dynamics': "CELL[cell_dynamics]",
            'wmass': "CELL[wmass]",
            'cell_factor': "CELL[cell_factor]",
            'pressure': "CELL[press]",
            'free_cell': ("CELL_PARAMETERS", cards.get_cell_parameters_card, None),
            'fix_volume': ("CELL[cell_dofree]", options.get_cell_dofree, None),
            'fix_area': ("CELL[cell_dofree]", options.get_cell_dofree, None),
            'fix_xy': ("CELL[cell_dofree]", options.get_cell_dofree, None),
            'isotropic': ("CELL[cell_dofree]", options.get_cell_dofree, None),
            'cell_do_free': ("CELL[cell_dofree]", options.get_cell_dofree, None),
        },
        'symmetry_flags': {
            'nosym': "SYSTEM[nosym]",
            'nosym_evc': "SYSTEM[nosym_evc]",
            "noinv": "SYSTEM[noinv]",
            'no_t_rev': "SYSTEM[no_t_rev]",
            'force_symmorphic': "SYSTEM[force_symmorphic]",
            'use_all_frac': "SYSTEM[use_all_frac]"
        },
        'boundary_conditions': {
            'assume_isolated': "SYSTEM[assume_isolated]",
            'esm': {
                'bc': "SYSTEM[esm_bc]",
                'nfit': "SYSTEM[esm_nfit]",
                'w': "SYSTEM[esm_w]",
                'efield': "SYSTEM[esm_efield]"
            },
            'fcp_opt': "CONTROL[lfcp]",
            'fcp_mu': "FCP[fcp_mu]"
        },
        'ekin_functional': {
            'ecfixed': "SYSTEM[ecfixed]",
            'qcutz': "SYSTEM[qcutz]",
            'q2sigma': "SYSTEM[q2sigma]"
        },
        'external_atomic_forces': {
            '$': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None)
        },
        'free_positions': {
            '$': [("ATOMIC_POSITIONS", cards.get_atomic_positions_cell_card, None),
                  ("CELL_PARAMETERS",)]},
        'electric_field': {
            'electric_potential': [
                ("CONTROL[tefield]", options.get_electric_potential_related),
                ("CONTROL[lelfield]", options.get_electric_potential_related),
                ("CONTROL[lberry]", options.get_electric_potential_related),
                ("SYSTEM[eamp]", options.get_system_eamp),
                ("ELECTRONS[efield]", options.get_electrons_efield),
                ("SYSTEM[edir]", options.get_system_edir),
                ("CONTROL[gdir]", options.get_control_gdir)
            ],
            'dipole_correction': "CONTROL[dipfield]",
            'electric_field_direction': [
                ("SYSTEM[edir]", options.get_system_edir,),
                ("CONTROL[gdir]", options.get_control_gdir),
            ],
            'potential_max_position': "SYSTEM[emaxpos]",
            'potential_decrease_width': "SYSTEM[eopreg]",
            'electric_field_amplitude': [
                ("SYSTEM[eamp]", options.get_system_eamp,),
                ("ELECTRONS[efield]", options.get_electrons_efield),
            ],
            'electric_field_vector': "ELECTRONS[efield_cart]",
            'nk_per_string': "CONTROL[nppstr]",
            'n_berry_cycles': "CONTROL[nberrycyc]",
        },
        'atomic_constraints': ("CONSTRAINTS", cards.get_atomic_constraints_card),  # Card
        'spin_constraints': {
            'spin_constraints': "SYSTEM[constrained_magnetization]",
            'lagrange_multiplier': "SYSTEM[lambda]",
            'target_magnetization': "SYSTEM[fixed_magnetization]",
        }
    }

    def __init__(self, **kwargs):
        super(PwInputConverter, self).__init__(
            *conversion_maps_builder(self.PW_TEMPLATE_MAP),
            input_namelists=('CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL',
                             FCP_NAMELIST),
            input_cards=('ATOMIC_SPECIES', 'ATOMIC_POSITIONS', 'K_POINTS',
                         'CELL_PARAMETERS', 'ATOMIC_FORCES', 'HUBBARD')
        )
        if 'xml_file' in kwargs:
            self._input['CONTROL']['input_xml_schema_file'] = "{!r}".format(
                os.path.basename(kwargs['xml_file'])
            )

    def clear_input(self):
        super(PwInputConverter, self).clear_input()


class PhononInputConverter(RawInputConverter):
    """
    Convert to/from Fortran input for Phonon.
    """
    PHONON_TEMPLATE_MAP = {
        'xq': {
         '$': ('qPointsSpecs', cards.get_qpoints_card, None),
        },
        'scf_ph': {
            'tr2_ph': "INPUTPH[tr2_ph]",
            'niter_ph': "INPUTPH[niter_ph]",
            'alpha_mix': "INPUTPH[alpha_mix]",
            'nmix_ph': "INPUTPH[nmix_ph]",
        },
        'files': {
            'prefix': "INPUTPH[prefix]",
            'outdir': "INPUTPH[outdir]",
            'fildyn': "INPUTPH[fildyn]",
            'fildrho': "INPUTPH[fildrho]",
            'fildvscf': "INPUTPH[fildvscf]",
            'lqdir': "INPUTPH[lqdir]",
        },
        'control_ph': {
            'ldisp': ["INPUTPH[ldisp]", ('qPointsSpecs', cards.get_qpoints_card, None)],
            'epsil': "INPUTPH[epsil]",
            'trans': "INPUTPH[trans]",
            'zeu': "INPUTPH[zeu]",
            'zue': "INPUTPH[zue]",
            'elop': "INPUTPH[elop]",
            'fpol': "INPUTPH[fpol]",
            'lraman': "INPUTPH[lraman]",
            'search_sym': "INPUTPH[search_sym]",
        },
        'control_job': {
            'recover': "INPUTPH[recover]",
            'max_seconds': "INPUTPH[max_seconds]",
        },
        'control_diel': {
            'lrpa': "INPUTPH[lrpa]",
            'lnoloc': "INPUTPH[lnoloc]",
        },
        'control_qplot': {
            'qplot': [('qPointsSpecs', cards.get_qpoints_card, None), "INPUTPH[qplot]"],
            'q2d': "INPUTPH[q2d]",
            'q_in_band_form': "INPUTPH[q_in_band_form]"
        },
        'miscellanea': {
            'amass': {'$': ("INPUTPH[amass]", options.set_one_amass_line, None)},
            'verbosity': "INPUTPH[verbosity]",
            'reduce_io': "INPUTPH[reduce_io]",
            'low_directory_check': "INPUTPH[low_directory_check]",
            'nogg': "INPUTPH[nogg]",
            'nscf_MPgrid': {
                'nk1': "INPUTPH[nk1]",
                'nk2': "INPUTPH[nk2]",
                'nk3': "INPUTPH[nk3]",
                'k1': "INPUTPH[k1]",
                'k2': "INPUTPH[k2]",
                'k3': "INPUTPH[k3]",
            }
        },
        'irr_repr': {
            'start_q': "INPUTPH[start_q]",
            'last_q': "INPUTPH[last_q]",
            'start_irr': "INPUTPH[start_irr]",
            'last_irr': "INPUTPH[last_irr]",
            'nat_todo':
            {
                '@natom': 'INPUTPH[nat_todo]',
                '$': [(PH_NAT_TODO_CARD, cards.get_nat_todo_card, None)]
            },
            'modenum': "INPUTPH[modenum]",
            'only_init': "INPUTPH[only_init]",
            'ldiag': "INPUTPH[ldiag]",
        },
        'electron_phonon_options': {
            'electron_phonon': "INPUTPH[electron_phonon]",
            'dvscf_star': {
                'open': "INPUTPH[dvscf_star%open]",
                'dir': "INPUTPH[dvscf_star%dir]",
                'ext': "INPUTPH[dvscf_star%ext]",
                'basis': "INPUTPH[dvscf_star%basis]",
                'pat': "INPUTPH[dvscf_star%pat]",
            },
            'drho_star': {
                'open': "INPUTPH[drho_star%open]",
                'dir': "INPUTPH[drho_star%dir]",
                'ext': "INPUTPH[drho_star%ext]",
                'basis': "INPUTPH[drho_star%basis]",
                'pat': "INPUTPH[drho_star%pat]",
            }
        },
        'lraman_options': {
            'eth_rps': "INPUTPH[eth_rps]",
            'eth_ns': "INPUTPH[eth_ns]",
            'dek': "INPUTPH[dek]",
        },
        'q_points': {
            'grid': {
                '@nq1': "INPUTPH[nq1]",
                '@nq2': "INPUTPH[nq2]",
                '@nq3': "INPUTPH[nq3]"
            },
            'q_points_list': ('qPointsSpecs', cards.get_qpoints_card, None),
            'nqs': ('qPointsSpecs', cards.get_qpoints_card, None)
        }
    }

    def __init__(self, **_kwargs):
        super(PhononInputConverter, self).__init__(
            *conversion_maps_builder(self.PHONON_TEMPLATE_MAP),
            input_namelists=('INPUTPH',),
            input_cards=('qPointsSpecs', PH_NAT_TODO_CARD)
        )


class NebInputConverter(RawInputConverter):
    """
    Convert to/from Fortran input for Phonon.
    """
    NEB_TEMPLATE_MAP = {
        'path': {
            'restartMode': "PATH[restart_mode]",
            'stringMethod': "PATH[string_method]",
            'pathNstep': "PATH[nstep_path]",
            'numOfImages': "PATH[num_of_images]",
            'optimizationScheme': "PATH[opt_scheme]",
            'optimizationStepLength': "PATH[ds]",
            'elasticConstMax': "PATH[k_max]",
            'elasticConstMin': "PATH[k_min]",
            'pathThreshold': "PATH[path_thr]",
            'endImagesOptimizationFlag': "PATH[first_last_opt]",
            'minimumImageFlag': "PATH[minimum_image]",
            'temperature': "PATH[temp_req]",
            'climbingImage': [
                "PATH[CI_scheme]",
                ("CLIMBING_IMAGES", cards.get_climbing_images, None)
            ],
            'useMassesFlag': "PATH[use_masses]",
            'useFreezingFlag': "PATH[use_freezing]",
            'constantBiasFlag': "PATH[lfcp]",
            'targetFermiEnergy': "PATH[fcp_mu]",
            'totChargeFirst': "PATH[fcp_tot_charge_first]",
            'totChargeLast': "PATH[fcp_tot_charge_last]",
            'climbingImageIndex': ("CLIMBING_IMAGES", cards.get_climbing_images, None)
        }
    }

    def __init__(self, **_kwargs):
        engine_template_map = copy.deepcopy(PwInputConverter.PW_TEMPLATE_MAP)
        engine_template_map['atomic_structure'] = {
            '@nat': ("SYSTEM[nat]", options.neb_set_system_nat, None),
            '$': [
                ('SYSTEM[ibrav]', options.set_ibrav_to_zero, None),
                ("CELL_PARAMETERS", cards.get_neb_cell_parameters_card, None),
                ("ATOMIC_POSITIONS", cards.get_neb_images_positions_card, None)
            ],
            'atomic_positions': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None),
            'crystal_positions': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None),
            'wyckoff_positions': ('ATOMIC_FORCES', cards.get_atomic_forces_card, None)
        }
        engine_template_map['free_positions'] = {
            '$': ("ATOMIC_POSITIONS", cards.get_neb_images_positions_card, None)
        }
        self.NEB_TEMPLATE_MAP.update({'engine': engine_template_map})
        super(NebInputConverter, self).__init__(
            *conversion_maps_builder(self.NEB_TEMPLATE_MAP),
            input_namelists=('PATH', 'CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL'),
            input_cards=('CLIMBING_IMAGES', 'ATOMIC_SPECIES', 'ATOMIC_POSITIONS', 'K_POINTS',
                         'CELL_PARAMETERS', 'ATOMIC_FORCES', 'HUBBARD')
        )

    def get_qe_input(self):
        """
        Overrides method in RawInputConverter because few lines
        in between the namelists are requested for the NEB input.

        :return: a string containing the text input for NEB calculations
        """
        qe_input = super(NebInputConverter, self).get_qe_input().split('\n')
        qe_input = ['BEGIN', 'BEGIN_PATH_INPUT'] + qe_input
        index = qe_input.index('&CONTROL')
        qe_input = qe_input[:index] + ['END_PATH_INPUT', 'BEGIN_ENGINE_INPUT'] + qe_input[index:]
        qe_input += ['END_ENGINE_INPUT', 'END']
        return '\n'.join(qe_input)


class TdInputConverter(RawInputConverter):
    """
    converts qes_lr schema to fortran input for turbo_lanczos, turbo_davidson and turbo_eels
    """
    TD_TEMPLATE_MAP = {
        'whatTD': ('cache[what]', options.set_what_td_calculation, None),
        'lr_input': {
            'restart': ('lr_input[restart]', options.set_boolean_flag, None),
            'restart_step': 'lr_input[restart_step]',
            'verbosity': 'lr_input[lr_verbosity]',
            'disk_io': 'lr_input[disk_io]',
            'prefix': 'lr_input[prefix]',
            'wfcdir': 'lr_input[wfcdir]',
            'outdir': 'lr_input[outdir]',
            'max_seconds': 'lr_input[max_seconds'
        },
        'lr_control': {
            'itermax': 'lr_control[itermax]',
            'n_pol': 'lr_control[n_ipol]',
            'ipol': 'lr_control[ipol]',
            'ltammd': ('lr_control[ltammd]', options.set_boolean_flag, None),
            'lrpa': ('lr_control[lrpa]', options.set_boolean_flag, None),
            'charge_response': ('lr_control[charge_response]', options.set_boolean_flag, None),
            'tqr': ('lr_control[tqr]', options.set_boolean_flag, None),
            'auto_rs': ('lr_control[auto_rs]', options.set_boolean_flag, None),
            'no_hxc': ('lr_control[no_hxc]', options.set_boolean_flag, None),
            'lproject': ('lr_control[lproject]', options.set_boolean_flag, None),
            'scissor': 'lr_control[scissor]',
            'ecutfock': 'lr_control[ecutfock]',
            'pseudo_hermitian': ('lr_control[pseudo_hermitian]', options.set_boolean_flag, None),
            'd0psi_rs': ('lr_control[d0psi_rs]', options.set_boolean_flag, None),
            'lshift_d0psi': ('lr_control[d0psi_rs]', options.set_boolean_flag, None),
            'q1': 'lr_control[q1]',
            'q2': 'lr_control[q2]',
            'q3': 'lr_control[q3]',
            'eels_approx': 'lr_control[approximation]'
        },
        'lr_davidson': {
            'num_eignv': 'lr_dav[num_eign]',
            'num_init': 'lr_dav[num_init]',
            'num_basis_max': 'lr_dav[num_basis_max]',
            'res_conv_thr': 'lr_dav[res_conv_thr]',
            'precondition': ('lr_dav[precondition]', options.set_boolean_flag, None),
            'reference': 'lr_dav[reference]',
            'single_pole': ('lr_dav[single_pole]', options.set_boolean_flag, None),
            'sort_contr': ('lr_dav[sort_contr', options.set_boolean_flag, None),
            'diag_of_h': ('lr_dav[diag_of_h]', options.set_boolean_flag, None),
            'close_pre': ('lr_dav[close_pre]', options.set_boolean_flag, None),
            'broadening': 'lr_dav[broadening]',
            'print_spectrum': ('lr_dav[print_spectrum]', options.set_boolean_flag, None),
            'start': 'lr_dav[start]',
            'finish': 'lr_dav[finish]',
            'step': 'lr_dav[step]',
            'if_checkorth': ('lr_dav[if_checkorth]', options.set_boolean_flag, None),
            'if_random_init': ('lr_dav[if_random_init]', options.set_boolean_flag, None),
            'if_check_her': ('lr_dav[if_check_her]', options.set_boolean_flag, None),
            'p_nbnd_occ': 'lr_dav[p_nbnd_occ]',
            'p_nbnd_virt': 'lr_dav[p_nbnd_virt]',
            'poor_of_ram': ('lr_dav[poor_of_ram]', options.set_boolean_flag, None),
            'max_iter': 'lr_dav[max_iter]',
            'ecutfock': 'lr_dav[ecutfock]',
            'conv_assistant': ('lr_dav[conv_assistant]', options.set_boolean_flag, None),
            'if_dft_spectrum': ('lr_dav[if_dft_spectrum]', options.set_boolean_flag, None),
            'no_hxc': ('lr_dav[no_hxc]', options.set_boolean_flag, None),
            'd0psi_rs': ('lr_dav[d0psi_rs]', options.set_boolean_flag, None),
            'lshift_d0psi': ('lr_dav[lshift_d0psi]', options.set_boolean_flag, None),
            'lplot_drho': ('lr_dav[lplot_drho]', options.set_boolean_flag, None),
            'vccouple_shift': 'lr_dav[vccouple_shift]',
            'ltammd': ('lr_dav[ltammd]', options.set_boolean_flag, None)
        },
        'lr_post': {
            'omeg': 'lr_post[omeg]',
            'beta_z_gamma_prefix': 'lr_post[beta_z_gamma_prefix]',
            'w_T_npol': 'lr_post[w_T_npol]',
            'plot_type': 'lr_post[plot_type]',
            'epsil': 'lr_post[epsil]',
            'iter_maxinit': 'lr_post[iter_maxinit]',
            'sum_rule': ('lr_post[sum_rule]', options.set_boolean_flag, None)
        }
    }

    def __init__(self, **_kwargs):
        super(TdInputConverter, self).__init__(
            *conversion_maps_builder(self.TD_TEMPLATE_MAP),
            input_namelists=('cache', 'lr_input', 'lr_control', 'lr_dav', 'lr_post')
        )

    def get_qe_input(self):
        """
        Overrides superclass get_qe_input with use_defaults set to False.
        :return: the input as obtained from its input builder
        """
        temp = super(TdInputConverter, self).get_qe_input().split('\n')
        for i, j in enumerate(temp):
            print(i, " - ", j)
        td = temp[1]
        start = temp.index('&lr_input')
        end = start + temp[start:].index('/')
        qe_input = '\n'.join(temp[start:end + 1])
        """ put lr_input in qe_input """

        if td.lower() in ('lanczos', 'eels'):
            start = temp.index('&lr_control')
        elif td.lower() == 'davidson':
            start = temp.index('&lr_dav')
        end = start + temp[start:].index('/')
        qe_input = qe_input + '\n' + '\n'.join(temp[start:end + 1])
        """ put one of lr_control(lanczos) or lr_davidson in qe_input"""

        start = temp.index('&lr_post')
        end = start + temp[start:].index('/')
        if end - start > 1:
            qe_input = qe_input + '\n' + '\n'.join(temp[start:end + 1])
        """ if not empty add lr_post namelist to qe_input """
        return qe_input


class TdSpectrumInputConverter(RawInputConverter):
    """
    Converts the XML input file described by qes_spectrum scheme in
    namelist input for turbo_spectrum post-processing tool.
    """
    SPEC_TEMPLATE_MAP = {
        'itermax': 'lr_input[itermax]',
        'itermax0': 'lr_input[itermax0]',
        'itermax_actual': 'lr_input[itermax_actual]',
        'extrapolation': 'lr_input[extrapolation]',
        'start': 'lr_input[start]',
        'end': 'lr_input[end]',
        'increment': 'lr_input[increment]',
        'ipol': 'lr_input[ipol]',
        'outdir': 'lr_input[outdir]',
        'prefix': 'lr_input[prefix]',
        'epsil': 'lr_input[epsil]',
        'sym_op': 'lr_input[sym_op]',
        'verbosity': 'lr_input[verbosity]',
        'units': 'lr_input[units]',
        'td': 'lr_input[td]',
        'eign_file': 'lr_input[eign_file]',
        'eels': ('lr_input[eels]', options.set_boolean_flag, None),
    }

    def __init__(self, **_kwargs):
        super(TdSpectrumInputConverter, self).__init__(
            *conversion_maps_builder(self.SPEC_TEMPLATE_MAP),
            input_namelists=['lr_input']
        )


TD_spctInConverter = TdSpectrumInputConverter


# XSpectra Input Converter
class XSpectraInputConverter(RawInputConverter):
    """
    Converts the XML input file described by XSPECTRA scheme in
    namelist input for XSPECTRA post-processing tool.
    """
    XSPECTRA_TEMPLATE_MAP = {
        'input_xspectra': {'calculation': 'input_xspectra[calculation]',
                           'verbosity': 'input_xspectra[verbosity]',
                           'prefix': 'input_xspectra[prefix]',
                           'outdir': 'input_xspectra[outdir]',
                           'xiabs': 'input_xspectra[xiabs]',
                           # xkvec
                           'xkvec1': ('input_xspectra[xkvec1]', options.get_xspectra_c, None),
                           'xkvec2': ('input_xspectra[xkvec2]', options.get_xspectra_c, None),
                           'xkvec3': ('input_xspectra[xkvec3]', options.get_xspectra_c, None),
                           # xepsilon
                           'xepsilon1': ('input_xspectra[xepsilon1]', options.get_xspectra_c, None),
                           'xepsilon2': ('input_xspectra[xepsilon2]', options.get_xspectra_c, None),
                           'xepsilon3': ('input_xspectra[xepsilon3]', options.get_xspectra_c, None),
                           'xcoordcrys': 'input_xspectra[xcoordcrys]',
                           'ef_r': 'input_xspectra[ef_r]',
                           'xe0': 'input_xspectra[xe0]',
                           'xonly_pot': 'input_xspectra[xonly_pot]',
                           'xread_wf': 'input_xspectra[xread_wf]',
                           'x_save_file': 'input_xspectra[x_save_file]',
                           'xniter': 'input_xspectra[xniter]',
                           'xerror': 'input_xspectra[xerror]',
                           'xcheck_conv': 'input_xspectra[xcheck_conv]',
                           'show_status': 'input_xspectra[show_status]',
                           'nelup': 'input_xspectra[nelup]',
                           'neldw': 'input_xspectra[neldw]',
                           'U_projection_type': 'input_xspectra[U_projection_type]',
                           'time_limit': 'input_xspectra[time_limit]',
                           'restart_mode': 'input_xspectra[restart_mode]',
                           'edge': 'input_xspectra[edge]',
                           'lplus': 'input_xspectra[lplus]',
                           'lminus': 'input_xspectra[lminus]'},
        'plot': {'xnepoint': 'plot[xnepoint]',
                 'xgamma': 'plot[xgamma]',
                 'xemax': 'plot[xemax]',
                 'xemin': 'plot[xemin]',
                 'cut_occ_states': 'plot[cut_occ_states]',
                 'terminator': 'plot[terminator]',
                 'gamma_mode': 'plot[gamma_mode]',
                 'gamma_file': 'plot[gamma_file]',
                 'gamma_energy': 'plot[gamma_energy]',
                 'gamma_value': 'plot[gamma_value]',
                 'xanes_file': 'plot[xanes_file]'},
        'pseudos': {'filecore': 'pseudos[filecore]',
                    'filerecon': 'pseudos[filerecon]',
                    # rpaw
                    'r_paw0': ('pseudos[r_paw0]', options.get_xspectra_c, None),
                    'r_paw1': ('pseudos[r_paw1]', options.get_xspectra_c, None),
                    'r_paw2': ('pseudos[r_paw2]', options.get_xspectra_c, None),
                    'r_paw3': ('pseudos[r_paw3]', options.get_xspectra_c, None)},
        'cut_occ': {'cut_ierror': 'cut_occ[cut_ierror]',
                    'cut_stepu': 'cut_occ[cut_stepu]',
                    'cut_stepl': 'cut_occ[cut_stepl]',
                    'cut_startt': 'cut_occ[cut_startt]',
                    'cut_tinf': 'cut_occ[cut_tinf]',
                    'cut_tsup': 'cut_occ[cut_tsup]',
                    'cut_desmooth': 'cut_occ[cut_desmooth]',
                    'cut_nmemu': 'cut_occ[cut_nmemu]',
                    'cut_nmeml': 'cut_occ[cut_nmeml]'},
        'k_points_IBZ': ('K_POINTS', cards.get_xspectra_k_points_card, None),
    }

    def __init__(self, **_kwargs):
        super(XSpectraInputConverter, self).__init__(
            *conversion_maps_builder(self.XSPECTRA_TEMPLATE_MAP),
            input_namelists=('input_xspectra', 'plot', 'pseudos', 'cut_occ'),
            input_cards=("K_POINTS",)
        )
