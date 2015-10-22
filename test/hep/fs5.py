#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs5", {})

root_dir["sample.txt"] = "Hello, world!"
root_dir.set("test.pickle", (10, 20, 30))
root_dir.set("subdir1/subdir2/test.pickle", (3.14, 2.718))

compareSequence(
    root_dir.values(not_dir=True),
    [ "Hello, world!", (10, 20, 30) ],
    ordered=False)

compareSequence(
    root_dir.values(not_dir=True, recursive=True),
    [ "Hello, world!", (10, 20, 30), (3.14, 2.718) ],
    ordered=False)

compareSequence(
    root_dir.items(not_dir=True, recursive=True),
    [ ("sample.txt", "Hello, world!"),
      ("test.pickle", (10, 20, 30)),
      ("subdir1/subdir2/test.pickle", (3.14, 2.718)) ],
    ordered=False)

compareSequence(
    list(root_dir.iterkeys(recursive=True)),
    [ "sample.txt", "test.pickle", "subdir1", "subdir1/subdir2",
      "subdir1/subdir2/test.pickle" ],
    ordered=False)

compareSequence(
    list(root_dir.itervalues(not_dir=True, recursive=True)),
    [ "Hello, world!", (10, 20, 30), (3.14, 2.718) ],
    ordered=False)

compareSequence(
    list(root_dir.items(not_dir=True, recursive=True)),
    [ ("sample.txt", "Hello, world!"),
      ("test.pickle", (10, 20, 30)),
      ("subdir1/subdir2/test.pickle", (3.14, 2.718)) ],
    ordered=False)

# Clean up.
del root_dir
cwd.delete("fs5", deldirs=True)
