#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram
from   hep.cernlib import hbook
from   hep.test import compare
from   math import sqrt

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create and fill a histogram.
histogram = Histogram((10, (0.0, 10.0)),
                      (10, (-1.0, 1.0)),
                      bin_type=float)
for i in xrange(0, 100):
    for j in xrange(-10, 10):
        histogram << (sqrt(i), 0.1 * j + 0.05)
histogram.accumulate((-10, -10), 42.0)
histogram.accumulate((-10, 0.1), 17.5)
histogram.accumulate((0.5, 10), -4.0)
histogram.accumulate((-10, 10), 3.33)
# Write it to an HBOOK file.
hbook_file = hbook.create("binned2d.hbook")
hbook_file["testhist"] = histogram
del histogram, hbook_file

# Load the histogram back from the file.
hbook_file = hbook.open("binned2d.hbook")
histogram = hbook_file["testhist"]
# Check that it's configured correctly.
compare(histogram.dimensions, 2)
compare(histogram.bin_type, float)
compare(histogram.axes[0].number_of_bins, 10)
compare(histogram.axes[0].range, (0.0, 10.0))
compare(histogram.axes[0].type, float)
compare(histogram.axes[1].number_of_bins, 10)
compare(histogram.axes[1].range, (-1.0, 1.0))
compare(histogram.axes[1].type, float)
# Do some checks on the contents.
compare(histogram.number_of_samples, 2004)
total = 0
for i in xrange(0, 10):
    for j in xrange(0, 10):
        total += histogram.getBinContent((i, j))
compare(total, 2000)
compare(histogram.getBinContent(("underflow", "underflow")), 42.0)
compare(histogram.getBinContent(("underflow", 5)), 17.5)
compare(histogram.getBinContent((0, "overflow")), -4.0)
compare(histogram.getBinContent((1, "overflow")), 0)
compare(histogram.getBinContent(("underflow", "overflow")), 3.33, precision=1e-6)
compare(histogram.getBinContent(("overflow", "overflow")), 0)
