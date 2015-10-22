#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram, Histogram1D
import hep.ext
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = Histogram1D(1, (0, 1), bin_type=int)
compare(histogram.axis.type, int)
compare(histogram.bin_type, int)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram1D)

histogram = Histogram1D(1, (0.0, 1), bin_type=float)
compare(histogram.axis.type, float)
compare(histogram.bin_type, float)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram1D)

histogram = Histogram((1, (0, 1)), bin_type=float)
compare(histogram.axis.type, int)
compare(histogram.bin_type, float)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram1D)

histogram = Histogram((1, (0, 1.0)))
compare(histogram.axis.type, float)
compare(histogram.bin_type, int)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram1D)

histogram = Histogram1D(1, (0, 1l))
compare(histogram.axis.type, long)
compare(histogram.bin_type, int)

