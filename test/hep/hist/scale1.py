#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram((10, (0, 10)))
map(histogram.accumulate,
    (1, 1, 2, 2, 2, 2, 4, 4, 6, 6, 6, 6, 6, 6, 8, 8, 9, 9, 9, 9))

scaled = hep.hist.scale(histogram, 0.5)
compare(list(hep.hist.BinValueIterator(scaled)),
        [0, 1, 2, 0, 1, 0, 3, 0, 1, 2])

scaled = hep.hist.scale(histogram, 1/3, bin_type=int)
compare(list(hep.hist.BinValueIterator(scaled)),
        [0, 0, 1, 0, 0, 0, 2, 0, 0, 1])

scaled = hep.hist.scale(histogram, 1/3)
compare(list(hep.hist.BinValueIterator(scaled)),
        [0, 2/3, 4/3, 0, 2/3, 0, 2, 0, 2/3, 4/3])

scaled = hep.hist.scale(histogram, 3)
compare(list(hep.hist.BinValueIterator(scaled)),
        [0, 6, 12, 0, 6, 0, 18, 0, 6, 12])

