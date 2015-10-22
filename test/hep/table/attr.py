#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep import test
import os

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create a new table.
schema = hep.table.Schema()
table = hep.table.create("attr.table", schema)
# Set some attributes.
table.int_attr = 42
table.str_attr = "Hello, world!"
table.tuple_attr = (1, -1, -1, -1)
# Write and close the table.
del table

# Open the table.
table = hep.table.open("attr.table")
# Check that the attributes were stored correctly.
test.compare(table.int_attr, 42)
test.compare(table.str_attr, "Hello, world!")
test.compare(table.tuple_attr, (1, -1, -1, -1))
# Close it.
del table

