#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.fs
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

cwd = hep.fs.getcwd()
root_dir = cwd.setdefault("fs1", {})
compare(root_dir.keys(), [])
compare(len(root_dir), 0)
compare(list(iter(root_dir)), [])

del root_dir
cwd.delete("fs1", deldirs=True)
