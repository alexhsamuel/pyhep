#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = Histogram((1, (0.0, 0.5)), (1, (0, 1)), bin_type=int)

compare(histogram.getBinContent(("underflow", "underflow")),    0)
compare(histogram.getBinContent((0          , "underflow")),    0)
compare(histogram.getBinContent(("overflow" , "underflow")),    0)
compare(histogram.getBinContent(("underflow", 0          )),    0)
compare(histogram.getBinContent((0          , 0          )),    0)
compare(histogram.getBinContent(("overflow" , 0          )),    0)
compare(histogram.getBinContent(("underflow", "overflow" )),    0)
compare(histogram.getBinContent((0          , "overflow" )),    0)
compare(histogram.getBinContent(("overflow" , "overflow" )),    0)

histogram.accumulate((-1, -1),    4)
histogram.accumulate(( 0, -1),    8)
histogram.accumulate(( 1, -1),   16)
histogram.accumulate((-1,  0),   32)
histogram.accumulate(( 0,  0),   64)
histogram.accumulate(( 1,  0),  128)
histogram.accumulate((-1,  1),  256)
histogram.accumulate(( 0,  1),  512)
histogram.accumulate(( 1,  1), 1024)

compare(histogram.getBinContent(("underflow", "underflow")),    4)
compare(histogram.getBinContent((0          , "underflow")),    8)
compare(histogram.getBinContent(("overflow" , "underflow")),   16)
compare(histogram.getBinContent(("underflow", 0          )),   32)
compare(histogram.getBinContent((0          , 0          )),   64)
compare(histogram.getBinContent(("overflow" , 0          )),  128)
compare(histogram.getBinContent(("underflow", "overflow" )),  256)
compare(histogram.getBinContent((0          , "overflow" )),  512)
compare(histogram.getBinContent(("overflow" , "overflow" )), 1024)
