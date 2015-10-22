#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.hist
from   hep.test import compare
import cPickle

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

# Create a histogram.
histogram = hep.hist.Histogram1D(
    10, (0, 100), "probability",
    bin_type=float, title="A Nice Histogram")
# Fill it.
map(histogram.accumulate,
    (30, 44, 108, 102, 37, -8, 106, 44, 25, 4, 20, -4, 5, 4, 16, 59, 23,
     98, 84, 110, 1, 102, 56, 71, 16, 16, 55, 40, 36, 104, 23, 36, 15,
     49, 103, 88, 29, -2, 47, -7, 45, 62, 82, 35, 61, -2, 11, -5, 81,
     86, 89, 72, 47, 32, 78, 106, 13, 30, 40, 35, 15, 62, 28, 79, -2,
     86, 88, 28, 72, 94, 56, 57, 6, 35, 94, 94, 27, 92, 16, 43, 36, 85,
     50, 28, 53, 54, 51, 32, 63, -8, 73, 52, 22, -6, 106, 76, -8, 22,
     94, 23, ))
# Remember the bin contents.
contents = [ (histogram.getBinContent(bin), histogram.getBinError(bin))
             for bin in hep.hist.AxesIterator(histogram.axes, True) ]
    
# Pickle it.
cPickle.dump(histogram, file("pickle1.pickle", "w"), 1)
del histogram

# Restore the pickle.
histogram = cPickle.load(file("pickle1.pickle"))

# Check it.
compare(histogram.axis.number_of_bins, 10)
compare(histogram.axis.range, (0, 100))
compare(histogram.axis.type, int)
compare(histogram.axis.name, "probability")
compare(histogram.bin_type, float)
compare(histogram.title, "A Nice Histogram")
compare(contents, 
        [ (histogram.getBinContent(bin), histogram.getBinError(bin))
          for bin in hep.hist.AxesIterator(histogram.axes, True) ])
