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
        self.assertListEqual(
            result, ['ATOMIC_SPECIES', ' Al 26.981538 Al.pbe-n-van.UPF', ' H 1.00794 H.pbe-van_ak.UPF']
        )

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

        result = get_atomic_positions_cell_card(
            'ATOMIC_POSITIONS', atomic_structure={'atomic_positions': {}}
        )
        self.assertListEqual(result, ['ATOMIC_POSITIONS bohr'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_positions_cell_card(
                'ATOMIC_POSITIONS', atomic_structure={'atomic_positions': {'something': True}}
            )
        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Cannot find any atoms '
                                          'for building ATOMIC_POSITIONS!'])

    def test_get_atomic_constraints_card(self):
        with self.assertLogs(logger, level='ERROR') as context:
            result = get_atomic_constraints_card('CONSTRAINTS')

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema:Missing required arguments '
                                          'when building CONSTRAINTS card!'])

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
            'atomic_positions': [
                {'atom': [{'@name': 'H', '@index': 1, '$': [-4.56670009, 0.0, 0.0]},
                          {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                          {'@name': 'H', '@index': 3, '$': [1.55776676, 0.0, 0.0]}]},
                {'atom': [{'@name': 'H', '@index': 1, '$': [-1.55776676, 0.0, 0.0]},
                          {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                          {'@name': 'H', '@index': 3, '$': [4.56670009, 0.0, 0.0]}]}
            ]}

        with self.assertLogs(logger, level='DEBUG') as context:
            result = get_atomic_forces_card('ATOMIC_FORCES', **kwargs)

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['DEBUG:qeschema:Missing required arguments '
                                          'when building ATOMIC_FORCES card!'])

    def test_get_cell_parameters_card(self):
        kwargs = {
            'atomic_structure': {
                '@nat': 1,
                '@alat': 7.5,
                'atomic_positions': {'atom': [{'@name': 'Al', '$': [0.0, 0.0, 0.0]}]},
                'cell': {'a1': [-0.5, 0.0, 0.5], 'a2': [0.0, 0.5, 0.5], 'a3': [-0.5, 0.5, 0.0]}},
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

    def test_get_climbing_images(self):
        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='no-CI')
        self.assertListEqual(result, [''])

        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='auto')
        self.assertListEqual(result, [''])

        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='manual', climbingImageIndex=[])
        self.assertListEqual(result, [''])

        result = get_climbing_images('CLIMBING_IMAGES', climbingImage='manual', climbingImageIndex=10)
        self.assertListEqual(result, [' 10 '])

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
                    'cell': {'a1': [12.0, 0.0, 0.0], 'a2': [0.0, 12.0, 0.0], 'a3': [0.0, 0.0, 12.0]}},
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'atomic_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-1.55776676, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [4.56670009, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0], 'a2': [0.0, 12.0, 0.0], 'a3': [0.0, 0.0, 12.0]}}
            ]}

        result = get_neb_images_positions_card('ATOMIC_POSITIONS', **kwargs)
        self.assertEqual(result[0], 'BEGIN_POSITIONS ')
        self.assertEqual(result[1], 'FIRST_IMAGE ')
        self.assertEqual(result[2], 'ATOMIC_POSITIONS { bohr }')
        self.assertEqual(re.sub(r'\s+', ' ', result[-2]), 'H 4.56670009 0.00000000 0.00000000')
        self.assertEqual(result[-1], 'END_POSITIONS ')
        self.assertEqual(len(result), 12)

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
                    'cell': {'a1': [12.0, 0.0, 0.0], 'a2': [0.0, 12.0, 0.0], 'a3': [0.0, 0.0, 12.0]}},
                {
                    '@nat': 3,
                    '@alat': 12.0,
                    'crystal_positions': {
                        'atom': [{'@name': 'H', '@index': 1, '$': [-0.1298139, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 2, '$': [0.0, 0.0, 0.0]},
                                 {'@name': 'H', '@index': 3, '$': [0.38055834, 0.0, 0.0]}]},
                    'cell': {'a1': [12.0, 0.0, 0.0], 'a2': [0.0, 12.0, 0.0], 'a3': [0.0, 0.0, 12.0]}}]}

        result = get_neb_cell_parameters_card('CELL_PARAMETERS', **kwargs)
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['CELL_PARAMETERS bohr',
                              ' 12.00000000 0.00000000 0.00000000',
                              ' 0.00000000 12.00000000 0.00000000',
                              ' 0.00000000 0.00000000 12.00000000'])

        result = get_neb_cell_parameters_card('CELL_PARAMETERS', atomic_structure=kwargs['atomic_structure'][0])
        self.assertListEqual([re.sub(r'\s+', ' ', s) for s in result],
                             ['CELL_PARAMETERS bohr',
                              ' 12.00000000 0.00000000 0.00000000',
                              ' 0.00000000 12.00000000 0.00000000',
                              ' 0.00000000 0.00000000 12.00000000'])

        with self.assertLogs(logger, level='ERROR') as context:
            result = get_neb_cell_parameters_card('CELL_PARAMETERS', atomic_structure=[])

        self.assertListEqual(result, [])
        self.assertEqual(context.output, ['ERROR:qeschema: No atomic_structure element found in kwargs !!!'])

    def test_get_neb_atomic_forces_card(self):
        self.assertIsNone(get_neb_atomic_forces_card('atomic_forces'))


if __name__ == '__main__':
    unittest.main()
