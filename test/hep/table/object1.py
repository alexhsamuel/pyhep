#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("x", "int16")
schema.addColumn("y", "int16")
table = hep.table.create("object1.table", schema)
table.append(x=10, y=20)
del table

table = hep.table.open("object1.table")
table.row_type = hep.table.RowObject
row = table[0]
compare(row._table, table)
del table
compare(row.x, 10)
compare(row.y, 20)
compare(row._index, 0)

row_dict = row.__dict__
compare(row_dict["x"], 10)
compare(row_dict["y"], 20)
compare(row_dict["_index"], 0)
