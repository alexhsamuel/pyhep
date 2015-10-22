#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram1D(10, (-10, 20))
compare(histogram.getBinRange("underflow"), ((None, -10), ))
compare(histogram.getBinRange(0),           ((-10,   -7), )) 
compare(histogram.getBinRange(1),           (( -7,   -4), )) 
compare(histogram.getBinRange(2),           (( -4,   -1), )) 
compare(histogram.getBinRange(3),           (( -1,    2), )) 
compare(histogram.getBinRange(4),           ((  2,    5), )) 
compare(histogram.getBinRange(5),           ((  5,    8), )) 
compare(histogram.getBinRange(6),           ((  8,   11), )) 
compare(histogram.getBinRange(7),           (( 11,   14), )) 
compare(histogram.getBinRange(8),           (( 14,   17), )) 
compare(histogram.getBinRange(9),           (( 17,   20), )) 
compare(histogram.getBinRange("overflow"),  (( 20, None), )) 

histogram = hep.hist.Histogram1D(10, (0.0, 2.0))
compare(histogram.getBinRange("underflow"), ((None, 0.0), ))
compare(histogram.getBinRange(0),           ((0.0,  0.2), )) 
compare(histogram.getBinRange(1),           ((0.2,  0.4), )) 
compare(histogram.getBinRange(2),           ((0.4,  0.6), )) 
compare(histogram.getBinRange(3),           ((0.6,  0.8), )) 
compare(histogram.getBinRange(4),           ((0.8,  1.0), )) 
compare(histogram.getBinRange(5),           ((1.0,  1.2), )) 
compare(histogram.getBinRange(6),           ((1.2,  1.4), )) 
compare(histogram.getBinRange(7),           ((1.4,  1.6), )) 
compare(histogram.getBinRange(8),           ((1.6,  1.8), )) 
compare(histogram.getBinRange(9),           ((1.8,  2.0), )) 
compare(histogram.getBinRange("overflow"),  ((2.0, None), )) 

