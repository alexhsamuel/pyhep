#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import compare, TestFailure

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs3", {})

root_dir["sample.txt"] = "Hello, world!"
root_dir.set("test.pickle", (10, 20, 30))
root_dir.set("subdir1/subdir2/test.pickle", (3.14, 2.718))

root_dir["subdir1/long.txt"] = """
This is a test.
A long file.
"""

compare(root_dir["sample.txt"], "Hello, world!")
compare(root_dir.get("test.pickle"), (10, 20, 30))
subdir1 = root_dir["subdir1"]
compare(subdir1["subdir2/test.pickle"], (3.14, 2.718))

lines = subdir1.get("long.txt", by_line=True)
compare(lines.next(), "\n")
compare(lines.next(), "This is a test.\n")
compare(lines.next(), "A long file.\n")
try:
    lines.next()
except StopIteration:
    pass
else:
    raise TestFailure, "missing exception"

# Clean up.
del root_dir
cwd.delete("fs3", deldirs=True)
