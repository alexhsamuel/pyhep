#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

# Create the histogram.
axis = hep.hist.UnevenlyBinnedAxis(
    [0, .1, .2, .3, .4, .45, .5, .55, .6, .8, 1])
histogram = hep.hist.Histogram(axis)

for i in range(100):
    histogram << i / 100

# Test values.
compare(histogram.getBinContent("underflow"), 0)
compare(histogram.getBinContent(0), 10)
compare(histogram.getBinContent(1), 10)
compare(histogram.getBinContent(2), 10)
compare(histogram.getBinContent(3), 10)
compare(histogram.getBinContent(4),  5)
compare(histogram.getBinContent(5),  5)
compare(histogram.getBinContent(6),  5)
compare(histogram.getBinContent(7),  5)
compare(histogram.getBinContent(8), 20)
compare(histogram.getBinContent(9), 20)
compare(histogram.getBinContent("overflow"), 0)
