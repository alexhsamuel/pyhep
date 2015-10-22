#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs4", {})

root_dir["sample.txt"] = "Hello, world!"
root_dir.set("test.pickle", (10, 20, 30))
root_dir.set("subdir1/subdir2/test.pickle", (3.14, 2.718))
root_dir["subdir1/long.txt"] = """
This is a test.
A long file.
"""

del root_dir["subdir1/subdir2"]
compareSequence(root_dir["subdir1"].keys(), [ "long.txt" ])
try:
    root_dir.delete("subdir1", deldirs=False)
except RuntimeError:
    pass
else:
    raise TestFailure, "missing exception"

del root_dir["subdir1/long.txt"]
root_dir.delete("subdir1", deldirs=False)
compareSequence(
    root_dir.keys(),
    ["sample.txt", "test.pickle"],
    ordered=False)

remaining = ["sample.txt", "test.pickle"]
name, value = root_dir.popitem()
assert_(name in remaining)
remaining.remove(name)
compareSequence(root_dir.keys(), remaining)

root_dir.set("subdir3/test.txt", "some stuff")
root_dir.clear()
compare(root_dir.keys(), [])

# Clean up.
del root_dir
cwd.delete("fs4", deldirs=True)
