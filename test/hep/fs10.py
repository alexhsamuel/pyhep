#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
import hep.root
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getdir(".")

root_file = hep.root.create("fs10.root")
dir1 = root_file.mkdir("dir1")
dir2 = dir1.mkdir("dir2")
del root_file, dir1, dir2

root_file = cwd["fs10.root"]
compare(root_file.keys(), ["dir1"])
compare(root_file.keys(recursive=1), [ "dir1/dir2", "dir1" ])
del root_file

cwd.get("fs10.root/dir1/dir2", writable=True).mkdir("dir3")
compare(cwd["fs10.root"].keys(recursive=1),
        [ "dir1/dir2/dir3", "dir1/dir2", "dir1" ])

cwd.set("fs10.root", { "dir4": {} }, writable=1, replacedirs=1)
root_file = hep.root.open("fs10.root")
compare(root_file.keys(), [ "dir4" ])
