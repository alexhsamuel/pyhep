#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cernlib.minuit import minimize
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

fit_result = minimize("x**2 - x + 1", (("x", 0.0), ))
compare(fit_result.values["x"], 0.5, precision=1e-6)

fit_result = minimize("hypot(a - 1, b - 2)", (("a", 0.0), ("b", 0.0), ))
compare(fit_result.values["a"], 1.0, precision=1e-6)
compare(fit_result.values["b"], 2.0, precision=1e-6)

fit_result = minimize("x", (("x", 0, 0.1, 3, 4), ))
compare(fit_result.values["x"], 3.0, precision=1e-6)

fit_result = minimize("-x", (("x", 0, 0.1, 3, 4), ))
compare(fit_result.values["x"], 4.0, precision=1e-6)

