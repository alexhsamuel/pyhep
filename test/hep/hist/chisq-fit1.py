#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.expr
import hep.hist
import hep.hist.fit
from   hep.test import compare, assert_
from   math import sqrt

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# CDF for PDF f(x) = 4 * x ** 2 - 3 * x + 15.
def cdf(x):
    return x ** 3 * 4 / 3 - x ** 2 * 3 / 2 + 15 * x


histogram = hep.hist.Histogram1D(20, (0.0, 4.0), bin_type=float)
for bin in hep.hist.AxisIterator(histogram.axis):
    x0, x1 = histogram.axis.getBinRange(bin)
    histogram.setBinContent(bin, cdf(x1) - cdf(x0))

expr = hep.expr.parse("a * x ** 2 + b * x + c")
result = hep.hist.fit.chiSquareFit1D(
    histogram, expr, "x", (("a", 1), ("b", 1), ("c", 1), ))
print result

compare(result.minuit_status, 3)
assert_(result.minimum / result.degrees_of_freedom < 1)
compare(result.values["a"],  4, precision=1e-6)
compare(result.values["b"], -3, precision=1e-6)
compare(result.values["c"], 15, precision=1e-6)

