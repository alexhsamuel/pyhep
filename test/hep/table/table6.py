#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep import test
import hep.table

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Row(hep.table.RowObject):

    computed = property(lambda self: self.twice + self.index)

    

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Open the table, and get the first row.
table = hep.table.open("table3.table", row_type=Row)

# Check it.
for row in table:
    test.compare(row.computed, 3 * row.index)
    test.compare(row.computed, 3 * row._index)
        
