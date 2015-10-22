#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *
import os.path

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

root_dir = hep.fs.getdir("fs8", makedirs=True)
root_dir.clear()

assert_(root_dir.parent.name == hep.fs.getcwd().name)
assert_(root_dir.writable)
assert_(root_dir.root.path == "/")

compare(root_dir.path, os.path.join(os.getcwd(), "fs8"))
compare(root_dir.join("foo"), os.path.join(root_dir.path, "foo"))

# Clean up.
del root_dir
hep.fs.getcwd().delete("fs8", deldirs=True)
