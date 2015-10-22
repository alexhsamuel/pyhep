#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep import test
import hep.table

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Open the table, and get the first row.
table = hep.table.open("table3.table", row_type=hep.table.RowObject)

for row in table:
    test.compare(row._table, table)
    test.compare(row._index, row.index)
    test.compare(row.as_double, float(row.index))
    test.compare(row.twice, 2 * row.index)
    test.compare(row.cycle, (101 + 23 * row.index) % 17)
