#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep import test
import hep.expr
import hep.table

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Open the table.
table = hep.table.open("table3.table")

selection = hep.expr.parse("index % 4 == 3")
for row in table.select(selection):
    test.compare(row["_index"] % 4, 3)
