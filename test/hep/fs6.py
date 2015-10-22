#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs6", {})
root_dir.clear()

root_dir.mkdir("subdir1")
try:
    root_dir.mkdir("subdir1")
except RuntimeError:
    pass
else:
    raise TestFailure, "missing exception"

root_dir["subdir1/test.txt"] = "foo"
compare(dict(root_dir.setdefault("subdir1", {})), { "test.txt": "foo" })
compare(dict(root_dir.setdefault("subdir2", {})), {})

try:
    root_dir["subdir1"] = {}
except RuntimeError:
    pass
else:
    raise TestFailure, "missing exception"
root_dir.set("subdir1", {}, replacedirs=True)
compare(len(root_dir["subdir1"]), 0)

root_dir["subdir3"] = { "test.pickle": "foo", "test.txt": "foo" }
compare(len(root_dir["subdir3"]), 2)

try:
    root_dir.set("subdir4/subdir5/test.txt", "foo", makedirs=False)
except KeyError:
    pass
else:
    raise TestFailure, "missing exception"
root_dir.set("subdir4/subdir5/test.txt", "foo")
compare(root_dir["subdir4"]["subdir5"]["test.txt"], "foo")

try:
    root_dir.set("subdir4/subdir5/test.txt", "bar", replace=False)
except RuntimeError:
    pass
else:
    raise TestFailure, "missing exception"
compare(root_dir["subdir4/subdir5/test.txt"], "foo")

subdir4 = root_dir["subdir4"]
subdir5 = subdir4["subdir5"]
compare(subdir5.replace, True)
subdir5.replace = False
try:
    subdir5["test.txt"] = "bar"
except RuntimeError:
    pass
else:
    raise TestFailure, "missing exception"
compare(root_dir["subdir4/subdir5/test.txt"], "foo")

subdir5.set("test.txt", "bar", replace=True)
compare(root_dir["subdir4/subdir5/test.txt"], "bar")

# Clean up.
del root_dir
cwd.delete("fs6", deldirs=True)
