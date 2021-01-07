#
# Copyright (c), 2021, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
import numpy as np
import h5py


def read_charge_file_hdf5(filename):
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


def get_minus_indexes(g1, g2, g3):
    """
    Used for getting the corresponding minus Miller Indexes. It is meant
    to be used for converting Gamma Trick grids and is defined only for
    the for i >=0, in the i =0 plan is defined only for j >=0 and when
    i=0 j=0 k must be >=0. Out of this domain returns None.

    :param g1: rank 1 array containing first Miller Index
    :param g2: rank 1 array containing second Miller Index
    :param g3: rank 1 array containing third Miller Index
    :return: a rank 2 array with dimension (ngm/2,3) containing mirrored Miller indexes
    """

    def scalar_func(i, j, k):
        """
        scalar function to be vectorized
        :param i: 1st Miller Index
        :param j: 2nd
        :param k: 3rd
        :return: the mirrored mirror indexes
        """
        if i > 0:
            return -i, j, k
        elif i == 0 and j > 0:
            return 0, -j, k
        elif i == 0 and j == 0 and k > 0:
            return 0, 0, -k
        else:
            return i, j, k

    vector_func = np.vectorize(scalar_func)

    res = np.array(vector_func(g1, g2, g3))
    return res.transpose()


def get_charge_r(filename, nr=None):
    """
    Reads a charge file written with QE in HDF5 format. *nr = [nr1,nr2,nr3]* (the dimensions of
    the charge k-points grid) are given as parameter (taken for the xml output file by the caller).

    Notes: In the new format, the values of the charge in the reciprocal space are stored.
    Besides, only the values of the charge > cutoff are stored, together with the Miller indexes.
    Hence
    """
    cdata = read_charge_file_hdf5(filename)
    if nr is None:
        nr1, nr2, nr3 = cdata['nrmin']
    else:
        nr1, nr2, nr3 = nr
    gamma_only = 'TRUE' in str(cdata['gamma_only']).upper()

    # Load the total charge
    rho_temp = np.zeros([nr1, nr2, nr3], dtype=np.complex128)
    for (i, j, k), rho in zip(cdata['MillInd'], cdata['rhotot_g']):
        try:
            rho_temp[i, j, k] = rho
        except IndexError:
            pass

    if gamma_only:
        rhotot_g = cdata['rhotot_g'].conjugate()
        MI = get_minus_indexes(
            cdata['MillInd'][:, 0], cdata['MillInd'][:, 1], cdata['MillInd'][:, 2]
        )
        print("MI", MI)
        for (i, j, k), rho in zip(MI, rhotot_g):
            try:
                rho_temp[i, j, k] = rho
            except IndexError:
                pass

    rhotot_r = np.fft.ifftn(rho_temp) * nr1 * nr2 * nr3

    # Read the charge difference spin up - spin down if present (for magnetic calculations)
    if 'rhodiff_g' in cdata.keys():
        rho_temp = np.zeros([nr1, nr2, nr3], dtype=np.complex128)
        for (i, j, k), rho in zip(cdata['MillInd'], cdata['rhodiff_g']):
            try:
                rho_temp[i, j, k] = rho
            except IndexError:
                pass

        if gamma_only:
            rhodiff_g = cdata['rhodiff_g'].conjugate()
            for (i, j, k), rho in zip(MI, rhodiff_g):
                try:
                    rho_temp[i, j, k] = rho
                except IndexError:
                    pass

        rhodiff_r = np.fft.ifftn(rho_temp) * nr1 * nr2 * nr3
        return rhotot_r.real, rhodiff_r.real
    else:
        return rhotot_r.real, None


def write_charge(filename, charge, header):
    """
    Write the charge or another quantity calculated by postqe into a text file *filename*.
    """

    fout = open(filename, "w")

    # The header contains some information on the system, the grid nr, etc.
    fout.write(header)
    nr = charge.shape
    count = 0
    # Loop with the order as in QE files
    for z in range(0, nr[2]):
        for y in range(0, nr[1]):
            for x in range(0, nr[0]):
                fout.write("  {:.9E}".format(charge[x, y, z]))
                count += 1
                if count % 5 == 0:
                    fout.write("\n")

    fout.close()
