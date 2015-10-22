#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep import test
import hep.table

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Row(hep.table.RowObject):

    computed1 = property(lambda self: self.twice + self.index)

    computed2 = property(
        lambda self: self.computed1 / 2 - self.as_double / (3 - 1))



#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Open the table, and get the first row.
table = hep.table.open("table3.table", row_type=Row)
# Check it.
for row in table:
    test.compare(row.computed2, float(row._index))
