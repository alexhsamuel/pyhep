#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
from   hep.cernlib import hbook
from   hep.hist import Histogram1D
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

hbook_file = hbook.create("remove1.hbook")
hbook_file.mkdir("dir1")
hbook_file.mkdir("dir2")
histograms = [ Histogram1D(10, (0., 1.)) for i in range(0, 4) ]
hbook_file.set("hist0", histograms[0], rz_id=100)
hbook_file.set("hist1", histograms[1], rz_id=101)
hbook_file.set("dir1/hist2", histograms[2], rz_id=100)
hbook_file.set("dir2/hist3", histograms[3], rz_id=100)

del hbook_file, histograms

del hbook.open("remove1.hbook", writable=True)["hist1"]

hbook_file = hbook.open("remove1.hbook")
compare(len(hbook_file.keys()), 3)
compare(hbook_file["dir1"].keys(), ["hist2"])
compare(hbook_file["dir2"].keys(), ["hist3"])
del hbook_file

del hbook.open("remove1.hbook", writable=True)["dir2/hist3"]

hbook_file = hbook.open("remove1.hbook")
compare(len(hbook_file.keys()), 3)
compare(hbook_file["dir1"].keys(), ["hist2"])
compare(hbook_file["dir2"].keys(), [])
del hbook_file

