#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.cernlib.hbook
import hep.hist
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create an HBOOK file.
root_dir = hep.cernlib.hbook.create("dir1.hbook")
# Create some directories in it.
dir1 = root_dir.mkdir("dir1")
dir2 = root_dir.mkdir("dir2")

# Check that we can get useful information about a directory.
assert_(root_dir.isdir("dir2"))
dir2_info = root_dir.getinfo("dir2")
compare(dir2_info.name, "dir2")
compare(dir2_info.type, "directory")

# Store a histogram.
dir1["hist1"] = hep.hist.Histogram1D(10, (0.0, 1.0))
compare(dir1.keys(), ["hist1"])
# Read it back and check it.
hist1 = root_dir["dir1/hist1"]
compare(hist1.dimensions, 1)
compare(hist1.axis.number_of_bins, 10)
compare(hist1.axis.range, (0.0, 1.0, ))

# Make a subdirectory.
compare(dir2.keys(), [])
dir3 = dir2.mkdir("dir3")
compare(dir2.keys(), ["dir3"])
# Store a histogram in it.
dir2["dir3/hist2"] = hep.hist.Histogram1D(20, (-0.5, 0.5))
# Read it back and check it.
hist2 = dir3["hist2"]
compare(hist2.dimensions, 1)
compare(hist2.axis.number_of_bins, 20)
compare(hist2.axis.range, (-0.5, 0.5, ))

# Delete the histogram.
del root_dir["dir2/dir3/hist2"]
compare(dir3.keys(), [])
