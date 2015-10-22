#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram1D(
    10, (0.0, 1.0), bin_type=float, error_model="asymmetric")
histogram.setBinContent(0, 14)
histogram.setBinError(0, (3, 4))

compare(histogram.getBinContent(0), 14.)
compare(histogram.getBinError(0), (3., 4.))
compare(histogram.getBinContent(1), 0.)
compare(histogram.getBinError(2), (0., 0.))
        
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram(
    (10, (0., 1.)), (10, (0., 1.)), (10, (0., 1.)),
    bin_type=float, error_model="asymmetric")
histogram.setBinContent((0, 0, 0), 14)
histogram.setBinError((0, 0, 0), (3, 4))

compare(histogram.getBinContent((0, 0, 0)), 14.)
compare(histogram.getBinError((0, 0, 0)), (3., 4.))
compare(histogram.getBinContent((0, 0, 1)), 0.)
compare(histogram.getBinError((0, 1, 0)), (0., 0.))

