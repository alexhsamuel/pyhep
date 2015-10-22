#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare
from   random import randint

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("x", "int32")
schema.addColumn("y", "int32")
table = hep.table.create("rowcache1.table", schema)
for i in range(100):
    table.append(x=i, y=i*i-1)
del schema, table

table = hep.table.open("rowcache1.table")
index = 0
for i in range(0, 10000):
    index = min(max(index + randint(0, 2) - 1, 0), 99)
    row = table[index]
    compare(row["x"], index)
    compare(row["y"], index**2 - 1)
    del row

