from   hep.cernlib import hbook
import hep.fs
import hep.hist
import hep.table 
from   random import random

# Construct a schema with three columns.
schema = hep.table.Schema(a="float32", b="float32", c="float32")
# Create a new HBOOK file.
hbook_file = hep.fs.getdir("test.hbook", makedirs=True, writable=True)
# Create a row-wise n-tuple in it.
table = hbook.createTable("ntuple", hbook_file, schema, column_wise=False)
# Fill 100 random rows into the ntuple.
for i in xrange(0, 100):
    table.append(a=random(), b=random(), c=random())
# Release these to close the HBOOK file.
del table, hbook_file

# Reopen the HBOOK file.
hbook_file = hep.fs.getdir("test.hbook", writable=True)
# Get the n-tuple.
table = hbook_file["ntuple"]
# Project a histogram of the sum of the three values in each row.
histogram = hep.hist.Histogram1D(30, (0.0, 3.0), expression="a + b + c")
hep.hist.project(table.rows, (histogram, ))
# Write the histogram to the HBOOK file.
hbook_file["histogram"] = histogram

