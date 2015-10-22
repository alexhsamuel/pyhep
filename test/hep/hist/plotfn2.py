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

fn = hep.hist.function.Function1D("sin(x) / x")

plot = hep.hist.plot.Plot(1, x_axis_range=(-12, 12), overflows=False)
plot.append(fn)

postscript.EPSFile("plotfn2.eps", (0.20, 0.13)).render(plot)
window = xwindow.FigureWindow(plot)

if len(sys.argv) > 1:
    raw_input("hit enter to end> ")

