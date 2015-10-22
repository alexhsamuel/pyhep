#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.root
import hep.table

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

root_file = hep.root.create("dir1.root")
hep.root.createTable("table1", root_file, hep.table.Schema())
del root_file

try:
    for table in (hep.root.open("dir1.root")["table1"], ):
        del table
        raise IOError, 'foo'
        # PyHEP XFAIL
        # The table in the temporary list gets cleaned up when we unwind
        # out of the loop.  This seems to trigger some strange bug.
except IOError, e:
    print 'done'
    pass

