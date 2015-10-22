#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.cernlib.minuit import minimize
from   hep.test import compare
from   math import hypot

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

def function(x, y, z):
    return (x - y + 1) ** 2 + (x - z + 2) ** 2 + (y + z) ** 2


fit_result = minimize(function, ("x", "y", "z"))
compare(fit_result.values["x"], -3/2, precision=1e-6)
compare(fit_result.values["y"], -1/2, precision=1e-6)
compare(fit_result.values["z"],  1/2, precision=1e-6)

fit_result = minimize(function, (("x", 4, None), "y", "z"))
compare(fit_result.values["x"],  4  , precision=1e-6)
compare(fit_result.values["y"],  4/3, precision=1e-6)
compare(fit_result.values["z"],  7/3, precision=1e-6)

fit_result = minimize(function, ("x", ("y", -1, None), "z"))
compare(fit_result.values["x"], -5/3, precision=1e-6)
compare(fit_result.values["y"], -1  , precision=1e-6)
compare(fit_result.values["z"],  2/3, precision=1e-6)

fit_result = minimize(function, ("x", ("y", 5, None), ("z", 6, None)))
compare(fit_result.values["x"],  4  , precision=1e-6)
compare(fit_result.values["y"],  5  , precision=1e-6)
compare(fit_result.values["z"],  6  , precision=1e-6)
