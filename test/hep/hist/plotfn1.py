#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.draw import postscript
from   hep.draw import xwindow
import hep.hist.function
import hep.hist.plot
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

fn = hep.hist.function.SampledFunction1D(
    (float, "test", None, (0, 4)))
for (x, y) in [ (0, 0), (1, 3), (2, 4), (3, 3), (4, 0) ]:
    fn.addSample(x, y)

plot = hep.hist.plot.Plot(1)
plot.append(fn)

postscript.EPSFile("plotfn1.eps", (0.20, 0.13)).render(plot)
window = xwindow.FigureWindow(plot)

if len(sys.argv) > 1:
    raw_input("hit enter to end> ")

