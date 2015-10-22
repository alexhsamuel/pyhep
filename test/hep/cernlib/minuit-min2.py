#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cernlib.minuit import minimize
from   hep.test import compare
from   math import hypot

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

def function1(val):
    return val ** 2 - val + 1

fit_result = minimize(function1, ("val", ))
compare(fit_result.values["val"], 0.5, precision=1e-6)

def function2(a, b):
    return hypot(a - 1, b - 2)

fit_result = minimize(function2, (("b", 0.0), ("a", 0.0)))
compare(fit_result.values["a"], 1.0, precision=1e-6)
compare(fit_result.values["b"], 2.0, precision=1e-6)

