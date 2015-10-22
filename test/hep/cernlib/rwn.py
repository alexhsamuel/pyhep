#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.cernlib.hbook import create, createTable, open
from   random import random
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create a row-wise ntuple in an HBOOK file.
schema = hep.table.Schema()
schema.addColumn("index", "float32")
schema.addColumn("value", "float32")
hbook_file = create("rwn.hbook")
table = createTable("rwn", hbook_file, schema, column_wise=0)

# Fill it with random values, saving these in an array.
values = []
for i in xrange(0, 100):
    value = random()
    values.append(value)
    table.append(index=i, value=value)
del table, hbook_file

# Open the ntuple.
table = open("rwn.hbook")["rwn"]
assert_(not table.column_wise)
compare(len(table), 100)
# Compare the values in it to the array.
i = 0
for row in table:
    compare(row["index"], i)
    compare(row["_index"], i)
    compare(row["value"], values[i], precision=1e-7)
    i += 1
del row, table
