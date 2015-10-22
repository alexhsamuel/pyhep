#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.expr
import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create a schema.
schema = hep.table.Schema()
schema.note1 = 42
schema.addColumn("foo", "float32", note2="this is foo", note3=())
schema.note5 = ( 1, 2, 3 )

# Create a table.
table = hep.table.create("schema1.table", schema)

# Close up.
del table, schema

# Check it.
table = hep.table.open("schema1.table")
schema = table.schema
compare(schema.note1, 42)
col = schema["foo"]
compare(col.name, "foo")
compare(col.type, "float32")
compare(col.note2, "this is foo")
compare(col.note3, ())
