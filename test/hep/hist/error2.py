#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.hist
from   hep.test import compare
from   math import sqrt

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram1D(
    10, (0.0, 1.0), bin_type=int, error_model="none")
histogram.setBinContent(4, 17)

compare(histogram.getBinError(0), (0., 0.))
compare(histogram.getBinError(4), (0., 0.))

#-----------------------------------------------------------------------

histogram = hep.hist.Histogram1D(
    10, (0.0, 1.0), bin_type=int, error_model="gaussian")
histogram.setBinContent(4, 17)

compare(histogram.getBinError(0), (0., 0.))
compare(histogram.getBinError(4), (sqrt(17), sqrt(17)))

