#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare, assert_
import os

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.description = "sample schema"
schema.addColumn("x", "float32", units="meters")

# Create a table without metadata.
table1 = hep.table.create(
    "metadata2-1.table", schema, with_metadata=False)
table1.notes = "more stuff"
table1.append(x=10)
del table1

# Create a table with metadata.
table2 = hep.table.create(
    "metadata2-2.table", schema, with_metadata=True)
table2.notes = "more stuff"
table2.append(x=12)
del table2

# Make sure no metadata file was written for the first table.
assert_(not os.path.isfile("metadata2-1.table.metadata"))

# Make sure no metadata attributes were recovered for the first table.
table = hep.table.open("metadata2-1.table", with_metadata=False)
assert_(not hasattr(table, "notes"))
assert_(not hasattr(table.schema, "description"))
assert_(not hasattr(table.schema["x"], "units"))
compare(len(table), 1)
compare(table[0]["x"], 10)
del table

# Open the second table without metadata, and make sure no metadata
# attributes were recovered.
table = hep.table.open("metadata2-2.table", with_metadata=False)
assert_(not hasattr(table, "notes"))
assert_(not hasattr(table.schema, "description"))
assert_(not hasattr(table.schema["x"], "units"))
compare(len(table), 1)
compare(table[0]["x"], 12)
del table

# Now open the second table with metadata, and make sure the metadata
# attributes were recoevered.
table = hep.table.open("metadata2-2.table")
compare(table.notes, "more stuff")
compare(table.schema.description, "sample schema")
compare(table.schema["x"].units, "meters")
compare(len(table), 1)
compare(table[0]["x"], 12)
del table

