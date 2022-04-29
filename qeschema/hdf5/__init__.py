#
# Copyright (c), 2021, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
import numpy as np
import h5py

__all__ = ['read_charge_file', 'get_wf_attributes', 'get_wavefunctions',
           'get_wfc_miller_indices']


def read_charge_file(filename):
    """
    Reads a PW charge file in HDF5 format.

    :param filename: the name of the HDF5 file to read.
    :return: a dictionary describing the content of file \
    keys=[nr, ngm_g, gamma_only, rhog_, MillerIndexes]
    """
    with h5py.File(filename, "r") as h5f:
        MI = h5f.get('MillerIndices')[:]
        nr1 = 2 * max(abs(MI[:, 0])) + 1
        nr2 = 2 * max(abs(MI[:, 1])) + 1
        nr3 = 2 * max(abs(MI[:, 2])) + 1
        nr = np.array([nr1, nr2, nr3])
        res = dict(h5f.attrs.items())
        res.update({'MillInd': MI, 'nr_min': nr})
        rhog = h5f['rhotot_g'][:].reshape(res['ngm_g'], 2).dot([1.e0, 1.e0j])
        res['rhotot_g'] = rhog
        if 'rhodiff_g' in h5f.keys():
            rhog = h5f['rhodiff_g'][:].reshape(res['ngm_g'], 2).dot([1.e0, 1.e0j])
            res['rhodiff_g'] = rhog
        return res


# TODO update to the new format
def get_wf_attributes(filename):
    """
    Read attributes from a wfc HDF5 file.

    :param filename: the path to the wfc file
    :return: a dictionary with all attributes included reciprocal vectors
    """
    with h5py.File(filename, "r") as f:
        res = dict(f.attrs)
        mi_attrs = f.get('MillerIndices').attrs
        bg = np.array(mi_attrs.get(x) for x in ['bg1', 'bg2', 'bg3'])
        res.update({'bg': bg})
    return res


def get_wavefunctions(filename, start_band=None, stop_band=None):
    """
    Returns a numpy array with the wave functions for bands from start_band to
    stop_band. If not specified starts from 1st band and ends with last one.
    Band numbering is Python style starts from 0.abs

    :param filename: path to the wfc file
    :param start_band: first band to read, default first band in the file
    :param stop_band:  last band to read, default last band in the file
    :return: a numpy array with shape [nbnd,npw]
    """
    with h5py.File(filename, "r") as f:
        igwx = f.attrs.get('igwx')
        if start_band is None:
            start_band = 0
        if stop_band is None:
            stop_band = f.attrs.get('nbnd')
        if stop_band == start_band:
            stop_band = start_band + 1
        res = f.get('evc')[start_band:stop_band, :]

    res = np.asarray(x.reshape([igwx, 2]).dot([1.e0, 1.e0j]) for x in res[:])
    return res


def get_wfc_miller_indices(filename):
    """
    Reads miller indices from the wfc file

    :param filename: path to the wfc HDF5 file
    :return: a np.array of integers with shape [igwx,3]
    """
    with h5py.File(filename, "r") as f:
        res = f.get("MillerIndices")[:, :]
    return res
