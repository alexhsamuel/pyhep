#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("x", "int32")
table = hep.table.create("asdict1.table", schema)
for i in range(100):
    table.append(x=i)
del schema, table

table = hep.table.open("asdict1.table")
compare(dict(table[0]), { "x": 0 })
compare(dict(table[17]), { "x": 17 })
compare(dict(table[79]), { "x": 79 })
compare(dict(table[0]), { "x": 0 })
compare(dict(table[99]), { "x": 99 })
