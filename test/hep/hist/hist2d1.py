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
x_axis = hep.hist.UnevenlyBinnedAxis([ 0, 0.2, 1 ])
y_axis = hep.hist.UnevenlyBinnedAxis([ 0, 0.5, 0.6, 1])
histogram = hep.hist.Histogram(x_axis, y_axis)
print histogram

for i in range(10):
    for j in range(10):
        histogram << (i / 10, j / 10)

# Test values.
compare(histogram.getBinContent((0, 0)), 10)
compare(histogram.getBinContent((1, 0)), 40)
compare(histogram.getBinContent((0, 1)),  2)
compare(histogram.getBinContent((1, 1)),  8)
compare(histogram.getBinContent((0, 2)),  8)
compare(histogram.getBinContent((1, 2)), 32)
