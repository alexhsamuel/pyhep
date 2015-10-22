#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs7", {})
root_dir.clear()

root_dir["subdir/test.txt"] = "foo"
assert_(root_dir.isdir("subdir"))
assert_(not root_dir.isdir("subdir/test.txt"))

info = root_dir.getinfo("subdir")
compare(info.type, "directory")
compare(info.name, "subdir")

info = root_dir.getinfo("subdir/test.txt")
compare(info.type, "text")
compare(info.name, "test.txt")
compare(info.file_size, 3)

# Clean up.
del root_dir
cwd.delete("fs7", deldirs=True)
