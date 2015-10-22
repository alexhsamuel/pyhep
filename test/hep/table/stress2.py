#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.fn import enumerate
import hep.table
from   hep.test import compare
import os
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

table_path = "/mnt/work/samuel/stress1.table"

schema = hep.table.Schema()
for i in xrange(1024):
    schema.addColumn("col%03x" % i, "int32")

table = hep.table.create(table_path, schema)

row = dict([ ("col%03x" % i, i) for i in xrange(1024) ])

for i in xrange(600000):
    row["col000"] = i
    row["col001"] = 2 * i + 1
    table.append(row)
    
del row, table, schema

#-----------------------------------------------------------------------

table = hep.table.open(table_path)

for index, row in enumerate(table):
    if index % 10000 == 0:
        sys.stdout.write("\r%d" % index)
        sys.stdout.flush()
    compare(row["_index"], index)
    compare(row["col000"], index)
    compare(row["col001"], 2 * index + 1)
    compare(row["col1ec"], 492)

sys.stdout.write("\n")

del row, table

#-----------------------------------------------------------------------

os.unlink(table_path)
