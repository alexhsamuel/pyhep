#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
from   hep.hist import Histogram1D
import hep.root
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

root_file = hep.root.create("remove1.root")
root_file.mkdir("dir1")
root_file.mkdir("dir2")
histograms = [ Histogram1D(10, (0., 1.)) for i in range(0, 4) ]
root_file["hist0"] = histograms[0]
root_file["hist1"] = histograms[1]
root_file["dir1/hist2"] = histograms[2]
root_file["dir2/hist3"] = histograms[3]
del root_file, histograms

del hep.root.open("remove1.root", writable=True)["hist1"]

root_file = hep.root.open("remove1.root")
compare(len(root_file), 3)
compare(root_file["dir1"].keys(), ["hist2"])
compare(root_file["dir2"].keys(), ["hist3"])
del root_file

del hep.root.open("remove1.root", writable=True)["dir2/hist3"]

root_file = hep.root.open("remove1.root")
compare(len(root_file), 3)
compare(root_file["dir1"].keys(), ["hist2"])
compare(root_file["dir2"].keys(), [])
del root_file

