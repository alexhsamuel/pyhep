#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram((10, (0, 10)), bin_type=float)
hep.hist.fillBinValues(histogram, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

compare(hep.hist.integrate(histogram), 45)

normalized = hep.hist.normalize(histogram)
compare(list(hep.hist.BinValueIterator(normalized)),
        [0, 1/45, 2/45, 1/15, 4/45, 1/9, 2/15, 7/45, 8/45, 1/5],
        precision=1e-10)

