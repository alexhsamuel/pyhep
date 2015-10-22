#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram1 = hep.hist.Histogram((10, (0, 10)))
hep.hist.fillBinValues(histogram1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
histogram2 = hep.hist.Histogram((10, (0, 10)))
hep.hist.fillBinValues(histogram2, [1, 2, 3, 1, 2, 3, 1, 2, 3, 1])

sum = hep.hist.add(histogram1, histogram2)
compare(list(hep.hist.BinValueIterator(sum)),
        [1, 3, 5, 4, 6, 8, 7, 9, 11, 10])

    

