#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from __future__ import division

from   hep.fn import enumerate
import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

h1 = hep.hist.Histogram1D(10, (0.0, 1.0))
for i, v in enumerate([  0,  1,  2,  6, -3,  5,  3,  2, 19,  4 ]):
    h1.setBinContent(i, v)

h2 = h1 * 2
for i, v in enumerate([  0,  2,  4, 12, -6, 10,  6,  4, 38,  8 ]):
    compare(h2.getBinContent(i), v)

h3 = -3 * h1
for i, v in enumerate([  0, -3, -6,-18,  9,-15, -9, -6,-57,-12 ]):
    compare(h3.getBinContent(i), v)

h4 = hep.hist.Histogram1D(10, (0, 1.0))
for i, v in enumerate([ 10,  8, -3,  5, -4, 12,  6, 11,  8, 14 ]):
    h4.setBinContent(i, v)

h5 = h1 + h4
for i, v in enumerate([ 10,  9, -1, 11, -7, 17,  9, 13, 27, 18 ]):
    compare(h5.getBinContent(i), v)

h6 = h4 - h2
for i, v in enumerate([ 10,  6, -7, -7,  2,  2,  0,  7,-30,  6 ]):
    compare(h6.getBinContent(i), v)

h7 = h4 / h1
for i, v in enumerate([ 0, 8, -1.5, 5/6, 4/3, 2.4, 2, 5.5, 8/19, 3.5 ]):
    compare(h7.getBinContent(i), v)

