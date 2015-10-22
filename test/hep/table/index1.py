#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
table = hep.table.create("index1.table", schema)
for i in range(10):
    table.append()
del table

table = hep.table.open("index1.table")
index_expr = table.compile("_index")

for i in range(9, -1, -1):
    row = table[i]
    compare(row["_index"], i)
    compare(index_expr.evaluate(row), i)
    
for row in table.select("_index % 3 == 1"):
    compare(row["_index"] % 3, 1)
