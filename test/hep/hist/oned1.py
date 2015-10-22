#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from   hep.hist import Histogram1D
from   hep.test import compare
from   math import sqrt

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

histogram = Histogram1D(10, (0.0, 1.0), "time", "sec",
                        bin_type=float, error_model="symmetric")
compare(histogram.axes[0], histogram.axis)
compare(histogram.axis.type, float)
compare(histogram.axis.range, (0.0, 1.0))
compare(histogram.axis.name, "time")
compare(histogram.axis.units, "sec")
compare(histogram.bin_type, float)
compare(histogram.axis.number_of_bins, 10)

histogram.accumulate(0.35)
histogram << 0.35
histogram << 0.35
histogram.accumulate(0.55, 4.5)
histogram.accumulate(0.55, -1)
histogram.setBinContent(9, -4.0)
histogram.setBinError(9, (1.0, 1.0))
histogram << -0.5
histogram.accumulate(100, 10)
compare(histogram.number_of_samples, 7)
compare(histogram.getBinContent(histogram.map(0.35)), 3.0)
compare(histogram.getBinContent(histogram.map(0.37)), 3.0)
compare(histogram.getBinContent(histogram.map(0.55)), 3.5)
contents = ( 0.0, 0.0, 0.0, 3.0, 0.0, 3.5, 0.0, 0.0, 0.0, -4.0, )
errors = ( 0.0, 0.0, 0.0, sqrt(3.0), 0.0, sqrt(21.25), 0.0, 0.0, 0.0, 1.0, )
for i in range(10):
    compare(histogram.getBinContent(i), contents[i])
    compare(histogram.getBinError(i), (errors[i], errors[i]))
compare(histogram.getBinContent("underflow"), 1.0)
compare(histogram.getBinError("underflow"), (1.0, 1.0))
compare(histogram.getBinContent("overflow"), 10.0)
compare(histogram.getBinError("overflow"), (10.0, 10.0))

# Make sure it also satisfies the N-dimensional protocol.
compare(histogram.map(( 0.35, )), ( 3, ))
compare(histogram.getBinContent([ 3 ]), 3.0)
compare(histogram.getBinError(( 4, )), (0.0, 0.0))
