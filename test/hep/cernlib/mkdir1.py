#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.cernlib.hbook
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

hbook_file = hep.cernlib.hbook.create("mkdir1.hbook")

dir1 = hbook_file.mkdir("DIR1")
compare(dir1.path, "DIR1")

dir1 = hbook_file["DIR1"]
compare(dir1.path, "DIR1")

dir2 = dir1.mkdir("DIR2")
compare(dir2.path, "DIR1/DIR2")

dir2 = hbook_file["DIR1/DIR2"]
compare(dir2.path, "DIR1/DIR2")

dir3 = dir2.mkdir("DIR3")
compare(dir3.path, "DIR1/DIR2/DIR3")

compare(dir1.keys(), [ "DIR2" ])
compare(dir2.keys(), [ "DIR3" ])
