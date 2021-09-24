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
import re

from qeschema.cards import get_atomic_species_card, get_atomic_positions_cell_card, \
    get_atomic_constraints_card, get_k_points_card, get_atomic_forces_card, \
    get_cell_parameters_card, get_qpoints_card, get_climbing_images, \
    get_neb_images_positions_card, get_neb_cell_parameters_card, \
    get_neb_atomic_forces_card

logger = logging.getLogger('qeschema')


class TestCardsFunctions(unittest.TestCase):

    def test_get_atomic_species_card(self):
        kwargs = {
            'atomic_species': {
                'species': [{'@name': 'Al', 'mass': 26.981538, 'pseudo_file': 'Al.pbe-n-van.UPF'},
                            {'@name': 'H', 'mass': 1.00794, 'pseudo_file': 'H.pbe-van_ak.UPF'}]
            }}

        result = get_atomic_species_card('ATOMIC_SPECIES', **kwargs)
        self.assertListEqual(result, ['ATOMIC_SPECIES',
                                      ' Al 26.981538 Al.pbe-n-van.UPF',
                                      ' H 1.00794 H.pbe-van_ak.UPF'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_species_card('ATOMIC_SPECIES')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments when "
                                          "building ATOMIC_SPECIES card! 'atomic_species'"])

    def test_get_atomic_positions_cell_card(self):
        kwargs = {
            'atomic_structure': {
                '@nat': 4,
                '@alat': 8.19,
                'atomic_positions': {
                    'atom': [{'@name': 'O1', '$': [0.5, 0.5, 0.5]},
                             {'@name': 'O1', '$': [1.5, 1.5, 1.5]},
                             {'@name': 'Fe1', '$': [0.0, 0.0, 0.0]},
                             {'@name': 'Fe2', '$': [1.0, 1.0, 1.0]}]
                },
                'cell': {'a1': [0.5, 0.5, 1.0], 'a2': [0.5, 1.0, 0.5], 'a3': [1.0, 0.5, 0.5]}
            },
        }

        result = get_atomic_positions_cell_card('ATOMIC_POSITIONS', **kwargs)
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['ATOMIC_POSITIONS bohr',
                              'O1 0.50000000 0.50000000 0.50000000',
                              'O1 1.50000000 1.50000000 1.50000000',
                              'Fe1 0.00000000 0.00000000 0.00000000',
                              'Fe2 1.00000000 1.00000000 1.00000000'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_positions_cell_card('ATOMIC_POSITIONS')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Missing required arguments '
                                          'when building ATOMIC_POSITIONS card!'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_positions_cell_card(
                'ATOMIC_POSITIONS', atomic_structure={'atomic_positions': {}}
            )
        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Cannot find any atoms '
                                          'for building ATOMIC_POSITIONS!'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_positions_cell_card(
                'ATOMIC_POSITIONS', atomic_structure={'atomic_positions': {'something': True}}
            )
        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Cannot find any atoms '
                                          'for building ATOMIC_POSITIONS!'])

        # Test with wyckoff_positions
        kwargs = {
            'atomic_structure': {
                '@nat': 1,
                '@alat': 7.42,
                'wyckoff_positions': {'atom': {'@name': 'Pt', '$': [0.0, 0.0, 0.0]}},
                'cell': {'a1': [-0.5, 0.0, 0.5],
                         'a2': [0.0, 0.5, 0.5],
                         'a3': [-0.5, 0.5, 0.0]}
            }
        }
        result = get_atomic_positions_cell_card('ATOMIC_POSITIONS', **kwargs)
        self.assertListEqual(result, ['ATOMIC_POSITIONS crystal_sg',
                                      'Pt     0.00000000    0.00000000    0.00000000'])

        # Test with logging errors
        kwargs = {
            'atomic_structure': {
                '@nat': 2,
                '@alat': 12.0,
                'atomic_positions': {'atom': [{'@name': 'C', '$': ['0.188', 0.0, 0.0]},
                                              {'@name': 'O', '$': [0.0, 0.0, 0.0]}]},
                'cell': {'a1': [1.0, 0.0, 0.0], 'a2': [0.0, 1.0, 0.0], 'a3': [0.0, 0.0, 1.0]}
            },
            'free_positions': {'@rank': 1, '@dims': [1], '$': [1]}
        }

        with self.assertLogs('qeschema', 'ERROR') as ctx:
            result = get_atomic_positions_cell_card('ATOMIC_POSITIONS', **kwargs)
        self.assertEqual(ctx.output, [
            'ERROR:qeschema:ATOMIC_POSITIONS: incorrect number of position constraints!',
            'ERROR:qeschema:ATOMIC_POSITIONS: incorrect datatype in positions!',
        ])
        self.assertListEqual(result, ['ATOMIC_POSITIONS bohr',
                                      'O      0.00000000    0.00000000    0.00000000'])

    def test_get_atomic_constraints_card(self):
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_constraints_card('CONSTRAINTS')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Missing required arguments '
                                          'when building CONSTRAINTS card!'])

        result = get_atomic_constraints_card(
            'CONSTRAINTS', num_of_constraints=1, tolerance=0.2, atomic_constraints=[]
        )
        self.assertListEqual(result, ['CONSTRAINTS', '1 0.2'])
        result = get_atomic_constraints_card(
            'CONSTRAINTS', num_of_constraints=1, tolerance=0.2, atomic_constraints=[{
                'constr_parms': [0.2, 0.3, 0.1, 0.9],
                'constr_type': 'test_constraint',
                'constr_target': 0.3,
            }]
        )
        self.assertListEqual(result, ['CONSTRAINTS', '1 0.2',
                                      'test_constraint 0.2 0.3 0.1 0.9 0.3'])

    def test_get_k_points_card(self):
        result = get_k_points_card('K_POINTS', k_points_IBZ={
            'monkhorst_pack': {'@nk1': 6, '@nk2': 6, '@nk3': 1, '@k1': 1, '@k2': 1, '@k3': 1}
        })
        self.assertListEqual(result, ['K_POINTS automatic', ' 6 6 1 1 1 1'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_k_points_card('K_POINTS')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ["ERROR:qeschema:Missing required arguments "
                                          "when building K_POINTS card! 'k_points_IBZ'"])

    def test_get_atomic_forces_card(self):
        kwargs = {
            'atomic_positions': {'atom': [{'@name': 'H', '@index': 1,
                                           '$': [-4.56670009, 0.0, 0.0]},
                                          {'@name': 'H', '@index': 2,
                                           '$': [0.0, 0.0, 0.0]},
                                          {'@name': 'H', '@index': 3,
                                           '$': [1.55776676, 0.0, 0.0]},
                                          {'@name': 'H', '@index': 1,
                                           '$': [-1.55776676, 0.0, 0.0]},
                                          {'@name': 'H', '@index': 2,
                                           '$': [0.0, 0.0, 0.0]},
                                          {'@name': 'H', '@index': 3,
                                           '$': [4.56670009, 0.0, 0.0]}]},
            'external_atomic_forces': [0.0, 0.0, 0.0,
                                       0.0, 0.0, 0.1,
                                       0.0, 0.0, -0.1,
                                       0.2, 0.0, 0.0,
                                       -0.2, 0.0, 0.0,
                                       0.0, 0.0, 0.0]
        }
        result = get_atomic_forces_card('ATOMIC_FORCES', **kwargs)
        self.assertListEqual(result, ['ATOMIC_FORCES', 
                                      'H        0.00000000     0.00000000     0.00000000',
                                      'H        0.00000000     0.00000000     0.10000000',
                                      'H        0.00000000     0.00000000    -0.10000000',
                                      'H        0.20000000     0.00000000     0.00000000',
                                      'H       -0.20000000     0.00000000     0.00000000',
                                      'H        0.00000000     0.00000000     0.00000000'])

        kwargs['external_atomic_forces'].pop()
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_forces_card('ATOMIC_FORCES', **kwargs)
        self.assertListEqual(result, ['ATOMIC_FORCES',
                                      'H        0.00000000     0.00000000     0.00000000',
                                      'H        0.00000000     0.00000000     0.10000000',
                                      'H        0.00000000     0.00000000    -0.10000000',
                                      'H        0.20000000     0.00000000     0.00000000',
                                      'H       -0.20000000     0.00000000     0.00000000'])
        self.assertListEqual(context.output, ['ERROR:qeschema:incorrect number of atomic forces'])

        # with self.assertLogs(logger, level='DEBUG') as context:
        #    result = get_atomic_forces_card('ATOMIC_FORCES', **kwargs)
        # self.assertListEqual(result,[])
        # self.assertEqual(context.output, ['DEBUG:qeschema:Missing required arguments '
        #                                  'when building ATOMIC_FORCES card!'])

        # FIXME: a fix is required in get_atomic_forces_card()
        # result = get_atomic_forces_card('ATOMIC_FORCES',
        #                                 external_atomic_forces=[0.1, 0.2], **kwargs)
        # self.assertListEqual(result, [])

    def test_get_cell_parameters_card(self):
        kwargs = {
            'atomic_structure': {
                '@nat': 1,
                '@alat': 7.5,
                'atomic_positions': {'atom': [{'@name': 'Al', '$': [0.0, 0.0, 0.0]}]},
                'cell': {'a1': [-0.5, 0.0, 0.5],
                         'a2': [0.0, 0.5, 0.5],
                         'a3': [-0.5, 0.5, 0.0],
                         'a4': 'test only, this item is skipped.'}},
        }

        result = get_cell_parameters_card('CELL_PARAMETERS', **kwargs)
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['CELL_PARAMETERS bohr',
                              ' -0.50000000 0.00000000 0.50000000 ',
                              ' 0.00000000 0.50000000 0.50000000 ',
                              ' -0.50000000 0.50000000 0.00000000 '])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_cell_parameters_card('CELL_PARAMETERS')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Missing required arguments '
                                          'when building CELL_PARAMETERS card!'])

        kwargs['atomic_structure'].pop('cell')
        result = get_cell_parameters_card('CELL_PARAMETERS', **kwargs)
        self.assertListEqual(result, [])

    def test_get_qpoints_card(self):
        result = get_qpoints_card('qPointsSpecs', ldisp=True)
        self.assertListEqual(result, [])

        result = get_qpoints_card('qPointsSpecs', ldisp=False)
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['0.0000 0.0000 0.0000'])

        kwargs = {
            'qplot': True,
            'nqs': 10,
            'q_points_list': {
                'q_point': [{'@weight': 0.1, '$': [0.1, 0.0, 0.0]},
                            {'@weight': 0.1, '$': [0.5, 0.0, 0.0]},
                            {'@weight': 0.1, '$': [1.0, 0.0, 0.0]}]
            }
        }
        result = get_qpoints_card('qPointsSpecs', **kwargs)
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             [' 10', ' 0.1 0.0 0.0 0.1', ' 0.5 0.0 0.0 0.1', ' 1.0 0.0 0.0 0.1'])

        kwargs.pop('nqs')
        with self.assertLogs(logger, level='WARNING') as context:
            result = get_qpoints_card('qPointsSpecs', **kwargs)
        self.assertListEqual(context.output, ['WARNING:qeschema:qplot was set to true in input '
                                              'but no value for nqs was provided: assuming nqs=1'])
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             [' 1', ' 0.1 0.0 0.0 0.1', ' 0.5 0.0 0.0 0.1', ' 1.0 0.0 0.0 0.1'])

    def test_get_climbing_images(self):
        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='no-CI')
        self.assertListEqual(result, [''])

        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='auto')
        self.assertListEqual(result, [''])

        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='manual',
                                     climbingImageIndex=[])
        self.assertListEqual(result, [''])

        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='manual',
                                     climbingImageIndex=10)
        self.assertListEqual(result, [' 10 '])

        result = get_climbing_images('CLIMBING_IMAGES')
        self.assertListEqual(result, [''])

    def test_get_neb_images_positions_card(self):
        kwargs = {
            'atomic_structure': [
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'atomic_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-4.56670009, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [1.55776676, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0],
                             'a2': [0.0, 12.0, 0.0],
                             'a3': [0.0, 0.0, 12.0]}},
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'atomic_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-1.55776676, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [4.56670009, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0],
                             'a2': [0.0, 12.0, 0.0],
                             'a3': [0.0, 0.0, 12.0]}}
            ]}

        result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertEqual(len(result), 12)
        self.assertListEqual(result, [
            'BEGIN_POSITIONS ',
            'FIRST_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -4.56670009    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      1.55776676    0.00000000    0.00000000',
            'LAST_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -1.55776676    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      4.56670009    0.00000000    0.00000000',
            'END_POSITIONS '
        ])

        kwargs['free_positions'] = {
            '@rank': 2, '@dims': [3, 3], '$': [1, 1, 1, 1, 1, 1, 1, 1, 1]
        }
        result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertEqual(len(result), 12)
        self.assertListEqual(result, [
            'BEGIN_POSITIONS ',
            'FIRST_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -4.56670009    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      1.55776676    0.00000000    0.00000000',
            'LAST_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -1.55776676    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      4.56670009    0.00000000    0.00000000',
            'END_POSITIONS '
        ])
        kwargs.pop('free_positions')

        kwargs['atomic_structure'].append(kwargs['atomic_structure'][-1])
        result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertEqual(len(result), 17)
        self.assertListEqual(result, [
            'BEGIN_POSITIONS ',
            'FIRST_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -4.56670009    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      1.55776676    0.00000000    0.00000000',
            'INTERMEDIATE_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -1.55776676    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      4.56670009    0.00000000    0.00000000',
            'LAST_IMAGE ',
            'ATOMIC_POSITIONS { bohr }',
            'H     -1.55776676    0.00000000    0.00000000',
            'H      0.00000000    0.00000000    0.00000000',
            'H      4.56670009    0.00000000    0.00000000',
            'END_POSITIONS '
        ])

        kwargs['atomic_structure'][-1]['atomic_positions']['atom'].pop()
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertEqual(context.output[0],
                         'ERROR:qeschema:found images with differing number of atoms !!!')
        self.assertEqual(result, '')

        kwargs['atomic_structure'] = kwargs['atomic_structure'][0]
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertListEqual(context.output, ['ERROR:qeschema:at least the atomic structures '
                                              'for first and last image should be provided'])
        self.assertListEqual(result, [])

        kwargs = {
            'atomic_structure': [
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'atomic_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-4.56670009, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0],
                             'a2': [0.0, 12.0, 0.0],
                             'a3': [0.0, 0.0, 12.0]}},
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'atomic_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-1.55776676, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [4.56670009, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0],
                             'a2': [0.0, 12.0, 0.0],
                             'a3': [0.0, 0.0, 12.0]}}
            ]}

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertListEqual(context.output, [
            'ERROR:qeschema:nat provided in first image differs from number '
            'of atoms in atomic_positions!!!'])
        self.assertEqual(result, '')

        kwargs['free_positions'] = {'@rank': 1, '@dims': [1], '$': [1]}
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertListEqual(context.output, [
            'ERROR:qeschema:nat provided in first image differs from number '
            'of atoms in atomic_positions!!!'])
        self.assertEqual(result, '')

        kwargs['atomic_structure'][0]['atomic_positions']['atom'].clear()
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertListEqual(context.output, [
            'ERROR:qeschema:no atomic coordinates provided for first image'
        ])
        self.assertEqual(result, '')

    def test_get_neb_cell_parameters_card(self):
        kwargs = {
            'atomic_structure': [
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'crystal_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-0.38055834, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [0.1298139, 0.0, 0.0]}]},
                    'cell': {'a0': [12.0, 0.0, 0.0],  # Ignored, only for testing
                             'a1': [12.0, 0.0, 0.0],
                             'a2': [0.0, 12.0, 0.0],
                             'a3': [0.0, 0.0, 12.0]}},
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'crystal_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-0.1298139, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [0.38055834, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0],
                             'a2': [0.0, 12.0, 0.0],
                             'a3': [0.0, 0.0, 12.0]}}]}

        result = get_neb_cell_parameters_card('CELL_PARAMETERS', **kwargs)
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['CELL_PARAMETERS bohr',
                              ' 12.00000000 0.00000000 0.00000000',
                              ' 0.00000000 12.00000000 0.00000000',
                              ' 0.00000000 0.00000000 12.00000000'])

        result = get_neb_cell_parameters_card('CELL_PARAMETERS',
                                              atomic_structure=kwargs['atomic_structure'][0])
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['CELL_PARAMETERS bohr',
                              ' 12.00000000 0.00000000 0.00000000',
                              ' 0.00000000 12.00000000 0.00000000',
                              ' 0.00000000 0.00000000 12.00000000'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_cell_parameters_card('CELL_PARAMETERS', atomic_structure=[])

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema: No atomic_structure '
                                          'element found in kwargs !!!'])

        kwargs['atomic_structure'][0]['cell'].clear()
        result = get_neb_cell_parameters_card('CELL_PARAMETERS', **kwargs)
        self.assertListEqual(result, [])

    def test_get_neb_atomic_forces_card(self):
        self.assertIsNone(get_neb_atomic_forces_card('atomic_forces'))


if __name__ == '__main__':
    unittest.main()
