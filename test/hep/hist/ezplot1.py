#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

import hep.draw.postscript
import hep.draw.xwindow
import hep.hist
import hep.hist.ezplot
from   random import normalvariate
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

histograms = []
for i in range(5):
    histogram = hep.hist.Histogram1D(20, (0.0, 1.0), "value")
    for n in range((i + 1) * 1000):
        histogram << normalvariate(0.3 + i * 0.1, 0.2)
    histograms.append(histogram)

style = {
    "title": "Stacked Histograms",
    "caption": r"selection: $1-f(v) < v^\alpha$",
    }

plot = hep.hist.ezplot.stacked1D(*histograms, **style)

hep.draw.postscript.PSFile("ezplot1.ps").render(plot)

window = hep.draw.xwindow.FigureWindow(plot)
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

