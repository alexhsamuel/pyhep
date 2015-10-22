#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.draw import postscript
from   hep.fn import enumerate
from   hep.hist import Histogram1D, Function1D
from   hep.hist import ezplot

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

data = Histogram1D(10, (0.0, 20.0), "energy", "GeV")
for i, v in enumerate((0, 0, 0, 0, 2, 5, 28, 32, 22, 10, )):
    data.setBinContent(i, v)
data.setBinContent("overflow", 2)

reference = Histogram1D(30, (0.0, 30.0), "energy", "GeV")
for i, v in enumerate(
    (0, 0, 0, 0, 0, 0, 1, 0, 1, 5, 13, 41, 100, 156, 177, 197, 148, 95,
     46, 16, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0)):
    reference.setBinContent(i, v)
reference *= 0.10

function1 = Function1D("100 * gaussian(15, 2, E)")
function2 = Function1D("95 * gaussian(14.8, 2.3, E)")

plot = ezplot.present1D(data, reference,
                        functions=(function1, function2),
                        # errors=True,
                        normalize_bin_size=1)
postscript.EPSFile("ezplot3.eps", (0.16, 0.10)).render(plot)
