#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.table
from   random import random, randint
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

num_cols = 1000
num_rows = 1000

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
for i in xrange(0, num_cols):
    schema.addColumn("COL%d" % i, "float64")
table = hep.table.create("stress1.table", schema)
table_rows = []
for j in xrange(0, num_rows):
    row = {}
    values = []
    for i in xrange(0, num_cols):
        value = random()
        row["COL%d" % i] = value
        values.append(value)
    table.append(row)
    table_rows.append(values)
del row, values, table, schema

table = hep.table.open("stress1.table");
compare(len(table.schema), num_cols)
compare(len(table), num_rows)
for row in table:
    values = table_rows[row["_index"]]
    for i in xrange(0, num_cols):
        compare(row["COL%d" % i], values[i], precision=1e-8)

