#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("count", "int16", title="number of grapefruits")
schema.addColumn("length", "float32", units="meters")
schema.name = "sample schema"

table = hep.table.create("metadata1.table", schema)
table.append(count=10, length=0.65)

del table, schema

#-----------------------------------------------------------------------

table = hep.table.open("metadata1.table")
schema = table.schema
print schema

compare(len(schema), 2)
compare(schema["count"].title, "number of grapefruits")
compare(schema["length"].units, "meters")
compare(schema.name, "sample schema")
compare(len(table), 1)

del table, schema

#-----------------------------------------------------------------------

# Overwrite the table with another by the same name but a different
# schema, to make sure the old metadata file gets clobbered and doesn't
# conflict with the new table.

schema = hep.table.Schema()
schema.addColumn("x", "int32", title="stuff")
schema.name = "sample schema"

table = hep.table.create("metadata1.table", schema)
table.append(x=42)
table.append(x=39)

del table, schema

#-----------------------------------------------------------------------

table = hep.table.open("metadata1.table")
schema = table.schema
print schema

compare(len(schema), 1)
compare(schema["x"].title, "stuff")
compare(len(table), 2)

del table, schema

