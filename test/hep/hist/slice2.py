#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import *
from   hep.test import compare
from   math import sqrt

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

# Create a 3D histogram.
histogram = Histogram((3, (0, 3), "count A"),
                      (4, (0, 4), "count B"),
                      (5, (0, 5), "count C"),
                      title="Sample Histogram")
histogram << (1, 2, 3)
histogram << (2, 3, 4)

sl = slice(histogram, 0, (1, ))
# print sl.title
compare(sl.dimensions, 2)
compare(sl.axes[0].number_of_bins, 4)
compare(sl.axes[0].range, (0, 4))
compare(sl.axes[1].number_of_bins, 5)
compare(sl.axes[1].range, (0, 5))
compare(sl.getBinContent((2, 3)), 1)
compare(sl.getBinContent((3, 4)), 0)

sl = slice(histogram, 1, (2, ))
# print sl.title
compare(sl.dimensions, 2)
compare(sl.axes[0].number_of_bins, 3)
compare(sl.axes[0].range, (0, 3))
compare(sl.axes[1].number_of_bins, 5)
compare(sl.axes[1].range, (0, 5))
compare(sl.getBinContent((1, 3)), 1)
compare(sl.getBinContent((2, 4)), 0)

sl = slice(histogram, 2)
# print sl.title
compare(sl.dimensions, 2)
compare(sl.axes[0].number_of_bins, 3)
compare(sl.axes[0].range, (0, 3))
compare(sl.axes[1].number_of_bins, 4)
compare(sl.axes[1].range, (0, 4))
compare(sl.getBinContent((1, 2)), 1)
compare(sl.getBinContent((2, 3)), 1)
compare(sl.getBinContent((1, 3)), 0)

sl = slice(slice(histogram, 0), 0)
compare(sl.dimensions, 1)
compare(sl.axis.number_of_bins, 5)
compare(sl.axis.range, (0, 5))
compare(list(BinValueIterator(sl)), [ 0, 0, 0, 1, 1 ])

