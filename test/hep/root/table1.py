#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.root
import hep.table
from   random import random
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("index", "int32")
schema.addColumn("value32", "float32")
schema.addColumn("value64", "float64")

root_file = hep.root.create("table1.root")
table = hep.root.createTable("table", root_file, schema)
values = []
for i in xrange(0, 100):
    value = random()
    values.append(value)
    table.append(index=i, value32=value, value64=value)
del root_file, table

table = hep.root.open("table1.root")["table"]
compare(len(table), 100)
i = 0
for row in table.rows:
    compare(row["index"], i)
    compare(row["value32"], values[i], precision=1e-6)
    compare(row["value64"], values[i], precision=1e-9)
    i += 1

