#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
import hep.cernlib.hbook
from   hep.test import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

cwd = hep.fs.getdir(".")

root_file = hep.cernlib.hbook.create("fs11.hbook")
dir1 = root_file.mkdir("dir1")
dir2 = dir1.mkdir("dir2")
del root_file, dir1, dir2

root_file = cwd["fs11.hbook"]
compare(root_file.keys(), ["dir1"])
compare(root_file.keys(recursive=1), [ "dir1/dir2", "dir1" ])
del root_file

cwd.get("fs11.hbook/dir1/dir2", writable=1).mkdir("dir3")
compare(cwd["fs11.hbook"].keys(recursive=1),
        [ "dir1/dir2/dir3", "dir1/dir2", "dir1" ])

cwd.set("fs11.hbook", { "dir4": {} }, writable=1, replacedirs=1)
root_file = hep.cernlib.hbook.open("fs11.hbook")
compare(root_file.keys(), [ "dir4" ])
