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
schema.addColumn("index", "int32")
schema.addColumn("value32", "float32")
schema.addColumn("value64", "float64")
hbook_file = create("cwn1.hbook")
table = createTable("cwn", hbook_file, schema, column_wise=1)

# Fill it with random values, saving these in an array.
values = []
for i in xrange(0, 100):
    value = random()
    values.append(value)
    table.append(index=i, value32=value, value64=value)
del table, hbook_file

# Open the ntuple.
table = open("cwn1.hbook")["cwn"]
assert_(table.column_wise)
compare(len(table), 100)
# Compare the values in it to the array.
i = 0
for row in table:
    compare(row["index"], i)
    compare(row["value32"], values[i], precision=1e-6)
    compare(row["value64"], values[i], precision=1e-9)
    i += 1
del row, table

