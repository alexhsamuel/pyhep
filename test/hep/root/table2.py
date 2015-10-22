#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.root
import hep.table
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()

root_file = hep.root.create("table2.root")
bar = root_file.mkdir("foo/bar")
table = hep.root.createTable("table", bar, schema, title="A nice test.")
for i in xrange(0, 10):
    table.append()
del root_file, bar, table

# Make sure the table is in the right directory.
table = hep.root.open("table2.root")["foo/bar/table"]
# Make sure an empty schema is handled correctly.
compare(len(table.schema.columns), 0)
compare(len(table), 10)
# Make sure the name and title are restored correctly.
compare(table.name, "table")
compare(table.title, "A nice test.")
