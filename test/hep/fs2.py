#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import *

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs2", {})

assert_(root_dir.is_empty)

root_dir["sample.txt"] = "Hello, world!"
root_dir.set("test.pickle", (10, 20, 30))
root_dir.set("subdir1/subdir2/test.pickle", (3.14, 2.718))

assert_(not root_dir.is_empty)
compareSequence(
    root_dir.keys(),
    ["sample.txt", "test.pickle", "subdir1"],
    ordered=False)
compare(len(root_dir), 3)
assert_(root_dir.has_key("sample.txt"))
assert_("test.pickle" in root_dir)
compareSequence(
    list(iter(root_dir)),
    ["sample.txt", "test.pickle", "subdir1"],
    ordered=False)

compare(root_dir["subdir1"].keys(), ["subdir2"])

compare(root_dir["subdir1/subdir2"].keys(), ["test.pickle"])

compareSequence(
    root_dir.keys(recursive=1),
    [ "sample.txt", "test.pickle", "subdir1",
      "subdir1/subdir2", "subdir1/subdir2/test.pickle" ],
    ordered=False)

compareSequence(
    root_dir.keys(recursive=1, not_dir=True),
    [ "sample.txt", "test.pickle", "subdir1/subdir2/test.pickle" ],
    ordered=False)

compareSequence(
    root_dir["subdir1"].keys(recursive=1),
    [ "subdir2/test.pickle", "subdir2" ],
    ordered=True)

del root_dir
cwd.delete("fs2", deldirs=True)
