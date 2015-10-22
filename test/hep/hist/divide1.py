#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram1 = hep.hist.Histogram((10, (0, 10)), bin_type=float)
hep.hist.fillBinValues(histogram1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
histogram2 = hep.hist.Histogram((10, (0, 10)), bin_type=float)
hep.hist.fillBinValues(histogram2, [1, 2, 3, 1, 2, 3, 1, 2, 3, 1])

quotient = hep.hist.divide(histogram1, histogram2)
compare(list(hep.hist.BinValueIterator(quotient)),
        [0, 1/2, 2/3, 3, 2, 5/3, 6, 7/2, 8/3, 9])

