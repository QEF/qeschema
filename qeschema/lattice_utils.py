#
# Copyright (c), 2015-2021, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# Authors: Davide Brunato, Pietro Delugas
#

import logging 
import numpy as np
from math import isclose

logger = logging.getLogger("qeschema")

def abc_from_cell(cell, dgts=5):
  """
  cell: dictionary with 'a1','a2','a3' keys with values corresponding to the 3 lattice vectors
  returns: 6ple with values of A,B,C,cos(AB), cos(BC), cos(AC) lenghts in Angstrom and cosines of the 
           lattice vectors
  """
  at = np.array((cell['a1'],cell['a2'], cell['a3']))
  A = round(np.sqrt(at[0].dot(at[0])),dgts) 
  B = round(np.sqrt(at[1].dot(at[1])),dgts)
  C = round(np.sqrt(at[2].dot(at[2])),dgts) 
  COSAB = round(at[0].dot(at[1])/A/B, dgts) 
  COSBC = round(at[1].dot(at[2])/B/C, dgts)
  COSAC = round(at[2].dot(at[0])/C/A, dgts)  
  bohr2ang = 0.529177 
  return (round(A * bohr2ang,dgts), round(B * bohr2ang,dgts), round(C * bohr2ang,dgts), 
  COSAB, COSBC, COSAC) 

def signed_ibrav(ibrav, alternative_axes):
  if alternative_axes is None:
    return ibrav 
  if ibrav == 3 and  alternative_axes == "b:a-b+c:-c":
    return -3 
  elif ibrav == 5 and  alternative_axes == "3fold-111":
    return -5 
  elif ibrav == 9:
    if alternative_axes == "-b:a:c":
      return -9 
    elif alternative_axes == "bcoA-type":
      return 91
    else:
      logger.error("%s is not a valid alternative-axes string for ibrav %i" % (alternative_axes, ibrav))  
  elif ibrav == 91:
    return 91 
  elif (ibrav == 12 or ibrav == 13) and alternative_axes == "unique-axis-b":
    return -ibrav 
  else:
    logger.error("%s is not a valid alternative-axes string for ibrav %i" % (alternative_axes,ibrav))

  



