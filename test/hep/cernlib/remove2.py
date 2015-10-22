#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
from   hep.cernlib import hbook
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

hbook_file = hbook.create("remove2.hbook")
hbook_file.mkdir("dir1")
hbook_file.mkdir("dir2")
hbook_file.mkdir("dir3")
hbook_file.mkdir("dir3/dir4")
del hbook_file

def ls(hbook_path, path):
    keys = hbook.open(hbook_path)[path].keys()
    keys.sort()
    return keys


compare(ls("remove2.hbook", ""), ["dir1", "dir2", "dir3"])
compare(ls("remove2.hbook", "dir3"), ["dir4"])
del hbook.open("remove2.hbook", writable=True)["dir2"]
compare(ls("remove2.hbook", ""), ["dir1", "dir3"])
compare(ls("remove2.hbook", "dir3"), ["dir4"])
del hbook.open("remove2.hbook", writable=True)["dir3/dir4"]
compare(ls("remove2.hbook", ""), ["dir1", "dir3"])
compare(ls("remove2.hbook", "dir3"), [])
