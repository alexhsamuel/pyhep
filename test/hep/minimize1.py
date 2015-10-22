#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.minimize
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

def function(x, y, z):
    return (x - y + 1) ** 2 + (x - z + 2) ** 2 + (y + z) ** 2


parameters, best_value = hep.minimize.gridMinimize(
    function,
    ("x", 41, -2., 2.),
    ("y", 41, -2., 2.),
    ("z", 41, -2., 2.))
compare(parameters["x"], -3/2, precision=1e-1)
compare(parameters["y"], -1/2, precision=1e-1)
compare(parameters["z"],  1/2, precision=1e-1)


parameters, best_value = hep.minimize.gridMinimize(
    function,
    ("y", 61, -3., 3.),
    ("z", 61, -3., 3.),
    x=4.)
compare(parameters["x"],  4  , precision=1e-1)
compare(parameters["y"],  4/3, precision=1e-1)
compare(parameters["z"],  7/3, precision=1e-1)

