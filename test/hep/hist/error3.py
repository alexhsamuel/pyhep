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
    10, (0.0, 1.0), bin_type=int, error_model="poisson")
histogram.setBinContent(4, 4)

compare(histogram.getBinError(0), (0.      , 1.1478745))
compare(histogram.getBinError(4), (2.2968057, 1.9818581))
