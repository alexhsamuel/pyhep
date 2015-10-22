#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram1D
import hep.root
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create and fill a histogram.
histogram = Histogram1D(100, (0.0, 100.0), bin_type=float)
for i in xrange(0, 50):
    for j in xrange(0, 50):
        histogram << (i + j)
histogram.accumulate(-1, 42.0)
histogram.accumulate(110, 17.5)
# Write it to an ROOT file.
hep.root.create("binned1d.root")["testhist"] = histogram

# Load the histogram back from the file.
histogram = hep.root.open("binned1d.root")["testhist"]
# Check that it's configured correctly.
compare(histogram.dimensions, 1)
compare(histogram.bin_type, float)
compare(histogram.axes[0].number_of_bins, 100)
compare(histogram.axes[0].range, (0.0, 100.0))
compare(histogram.axes[0].type, float)
# Do some checks on the contents.
compare(histogram.number_of_samples, 2502)
total = 0
for i in range(0, histogram.axis.number_of_bins):
    total += histogram.getBinContent(i)
compare(total, 2500)
compare(histogram.getBinContent("underflow"), 42.0)
compare(histogram.getBinContent("overflow"), 17.5)

