#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from __future__ import division

from   hep.fn import enumerate
from   hep.hist import Histogram, AxesIterator
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

h1 = Histogram((2, (0, 1.0)), (4, (-1, 1.0)))
for i, v in zip(AxesIterator(h1.axes), [  0,  1,  2,  6, -3,  5,  3,  2 ]):
    h1.setBinContent(i, v)

h2 = h1 * 2
for i, v in zip(AxesIterator(h2.axes), [  0,  2,  4, 12, -6, 10,  6,  4 ]):
    compare(h2.getBinContent(i), v)

h3 = -3 * h1
for i, v in zip(AxesIterator(h3.axes), [  0, -3, -6,-18,  9,-15, -9, -6 ]):
    compare(h3.getBinContent(i), v)

h4 = Histogram((2, (0.0, 1.0)), (4, (-1.0, 1.0)))
for i, v in zip(AxesIterator(h4.axes), [ 10,  8, -3,  5, -4, 12,  6, 11 ]):
    h4.setBinContent(i, v)

h5 = h1 + h4
for i, v in zip(AxesIterator(h5.axes), [ 10,  9, -1, 11, -7, 17,  9, 13 ]):
    compare(h5.getBinContent(i), v)

h6 = h4 - h2
for i, v in zip(AxesIterator(h6.axes), [ 10,  6, -7, -7,  2,  2,  0,  7 ]):
    compare(h6.getBinContent(i), v)

h7 = h4 / h1
for i, v in zip(AxesIterator(h6.axes), [ 0, 8, -1.5, 5/6, 4/3, 2.4, 2, 5.5 ]):
    compare(h7.getBinContent(i), v)

