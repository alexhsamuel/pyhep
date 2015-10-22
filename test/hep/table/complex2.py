#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from   hep.test import compare
import hep.table
from   random import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create a new table.
schema = hep.table.Schema()
schema.addColumn("c", "complex128")
table = hep.table.create("complex1.table", schema)

# Fill in some rows.
values1 = []
values2 = []
for i in xrange(0, 1000):
    value = random() + random() * 1j
    table.append(c=value)
    if abs(value) > 1:
        values1.append(value)
    if value.real > 0.5 and value.imag < -0.5:
        values2.append(value)

# Write and close the table.
del schema, table

# Reopen the table.
table = hep.table.open("complex1.table")

# Check rows.
for row, value in zip(table.select("abs(c) > 1"), values1):
    compare(row["c"], value)
for row, value in zip(table.select("c.real > 0.5 and c.imag < -0.5"), values2):
    compare(row["c"], value)

