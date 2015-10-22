#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create a schema.
schema = hep.table.Schema(y="int16")
schema.addColumn("x", "float32")
schema["y"].description = "'y' must be an integer"

# Save it.
hep.table.saveSchema(schema, "schema2.xml")
del schema

# Reload it.
schema = hep.table.loadSchema("schema2.xml")

# Check it.
keys = schema.keys()
keys.sort()
compare(keys, ["x", "y"])
compare(schema["x"].type, "float32")
compare(schema["y"].type, "int16")
compare(schema["y"].description, "'y' must be an integer")

