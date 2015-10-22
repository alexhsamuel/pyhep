import hep.root
import hep.hist
import hep.table 
from   random import random

# Construct a schema with three columns.
schema = hep.table.Schema(a="float32", b="float32", c="float32")

# Create a new Root file.
root_file = hep.fs.getdir("test.root", makedirs=True, writable=True)
# Create a tree in it.
table = hep.root.createTable("tree", root_file, schema, title="PyHEP test")
# Fill 100 random rows into the ntuple.
for i in xrange(0, 100):
    table.append(a=random(), b=random(), c=random())
# Release these to close the Root file.
del table, root_file

# Reopen the Root file.
root_file = hep.fs.getdir("test.root", writable=True)
# Get the table.
table = root_file["tree"]
# Project a histogram of the sum of the three values in each row.
histogram = hep.hist.Histogram1D(30, (0.0, 3.0), expression="a + b + c")
hep.hist.project(table.rows, (histogram, ))
# Write the histogram to the Root file.
root_file["histogram"] = histogram

