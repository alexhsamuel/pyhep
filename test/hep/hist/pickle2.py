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
histogram = hep.hist.Histogram(
    (2, (0.0, 10.0), "energy", "GeV/c^2"),
    (4, (0, 40), "hits"),
    bin_type=float,
    title="A Nice Histogram")
# Fill it.
map(histogram.accumulate,
    [ ( 6.06, 38), ( 6.57, 20), (10.04,  5), ( 8.21,  3), ( 3.52, 22),
      ( 2.32, 22), ( 1.79,  2), (10.64, 15), (10.11, 44), ( 9.07, 30),
      ( 7.30, 43), ( 8.31, 35), ( 0.66, 27), ( 0.12, 44), ( 3.96, 32),
      ( 7.99, 18), ( 8.86, 20), ( 3.49, 37), ( 8.68, 24), ( 8.97, 16),
      ( 5.62, 10), ( 3.47,  9), ( 0.44, -3), ( 5.96, -1), ( 6.07, 15),
      ( 2.53,  0), ( 4.29,  5), ( 8.57, 36), ( 3.09, 10), ( 7.67, 26),
      ( 7.84,  0), ( 4.80,  0), (-0.88,  1), ( 0.63, 38), ( 7.69,  0),
      ( 2.12,  1), (10.83, -1), ( 3.23, 27), ( 0.52, -3), ( 5.16, 14) ])
# Remember the bin contents.
contents = [ (histogram.getBinContent(bin), histogram.getBinError(bin))
             for bin in hep.hist.AxesIterator(histogram.axes, True) ]
    
# Pickle it.
cPickle.dump(histogram, file("pickle2.pickle", "w"), 1)
del histogram

# Restore the pickle.
histogram = cPickle.load(file("pickle2.pickle"))

# Check it.
compare(histogram.axes[0].number_of_bins, 2)
compare(histogram.axes[0].range, (0.0, 10.0))
compare(histogram.axes[0].type, float)
compare(histogram.axes[0].name, "energy")
compare(histogram.axes[0].units, "GeV/c^2")
compare(histogram.axes[1].number_of_bins, 4)
compare(histogram.axes[1].range, (0, 40))
compare(histogram.axes[1].type, int)
compare(histogram.axes[1].name, "hits")
compare(histogram.bin_type, float)
compare(histogram.title, "A Nice Histogram")
compare(contents, 
        [ (histogram.getBinContent(bin), histogram.getBinError(bin))
          for bin in hep.hist.AxesIterator(histogram.axes, True) ])
