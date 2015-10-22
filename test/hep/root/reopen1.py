#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
import hep.root
import hep.hist
import hep.table 
from   hep.test import compare

#-----------------------------------------------------------------------
# clean up
#-----------------------------------------------------------------------

cwd = hep.fs.getdir(".", writable=True)
if "reopen1.root" in cwd:
    del cwd["reopen1.root"]

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Construct a schema with three columns.
schema = hep.table.Schema(a="float32", b="float32")

# Create a new Root file.
root_file = hep.fs.getdir("reopen1.root", makedirs=True, writable=True)
# Create a tree in it.
table = hep.root.createTable("tree", root_file, schema, title="PyHEP test")
# Fill 100 random rows into the ntuple.
table.append(a=1, b=2)
# Release these to close the Root file.
del table, root_file

# Reopen the Root file.
root_file = hep.fs.getdir("reopen1.root", writable=True)
# Get the table.
table = root_file["tree"]
# Fill a row into the ntuple.
table.append(a=4, b=5)
# Release these to close the Root file.
del table, root_file

# Reopen the Root file.
root_file = hep.fs.getdir("reopen1.root")
# Get the table.
table = root_file["tree"]
# Make sure both rows are there.
compare(len(table), 2)
compare(table[0]["a"], 1)
compare(table[1]["b"], 5)
# Release these to close the Root file.
del table, root_file

