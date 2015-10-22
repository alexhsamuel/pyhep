#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep import test
import os

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

number_of_rows = 1000

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

# Create a new table.
schema = hep.table.Schema()
schema.addColumn("index", "int32")
schema.addColumn("as_double", "float64")
schema.addColumn("twice", "int32")
schema.addColumn("cycle", "int32")
table = hep.table.create("table3.table", schema)

# Fill in some rows.
for i in xrange(0, number_of_rows):
    row = {
        "twice": 2 * i,
        "cycle": (101 + 23 * i) % 17,
        }
    table.append(row, index=i, as_double=i)

# Write and close the table.
del schema, row, table

# Open the table.
table = hep.table.open("table3.table")
# Check that the columns were restored correctly.
test.assert_(
    isinstance(table.schema["index"], hep.table.Column))
test.compare(table.schema["index"].Python_type, int)
test.compare(table.schema["as_double"].size, 8)
test.compare(table.schema["as_double"].Python_type, float)

# Check all rows.
for i in xrange(0, number_of_rows):
    row = table[i]
    test.compare(row["_table"], table)
    test.compare(row["_index"], i)
    test.compare(row["index"], i)
    test.compare(row["as_double"], float(i))
    test.compare(row["twice"], 2 * i)
    test.compare(row["cycle"], (101 + 23 * i) % 17)

# Check rows with a selection.
for row in table.select("cycle > 10"):
    test.assert_(row["cycle"] > 10)

# Test the protocol for the selection expression which is directly
# callable. 
def selection(cycle):
    return cycle > 10
# Check rows.
for row in table.select(selection):
    test.assert_(row["cycle"] > 10)

# Clean up.
del table
