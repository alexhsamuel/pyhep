#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import compare
import hep.root
import hep.table 

#-----------------------------------------------------------------------
# clean up
#-----------------------------------------------------------------------

cwd = hep.fs.getdir(".", writable=True)
if "replace1.root" in cwd:
    del cwd["replace1.root"]

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Construct a schema with three columns.
schema = hep.table.Schema(a="float32", b="float32", c="float32")

# Create a new Root file.
root_file = hep.fs.getdir("replace1.root", makedirs=True, writable=True)
# Create a tree in it.
table = hep.root.createTable("tree", root_file, schema, title="PyHEP test")
# Fill a row into the ntuple.
table.append(a=1, b=2, c=3)
table.append(a=4, b=5, c=6)
# Release these to close the Root file.
del table, root_file

# Recreate the Root file.
root_file = hep.fs.getdir("replace1.root", makedirs=True, writable=True)
# Get the table.
table = root_file["tree"]
# Fill a row into the ntuple.
table.append(a=7, b=8, c=9)
# Release these to close the Root file.
del table, root_file

# Reopen the Root file.
root_file = hep.fs.getdir("replace1.root")
# Get the table.
table = root_file["tree"]
# Make sure both rows are there.
compare(len(table), 1)
compare(table[0]["a"], 7)
# Release these to close the Root file.
del table, root_file

