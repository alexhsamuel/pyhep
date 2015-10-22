#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

root_dir = hep.fs.getdir("fs9", makedirs=True)
root_dir.clear()

for name in [
    "test1.txt",
    "test2.pickle",
    "subdir3/test4.txt",
    "subdir3/test5.txt",
    "subdir6/subdir7/test8.pickle",
    "other9.txt",
    ]:
    root_dir[name] = "foo"

compareSequence(
    root_dir.keys(glob="*.txt"),
    [ "test1.txt", "other9.txt" ],
    ordered=False)

compareSequence(
    root_dir.keys(glob="test*", recursive=1),
    [ "test1.txt", "test2.pickle", "subdir3/test4.txt",
      "subdir3/test5.txt", "subdir6/subdir7/test8.pickle" ],
    ordered=False)

compareSequence(
    root_dir.keys(only_type="pickle", recursive=1),
    [ "test2.pickle", "subdir6/subdir7/test8.pickle" ],
    ordered=False)

compareSequence(
    root_dir.keys(pattern="t..t[28]|o.*9|test4$", recursive=1),
    [ "test2.pickle", "subdir6/subdir7/test8.pickle",
      "other9.txt" ],
    ordered=False)

# Clean up.
del root_dir
hep.fs.getcwd().delete("fs9", deldirs=True)
