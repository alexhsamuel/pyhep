#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   hep.cernlib.hbook import create, createTable
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# HBOOK requires correct data alignment of columns.  If this is not
# handled correctly when the schema is used to book the CWN, a schema
# such as this one will cause problems, since the float64 columns are
# not 64-bit-aligned.

schema = hep.table.Schema()
schema.addColumn("index1", "int32")
schema.addColumn("value1", "float64")
schema.addColumn("index2", "int32")
schema.addColumn("value2", "float64")
schema.addColumn("index3", "int32")
schema.addColumn("value3", "float64")
schema.addColumn("index4", "int32")
schema.addColumn("value4", "float64")
schema.addColumn("index5", "int32")
schema.addColumn("value5", "float64")
schema.addColumn("index6", "int32")
schema.addColumn("value6", "float64")

hbook_file = create("cwn2.hbook")
table = createTable("cwn", hbook_file, schema, column_wise=1)
compare(len(table.schema), 12)
