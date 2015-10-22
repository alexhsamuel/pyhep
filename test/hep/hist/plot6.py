"""Test plotting of unevenly-binned 2-D histograms."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.draw import *
import hep.draw.postscript
import hep.draw.xwindow
import hep.hist
import hep.hist.plot
from   random import random
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

histogram = hep.hist.Histogram(
    (10, (0.0, 1.0), "X"), (20, (-1.0, 1.0), "Y"),
    bin_type=float)

for i in range(10000):
    # Generate a flat distribution.
    x = random()
    y = random() * 2 - 1
    w = random() * 1.5 - x
    histogram.accumulate((x, y), w)

layout = GridLayout(2, 1)

plot = hep.hist.plot.Plot(2, overflows=False)
plot.append(histogram)
layout[0, 0] = plot
plot = hep.hist.plot.Plot(2, overflows=False, z_range=(-10, 20))
plot.append(histogram)
layout[1, 0] = plot

hep.draw.postscript.EPSFile("plot6.eps", (0.23, 0.1)).render(layout)
window = hep.draw.xwindow.FigureWindow(layout, (0.23, 0.1))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
