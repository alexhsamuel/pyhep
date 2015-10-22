#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import *
from   hep.test import compare
from   math import sqrt

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

contents = (
    ( 1,  2,  3,  4,  5),
    ( 6,  7,  8,  9, 10),
    (11, 12, 13, 14, 15),
    (16, 17, 18, 19, 20),
    )

# Create a 2D histogram.
histogram = Histogram((5, (0, 5)), (4, (0, 4)), error_model="symmetric")
for x in range(5):
    for y in range(4):
        histogram.setBinContent((x, y), contents[y][x])
        histogram.setBinError((x, y), sqrt(contents[y][x]))

# Slice the second column.
sl = slice(histogram, 0, (1, ))
compare(sl.axis.number_of_bins, 4)
compare(sl.axis.range, (0, 4))
compare(list(BinValueIterator(sl)), [ 2, 7, 12, 17 ])

# Sum and slice the first and fourth columns.
sl = slice(histogram, 0, (0, 3, ))
compare(sl.axis.number_of_bins, 4)
compare(sl.axis.range, (0, 4))
compare(list(BinValueIterator(sl)), [ 5, 15, 25, 35 ])

# Project out columns onto rows.
sl = slice(histogram, 0, "all")
compare(sl.axis.number_of_bins, 4)
compare(sl.axis.range, (0, 4))
compare(list(BinValueIterator(sl)), [ 15, 40, 65, 90 ])

# Slice the third row.
sl = slice(histogram, 1, (2, ))
compare(sl.axis.number_of_bins, 5)
compare(sl.axis.range, (0, 5))
compare(list(BinValueIterator(sl)), [ 11, 12, 13, 14, 15 ])

# Project out rows onto columns.
sl = slice(histogram, 1, "range")
compare(sl.axis.number_of_bins, 5)
compare(sl.axis.range, (0, 5))
compare(list(BinValueIterator(sl)), [ 34, 38, 42, 46, 50 ])

