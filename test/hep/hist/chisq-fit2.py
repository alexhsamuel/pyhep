#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.expr
import hep.hist
import hep.hist.fit
from   hep.test import compare, assert_
from   math import sqrt
import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram1D(20, (0.0, 4.0), bin_type=float)
contents = [ 6.8, 5.8, 4.1, 5.1, 3.9, 4.8, 4.3, 4.5, 4.0, 5.1, 5.7, 5.9,
             7.0, 8.4, 9.4, 10.7, 12.4, 14.2, 15.7, 18.0 ]
for i in range(20):
    histogram.setBinContent(i, contents[i])

expr = hep.expr.parse("a * x ** 2 + b * x + c")
result = hep.hist.fit.chiSquareFit1D(
    histogram, expr, "x", (("a", 1), ("b", 1), ("c", 1), ))
print result

compare(result.minuit_status, 3)
assert_(result.minimum < 40)
# Despite the noise, the parameter values shouldn't be *too* far off.
compare(result.values["a"],  10, precision=1)
compare(result.values["b"], -25, precision=1)
compare(result.values["c"],  35, precision=1)
