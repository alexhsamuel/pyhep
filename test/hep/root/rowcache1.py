#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
import hep.root
from   hep.test import compare
from   random import randint

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

root_file = hep.root.create("rowcache1.root")
schema = hep.table.Schema()
schema.addColumn("x", "int32")
schema.addColumn("y", "int32")
table = hep.root.createTable("table", root_file, schema)
for i in range(100):
    table.append(x=i, y=i*i-1)
del schema, table, root_file

table = hep.root.open("rowcache1.root")["table"]
for i in range(0, 10000):
    index = randint(0, len(table) - 1)
    row = table[index]
    compare(row["x"], index)
    compare(row["y"], index**2 - 1)
