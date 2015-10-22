#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram
import hep.ext
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = Histogram((1, (0, 1)), (1, (0.0, 1.0)), bin_type=int)
compare(histogram.axes[0].type, int)
compare(histogram.axes[1].type, float)
compare(histogram.bin_type, int)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram2D)

histogram = Histogram((1, (0.0, 1.0)), (1, (0, 1)), bin_type=float)
compare(histogram.axes[0].type, float)
compare(histogram.axes[1].type, int)
compare(histogram.bin_type, float)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram2D)

histogram = Histogram((1, (0, 1)), (1, (0, 1.)), bin_type=float)
compare(histogram.axes[0].type, int)
compare(histogram.axes[1].type, float)
compare(histogram.bin_type, float)
# Make sure the extension type is used.
compare(type(histogram), hep.ext.Histogram2D)

histogram = Histogram((1, (0l, 1)), (1, (0, 1)))
compare(histogram.axes[0].type, long)
compare(histogram.axes[1].type, int)
compare(histogram.bin_type, int)

histogram = Histogram((1, (0, 1)), (1, (0, 1)), bin_type=long)
compare(histogram.axes[0].type, int)
compare(histogram.axes[1].type, int)
compare(histogram.bin_type, long)
