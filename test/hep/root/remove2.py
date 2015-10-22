#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.root
from   hep.test import compare

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def ls(root_path, path):
    dir = hep.root.open(root_path)
    if path:
        dir = dir[path]
    keys = dir.keys()
    keys.sort()
    return keys


#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

root_file = hep.root.create("remove2.root")
root_file.mkdir("dir1")
root_file.mkdir("dir2")
root_file.mkdir("dir3")
root_file.mkdir("dir3/dir4")
del root_file

compare(ls("remove2.root", ""), ["dir1", "dir2", "dir3"])
compare(ls("remove2.root", "dir3"), ["dir4"])
del hep.root.open("remove2.root", writable=True)["dir2"]
compare(ls("remove2.root", ""), ["dir1", "dir3"])
compare(ls("remove2.root", "dir3"), ["dir4"])
del hep.root.open("remove2.root", writable=True)["dir3/dir4"]
compare(ls("remove2.root", ""), ["dir1", "dir3"])
compare(ls("remove2.root", "dir3"), [])
del hep.root.open("remove2.root", writable=True)["dir3"]
compare(ls("remove2.root", ""), ["dir1"])

#-----------------------------------------------------------------------
# PyHEP XFAIL
#
# OK, so here's the problem: A root.Directory object holds a reference
# to the containing root.File object.  A directory object also holds
# references to its subdirectories, but not to its parents, since that
# would be a reference loop.   Also, a file object cannot hold a
# refernece to its root directory or any other directory it contains.
#
# When a file is deleted, it causes problems with Root when the root
# directory is deleted before other directories.  This is hard to
# arrange.
#
# ??
#
#-----------------------------------------------------------------------
