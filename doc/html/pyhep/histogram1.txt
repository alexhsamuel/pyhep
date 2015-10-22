import hep.hist
import random

histogram = hep.hist.Histogram1D(11, (2, 13), "rolls", bin_type=int)
for count in xrange(0, 1000):
    roll = random.randint(1, 6) + random.randint(1, 6)
    histogram << roll

hep.hist.dump(histogram)
