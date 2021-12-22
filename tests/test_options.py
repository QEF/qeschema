#!/usr/bin/env python3
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
# Authors: Davide Brunato
#
import unittest
import logging

from qeschema import XmlDocumentError
from qeschema.options import get_specie_related_values, get_starting_magnetization, \
    get_system_nspin, set_ibrav_to_zero, get_system_eamp, get_electrons_efield, \
    get_system_edir, get_electric_potential_related, get_control_gdir, \
    get_cell_dofree, neb_set_system_nat, ha2ry, set_one_amass_line, \
    set_lda_plus_u_flag, set_boolean_flag, set_what_td_calculation

logger = logging.getLogger('qeschema')


class TestConversionFunctions(unittest.TestCase):

    def test_get_specie_related_values(self):
        kwargs = {
            'atomic_species': {
                '@ntyp': 3,
                'species': [
                    {'@name': 'O1', 'mass': 1.0, 'pseudo_file': 'O.pz-rrkjus.UPF',
                     'starting_magnetization': 0.0},
                    {'@name': 'Fe1', 'mass': 1.0, 'pseudo_file': 'Fe.pz-nd-rrkjus.UPF',
                     'starting_magnetization': 0.5},
                    {'@name': 'Fe2', 'mass': 1.0, 'pseudo_file': 'Fe.pz-nd-rrkjus.UPF',
                     'starting_magnetization': -0.5}]},
            'Hubbard_U': [{'@specie': 'O1', '@label': 'no Hubbard', '$': 0.0},
                          {'@specie': 'Fe1', '@label': '3d', '$': 0.3160442},
                          {'@specie': 'Fe2', '@label': '3d', '$': 0.3160442}],
            '_related_tag': 'Hubbard_U'
        }
        result = get_specie_related_values('Hubbard_U', **kwargs)
        self.assertListEqual(result, [' Hubbard_U(2)=0.3160442', ' Hubbard_U(3)=0.3160442'])

        kwargs['Hubbard_U'][1]['@spin'] = True
        result = get_specie_related_values('Hubbard_U', **kwargs)
        self.assertListEqual(result, [' Hubbard_U(2)=0.3160442', ' Hubbard_U(3)=0.3160442'])

        kwargs['atomic_species']['species'][1]['@name'] = 'unknown'
        with self.assertRaises(XmlDocumentError) as ctx:
            get_specie_related_values('Hubbard_U', **kwargs)
        self.assertEqual(str(ctx.exception), "Unknown specie 'Fe1' in tag 'Hubbard_U'")

        del kwargs['atomic_species']['species'][1]['@name']
        with self.assertRaises(KeyError):
            get_specie_related_values('Hubbard_U', **kwargs)

        del kwargs['atomic_species']
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_specie_related_values('Hubbard_U', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required argument "
                                          "'atomic_species' when building parameter 'Hubbard_U'"])

        kwargs = {
            'atomic_species': {
                '@ntyp': 3,
                'species': [
                    {'@name': 'O1', 'mass': 1.0, 'pseudo_file': 'O.pz-rrkjus.UPF',
                     'starting_magnetization': 0.0},
                    {'@name': 'Fe1', 'mass': 1.0, 'pseudo_file': 'Fe.pz-nd-rrkjus.UPF',
                     'starting_magnetization': 0.5},
                    {'@name': 'Fe2', 'mass': 1.0, 'pseudo_file': 'Fe.pz-nd-rrkjus.UPF',
                     'starting_magnetization': -0.5}]
            },
            'Hubbard_J': [{'@specie': 'O1', '@label': 'no Hubbard', '$': [1.0, 0.0, 0.0]},
                          {'@specie': 'Fe1', '@label': '3d', '$': [0.0, 1.0, 0.0]},
                          {'@specie': 'Fe2', '@label': '3d', '$': [0.0, 0.0, 1.0]}],
            '_related_tag': 'Hubbard_J'
        }

        result = get_specie_related_values('Hubbard_J', **kwargs)
        self.assertListEqual(result, [' Hubbard_J(2,2)=1.0', ' Hubbard_J(3,3)=1.0'])

    def test_get_starting_magnetization(self):
        kwargs = {
            'atomic_species': {
                'species': [{'@name': 'Al', 'mass': 26.981538, 'pseudo_file': 'Al.pbe-n-van.UPF'},
                            {'@name': 'H', 'mass': 1.00794, 'pseudo_file': 'H.pbe-van_ak.UPF'}]
            },
            '_related_tag': 'atomic_species'
        }
        result = get_starting_magnetization('starting_magnetization', **kwargs)
        self.assertListEqual(result, [' starting_magnetization(1)=0.0', ' starting_magnetization(2)=0.0'])

        del kwargs['atomic_species']
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_starting_magnetization('starting_magnetization', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when building "
                                          "parameter 'starting_magnetization'! 'atomic_species'"])

    def test_get_system_nspin(self):
        kwargs = {'lsda': True, '_related_tag': 'noncolin', 'noncolin': False}

        result = get_system_nspin('nspin', **kwargs)
        self.assertListEqual(result, [' nspin=2'])

        del kwargs['lsda']
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_system_nspin('nspin', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments "
                                          "when building parameter 'nspin'! 'lsda'"])

    def test_set_ibrav_to_zero(self):
        self.assertListEqual(set_ibrav_to_zero('name'), [' ibrav=0'])

    def test_get_system_eamp(self):
        kwargs = {'electric_potential': 'Berry_Phase', '_related_tag': 'electric_potential'}

        result = get_system_eamp('eamp', **kwargs)
        self.assertListEqual(result, [])

        kwargs['electric_potential'] = 'sawtooth_potential'
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_system_eamp('eamp', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when "
                                          "building parameter 'eamp'! 'electric_field_amplitude'"])

        kwargs['electric_field_amplitude'] = '0.0000000E+00'
        result = get_system_eamp('eamp', **kwargs)
        self.assertListEqual(result, [' eamp=0.0000000E+00'])

        kwargs['electric_potential'] = 'unknown'
        result = get_system_eamp('eamp', **kwargs)
        self.assertListEqual(result, [])

    def test_get_electrons_efield(self):
        kwargs = {'electric_potential': 'Berry_Phase', '_related_tag': 'electric_potential'}

        result = get_electrons_efield('efield', **kwargs)
        self.assertListEqual(result, [])

        kwargs['electric_potential'] = 'homogenous_field'
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_electrons_efield('efield', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when "
                                          "building parameter 'efield'! 'electric_field_amplitude'"])

        kwargs['electric_field_amplitude'] = '0.0000000E+00'
        result = get_electrons_efield('efield', **kwargs)
        self.assertListEqual(result, [' efield=0.0000000E+00'])

        kwargs['electric_potential'] = 'unknown'
        result = get_electrons_efield('efield', **kwargs)
        self.assertListEqual(result, [])

    def test_get_system_edir(self):
        kwargs = {'electric_potential': 'Berry_Phase',
                  '_related_tag': 'electric_field_direction',
                  'electric_field_direction': 3}

        result = get_system_edir('edir', **kwargs)
        self.assertListEqual(result, [])

        kwargs['electric_potential'] = 'sawtooth_potential'
        result = get_system_edir('edir', **kwargs)
        self.assertListEqual(result, [' edir=3'])

        del kwargs['electric_potential']
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_system_edir('edir', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when "
                                          "building parameter 'edir'! 'electric_potential'"])

    def test_get_electric_potential_related(self):
        result = get_electric_potential_related('tefield', electric_potential='Berry_Phase')
        self.assertListEqual(result, [' tefield=.false.'])

        result = get_electric_potential_related('lelfield', electric_potential='Berry_Phase')
        self.assertListEqual(result, [' lelfield=.false.'])

        result = get_electric_potential_related('lberry', electric_potential='Berry_Phase')
        self.assertListEqual(result, [' lberry=.true.'])

        result = get_electric_potential_related('unknown', electric_potential='Berry_Phase')
        self.assertListEqual(result, [])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_electric_potential_related('lberry')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when "
                                          "building parameter 'lberry'! 'electric_potential'"])

    def test_get_control_gdir(self):
        kwargs = {'electric_potential': 'Berry_Phase',  'electric_field_direction': 3}

        result = get_control_gdir('gdir', **kwargs)
        self.assertListEqual(result, [' gdir=3'])

        kwargs['electric_potential'] = 'other'
        result = get_control_gdir('gdir', **kwargs)
        self.assertListEqual(result, [])

        del kwargs['electric_potential']
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_control_gdir('gdir', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when "
                                          "building parameter 'gdir'! 'electric_potential'"])

    def test_get_cell_dofree(self):
        result = get_cell_dofree('cell_dofree')
        self.assertListEqual(result, [ " cell_dofree = 'all'"])

        result = get_cell_dofree('cell_dofree', fix_volume=True)
        self.assertListEqual(result, [" cell_dofree = 'shape'"])

        result = get_cell_dofree('cell_dofree', fix_area=True)
        self.assertListEqual(result, [" cell_dofree = '2Dshape'"])

        result = get_cell_dofree('cell_dofree', isotropic=True)
        self.assertListEqual(result, [" cell_dofree = 'volume'"])

        result = get_cell_dofree('cell_dofree',cell_do_free="ibrav+volume")
        self.assertListEqual(result, [" cell_dofree = 'ibrav+volume'"])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_cell_dofree('cell_dofree', fix_volume=True, fix_area=True)

        self.assertListEqual(result, [" cell_dofree = 'all'"])
        err = ('ERROR:qeschema:only one of fix_volume, fix_area, fix_xy, '
               'isotropic, cell_do_free can be true')
        self.assertEqual(context.output, [err])

        with self.assertLogs(logger, level='ERROR' ) as context:
          result = get_cell_dofree('cell_dofree', fix_volume=True, cell_do_free="volume")
        err = ('ERROR:qeschema:only one of fix_volume, fix_area, fix_xy, '
               'isotropic, cell_do_free can be true')
        self.assertEqual(context.output, [err])

    def test_neb_set_system_nat(self):
        with self.assertLogs(logger, level='ERROR') as context:
            result = neb_set_system_nat('nat')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:No atomic_structure element found !!!'])

        result = neb_set_system_nat('nat', atomic_structure=[{'@nat': 5}])
        self.assertListEqual(result, [' nat = 5'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = neb_set_system_nat('nat', atomic_structure=[{}])
        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:error reading nat value from atomic_structure !!!'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = neb_set_system_nat('nat', atomic_structure=[])
        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:error reading nat value from atomic_structure !!!'])

    def test_ha2ry(self):
        result = ha2ry('alpha', _related_tag='value', value=10)
        self.assertListEqual(result, [' alpha =  20.00000000'])

    def test_set_one_amass_line(self):
        result = set_one_amass_line('amass', amass={'@atom': 1, '$': 26.98})
        self.assertListEqual(result, [' amass(1)= 26.980'])

        result = set_one_amass_line('amass', amass=[{'@atom': 1, '$': 26.98}, {'@atom': 2, '$': 74.92}])
        self.assertListEqual(result, [' amass(1)= 26.980', ' amass(2)= 74.920'])

    def test_set_lda_plus_u_flag(self):
        kwargs = {
            '_related_tag': 'Hubbard_U',
            'Hubbard_U': [{'@specie': 'O1', '@label': 'no Hubbard', '$': 0.0},
                          {'@specie': 'Fe1', '$': 0.3160442},
                          {'@specie': 'Fe2', '$': 0.3160442}],
        }

        result = set_lda_plus_u_flag('lda_plus_u', **kwargs)
        self.assertListEqual(result, [' lda_plus_u = .true.'])

        result = set_lda_plus_u_flag('lda_plus', _related_tag='Hubbard_U', Hubbard_U=[])
        self.assertListEqual(result, [])

    def test_set_boolean_flag(self):
        result = set_boolean_flag('restart', restart=False, _related_tag='restart')
        self.assertListEqual(result, [' restart = .false.'])

        result = set_boolean_flag('pseudo_hermitian', pseudo_hermitian=True, _related_tag='pseudo_hermitian')
        self.assertListEqual(result, [' pseudo_hermitian = .true.'])

    def test_set_what_td_calculation(self):
        result = set_what_td_calculation('what', whatTD='davidson')
        self.assertListEqual(result, ['davidson'])

        with self.assertRaises(AssertionError):
            set_what_td_calculation(True, whatTD='davidson')

        with self.assertRaises(KeyError):
            set_what_td_calculation('what')


if __name__ == '__main__':
    unittest.main()
