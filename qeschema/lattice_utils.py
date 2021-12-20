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
from numpy.lib.twodim_base import tri

from xmlschema.validators.helpers import base64_binary_validator

logger = logging.getLogger("qeschema")

def bohr2angs(l):
  la: float = l * 0.529177210903
  return la 

def angs2bohr(l: float):
  """
  l: float legth in Angstroem to convert in Bohr units 
  """
  lb: float = l / 0.529177210903
  return lb 

def latgen(celldm, ibrav_):
  if ibrav_ in [1,2,3,-3]:
    c1 = celldm[0]  * np.array([1.0, 0.0, 0.0]) 
    c2 = celldm[0]  * np.array([0.0, 1.0, 0.0])
    c3 = celldm[0]  * np.array([0.0, 0.0, 1.0])
    if ibrav_ ==1: 
      v1 = c1 
      v2 = c2 
      v3 = c3 
    elif ibrav_ == 2:
      v1 =  0.5e0 * ( c3  - c1 ) 
      v2 =  0.5e0 * ( c2  + c3 )
      v3 =  0.5e0 * ( c2  - c1 )
    elif ibrav_ == -3:
      v1 = 0.5e0 * ( -c1 + c2 + c3 )
      v2 = 0.5e0 * ( +c1 - c2 + c3 ) 
      v3 = 0.5e0 * ( +c1 + c2 - c3 )
    elif ibrav_ == 3:
      v1 = 0.5e0 * ( c1 + c2 + c3 ) 
      v2 = 0.5e0 * (-c1 + c2 + c3 ) 
      v3 = 0.5e0 * (-c1 - c2 + c3 ) 
  elif ibrav_ == 4:
    cab = np.cos(np.pi/3.0)
    sab = np.sin(np.pi/3.0)
    v1 = celldm[0] *             np.array([  1.0,   0.0,   0.0])
    v2 = celldm[0] *             np.array([  cab,   sab,   0.0])
    v3 = celldm[0] * celldm[2] * np.array([  0.0,   0.0,   1.0])
  elif ibrav_ in [-5, 5]:
    tx = np.sqrt((1 - celldm[3])/2.e0) 
    ty = np.sqrt((1 - celldm[3])/6.e0)
    tz = np.sqrt((1 + 2.e0 * celldm[3])/3.e0)
    if ibrav_ == 5:
      v1 = np.array([ tx,  -ty,    tz])
      v2 = np.array([  0, 2.e0*ty, tz])
      v3 = np.array([-tx,  -ty,    tz])
    else:
      u = tz - 2.e0 * np.sqrt(2.0) * ty 
      v = tz + np.sqrt(2.0) * ty 
      v1 = celldm[0] / np.sqrt(3.0) * np.array ([u, v, v])
      v2 = celldm[0] / np.sqrt(3.0) * np.array ([v, u, v])
      v3 = celldm[0] / np.sqrt(3.0) * np.array ([v, v, u]) 
  elif ibrav_ ==6:
    v1 = celldm[0] * np.array( [1.0, 0.0,     0.0  ])
    v2 = celldm[0] * np.array( [0.0, 1.0,     0.0  ])
    v3 = celldm[0] * np.array( [0.0, 0.0, celldm[2]])
  elif ibrav_ == 7:
    v1 = celldm[0] * 0.5 * np.array( [ 1.0, -1.0,   celldm[2] ])
    v2 = celldm[0] * 0.5 * np.array( [ 1.0,  1.0,   celldm[2] ])
    v3 = celldm[0] * 0.5 * np.array( [-1.0, -1.0,   celldm[2] ]) 
  elif ibrav_ in [8, 9, -9, 91, 10, 11 ]:
    c1 = celldm[0] * np.array([ 1.0,   0.0,         0.0    ])
    c2 = celldm[0] * np.array([ 0.0, celldm[1],     0.0    ])
    c3 = celldm[0] * np.array([ 0.0,   0.0,       celldm[2]])
    if ibrav_ ==8:
      v1 = c1 
      v2 = c2 
      v3 = c3 
    elif ibrav_ == 9:
      v1 = 0.5 * ( c1 + c2 )
      v2 = 0.5 * ( c2 - c1 )
      v3 = c3 
    elif ibrav_ == -9:
      v1 = 0.5 * ( c1 - c2 )
      v2 = 0.5 * ( c1 + c2 )
      v3 = c3 
    elif ibrav_ == 91:
      v1 = c1 
      v2 = 0.5 * ( c2 - c3 )
      v3 = 0.5 * ( c2 + c3 )
    elif ibrav_ == 10:
      v1 = 0.5 * ( c1 + c3 )
      v2 = 0.5 * ( c1 + c2 )
      v3 = 0.5 * ( c2 + c3 )
    elif ibrav_ == 11:
      v1 = 0.5 * ( c3 + c2 + c1 )
      v2 = 0.5 * ( c3 + c2 - c1)
      v3 = 0.5 * ( c3 - c2 - c1 )
  elif ibrav_ in [12, 13]:
    c = celldm[3]
    s = np.sqrt(1.0-c**2)
    c1 = celldm[0] *             np.array([ 1.0, 0.0, 0.0 ])
    c2 = celldm[0] * celldm[1] * np.array([  c,   s,  0.0 ])
    c3 = celldm[0] * celldm[2] * np.array([ 0.0, 0.0, 1.0 ])
    if ibrav_  == 12:
      v1 = c1 
      v2 = c2 
      v3 = c3
    elif ibrav_ == 13:
      v1 = 0.5 * ( c1 -c3 ) 
      v2 = c2 
      v3 = 0.5 * ( c1 + c3 )
  elif ibrav_ in  [-12, -13]:
    c = celldm[4]
    s = np.sqrt(1 - c**2)
    c1 = celldm[0] *             np.array([ 1.0, 0.0, 0.0 ])
    c2 = celldm[0] * celldm[1] * np.array([ 0.0, 1.0, 0.0 ])
    c3 = celldm[0] * celldm[2] * np.array([  c,  0.0,  s  ])
    if ibrav_ == -12: 
      v1 = c1 
      v2 = c2 
      v3 = c3
    elif ibrav_ == -13:
      v1 = 0.5 * ( c1 + c2 )
      v2 = 0.5 * ( c2 - c1 )
      v3 = c3
  elif ibrav_ == 14:
    v1 = celldm[0] * np.array([1.0, 0.0, 0.0 ])
    cab = celldm[5]
    sab = np.sqrt(1 - cab**2)
    v2 = celldm[0] * celldm[1] * np.array([ cab, sab, 0.0])
    cca = celldm[4]
    cbc = celldm[3]
    v3l = celldm[0] * celldm[2]
    v3x =  cca
    v3y = ( cbc -cca * cab) / sab 
    v3z =  np.sqrt( 1.0 - v3x**2 - v3y**2 )
    v3 = v3l * np.array ([ v3x, v3y, v3z ]) 
  else:
    logger.error("latgen: ibrav unknown")
  return np.array([v1, v2, v3]) 



def qe_ibrav(bravais_index, alt_axes = None):
  if bravais_index < 0 or bravais_index > 14:
    logger.error("wrong value for the bravais_index") 
  if bravais_index == 3:
    if alt_axes == "b:a-b+c:-c": 
      ibrav_ =  -3 
    else: 
      ibrav_ = 3 
  elif bravais_index == 5:
    if alt_axes == "3fold-111":
      ibrav_ =  -5 
    else:
      ibrav_ = 5
  elif bravais_index == 9:
    if alt_axes == "-b:a:c":
      ibrav_ = -9 
    elif alt_axes == "bcoA-type":
      ibrav_ = 91 
    else:
      ibrav_ = 9
  elif bravais_index == 12 or bravais_index == 13:
    if alt_axes == "unique-axis-b":
      ibrav_ = -bravais_index 
    else:
      ibrav_ = bravais_index
  else:
    ibrav_ = bravais_index
  return ibrav_ 

def at2celldm(at, ibrav_, alat_ = None):
  c1 = np.sqrt(at[0].dot(at[0]))
  c2 = None
  c3 = None
  c4 = None
  c5 = None
  c6 = None
  if ibrav_ == 0:
    if alat_:
      c1 = alat_ 
  elif ibrav_  == 2:
    c1 = c1 * np.sqrt(2.e0)
  elif ibrav_ == 3 or ibrav_ == -3:
    c1 = c1 / np.sqrt(3.e0)*2.e0  
  elif ibrav_ == 4 or ibrav_ == 6:
    c3 = np.sqrt(at[2].dot(at[2]))/c1
  elif ibrav_ == 5 or ibrav_ == -5:
    c4 = at[0].dot(at[1])/c1/np.sqrt(at[1].dot(at[1]))
  elif ibrav_ == 7:
    c1 = np.abs(at[0][0]) * 2.e0 
    c3 = np.abs(at[0][2]/at[0][0])
  elif ibrav_ == 8:
    c2 = np.sqrt(at[1].dot(at[1]))/c1 
    c3 = np.sqrt(at[2].dot(at[2]))/c1
  elif ibrav_ == 9 or ibrav_ == -9:
    c1 = np.abs(at[0][0]) * 2.e0
    c2 = np.abs(at[1][1]) * 2.e0 / c1 
    c3 = np.abs(at[2][2]) / c1 
  elif ibrav_ == 91:
    c2 = np.abs(at[1][1]) * 2.e0 / c1 
    c3 = np.abs(at[2][2]) * 2.e0 / c1 
  elif ibrav_ == 10:
    c1 = np.abs(at[0][0]) * 2.e0
    c2 = np.abs(at[1][1]) * 2.e0 / c1 
    c3 = np.abs(at[2][2]) * 2.e0 / c1
  elif ibrav_ == 11:
    c1 = np.abs(at[0][0]) * 2.e0
    c2 = np.abs(at[0][1]) * 2.e0 / c1 
    c3 = np.abs(at[0][2]) * 2.e0 / c1 
  elif ibrav_ == 12 or ibrav_ == -12:
    c2 = np.sqrt(at[1].dot(at[1])) / c1 
    c3 = np.sqrt(at[2].dot(at[2])) / c1
    if ibrav_  == 12:
      c4 = at[0].dot(at[1]) /c1 / c1 / c2 
    else: 
      c5 =  at[0].dot(at[2]) /c1 / c1 / c3
  elif ibrav_ == 13:
     c1 = np.abs(at[0][0]) * 2.e0 
     c2 = np.sqrt(at[1].dot(at[1])) / c1 
     c3 = np.abs(at[0][2]/at[0][0])
     c4 = at[1][0]/at[0][0] /c2 / 2.e0
  elif ibrav_ == -13:
    c1 = np.abs(at[0][0]) *2.e0 
    c2 = np.abs (at[1][1]/at[1][0])
    c3 = np.sqrt(at[2].dot(at[3]))/ c1 
    c5 = at[2][0]/ at[0][0]/ c3/ 2.e0
  elif ibrav_ == 14:
    c2 = np.sqrt(at[1].dot(at[1]))/c1 
    c3 = np.sqrt(at[2].dot(at[2]))/c1
    c4 = at[1].dot(at[2])/ c1 / c1 / c2 / c3
    c5 = at[0].dot(at[2])/ c1 / c1 / c3
    c6 = at[1].dot(at[0])/ c1 / c1 / c2 
  return (c1,c2,c3,c4,c5,c6)

def qe_abc2at(abc, ibrav_, abc_is_primitive = False):
  celldm_ =  abc2celldm(abc, ibrav_, abc_is_primitive)
  return latgen(celldm_, ibrav_)


def abc2celldm(abc, ibrav_, abc_is_primitive = False):
  c1 = angs2bohr(abc[0])
  c2 = abc[1]/abc[0]
  c3 = abc[2]/abc[0]
  triclic_lattices = [14, 0]
  unique_axis_b    = [-12, -13]
  unique_axis_c    = [-5, 5, 12, 13]
  if ibrav_ in triclic_lattices:
    c4 = abs[3]
    c5 = abs[4]
    c6 = abs[5]
  elif ibrav_ in unique_axis_b:
    c4 = 0.0
    c5 = abc[4]
    c6 = abc[5]
  elif ibrav_ in unique_axis_c:
    c4 = abc[3]
    c5 = 0.0 
    c6 = 0.0 
  else:
    c4 = 0.e0
    c5 = 0.e0
    c6 =0.e0 
  return (c1,c2,c3,c4,c5,c6) 

def celldm2abc(celldm, ibrav_, abc_is_primitive=False):
  at_ = latgen(celldm, ibrav_)
  orthorombic_lattices =[1, 2, 3, -3, 6, 7, 8, 9, -9, 91, 10] # all angles of conventional cell fixed to 90 degrees 
  triclic_lattices = [14, 0] #3 angles 
  unique_axis_b    = [-12, -13] # bc and ab == 90 degrees -- ca angle free 
  unique_axis_c    = [-5, 5, 12, 13, 4] # ca and bv == 90 degrees -- ab angle free (PI/3 for hexagonal case)

  if abc_is_primitive:
    a = np.sqrt(at_[0].dot(at_[0])) 
    b = np.sqrt(at_[1].dot(at_[1]))
    c = np.sqrt(at_[2].dot(at_[2]))
    cbc = at_[1].dot(at_[2])/ b/ c 
    cca = at_[2].dot(at_[0])/ c/ a 
    cab = at_[0].dot(at_[1])/ a/ b 
    a = bohr2angs(a)
    b = bohr2angs(b)
    c = bohr2angs(c)
  else:
    a = bohr2angs(celldm[0])
    b = a 
    c = a 
    if celldm[1]:
      b *= celldm[1] 
    if celldm[2]: 
      c *= celldm[2] 
    #
    if ibrav_ in triclic_lattices:
      cbc = celldm[3]
      cca = celldm[4]
      cab = celldm[5]
    elif ibrav_ in unique_axis_b:
      cbc = 0.e0
      cca = celldm[4]
      cab = 0.e0 
    elif ibrav_ in unique_axis_c:
      if celldm[3] != 0.e0:
        cab = celldm[3]
      else:
        cab = at_[0].dot(at_[1])/ (angs2bohr(a)**2) 
      cca = 0.e0
      cbc = 0.e0 
    elif ibrav_ in orthorombic_lattices: 
      cbc = 0.e0
      cca = 0.e0 
      cab = 0.e0
    else:
      logger.error("celldm2abc: unknown ibrav ")
  return (a,b,c,cbc, cca, cab)   
     
def qe_at2abc(at_, ibrav_, abc_is_primitive_ = False):
  celldm_ = at2celldm(at_, ibrav_)
  return celldm2abc(celldm_, ibrav_, abc_is_primitive_)



class lattice:
  def __init__(self, vectors = None, abc = None, abc_is_primitive = False, 
               bravais_index = None, alt_axes = None, celldm = None, alat_ = None):
    self.bravais_index = bravais_index
    self.alt_axes = alt_axes 
    self.cell  = self.__init_vectors(vectors, abc, abc_is_primitive, celldm)
    self.ibrav, self.celldm = self.get_ibrav_celldm() 
    abc_ = self.get_primitive_abc(abc, abc_is_primitive)
    self.primitive_abc = dict (zip(("a","b","c","cosBC","cosCA","cosAB"),abc_)) 
    abc_ = self.get_conventional_abc()
    self.conventional_abc = dict(zip(("a","b","c","cosBC","cosCA","cosAB"), abc_))
    self.alt_axes = alt_axes
    
  def __init_vectors(self, vectors = None, abc = None, abc_is_primitive = False, celldm = None):
    ibrav_ = qe_ibrav(self.bravais_index, self.alt_axes)
    if vectors:
      cellvec = np.asarray(vectors)
    elif abc:
      cellvec = qe_abc2at(abc, abc_is_primitive, ibrav_)
    elif celldm:
      cellvec = latgen(ibrav_, celldm)
    else:
      logger.error("lattice initialization failed")
    return cellvec 

  def get_ibrav_celldm(self, alat_ = None):
    ibrav_ = qe_ibrav(self.bravais_index, self.alt_axes)
    celldm = at2celldm(self.cell, ibrav_) 
    return ibrav_, celldm 
  
  def get_primitive_abc(self, abc = None, abc_is_primitive = False):
    if abc:
      if (np.round(self.cell - qe_abc2at(abc, self.ibrav, abc_is_primitive), 5) != 0.0).any(): 
          logger.error("abc parameters in input do not match with expected cell vectors")  
    a = round(np.sqrt(self.cell[0].dot(self.cell[0])),5) 
    b = round(np.sqrt(self.cell[1].dot(self.cell[1])),5)
    c = round(np.sqrt(self.cell[1].dot(self.cell[1])),5)
    bc = round(self.cell[1].dot(self.cell[2])/b/c, 5)   
    ca = round(self.cell[2].dot(self.cell[0])/c/a, 5)
    ab = round(self.cell[0].dot(self.cell[1])/a/b, 5)
    return a, b, c, bc, ca, ab

  def get_conventional_abc(self):
    abc = qe_at2abc(self.cell, self.ibrav)
    return abc 











