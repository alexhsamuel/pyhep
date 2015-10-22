"""Test plotting of histogram statistics."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.draw import *
import hep.draw.postscript
import hep.draw.xwindow
import hep.hist
from   hep.hist.plot import Plot, Statistics
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

green = Color(0.2, 0.6, 0.4)

histogram1 = hep.hist.makeSample1D("normal gaussian")
histogram2 = hep.hist.makeSample1D("gaussian")

layout = GridLayout(2, 1)
plot = Plot(1, overflows=False,
            marker="filled dot", marker_size=0.0015)
plot.append(histogram1, color=black)
plot.append(histogram2, color=Color(0.6, 0, 0))
plot.append(Statistics(
    ("sum", "mean", "sd"), histogram1, histogram2))
layout[0, 0] = plot

plot = Plot(1, overflows=False,
            marker="filled dot", marker_size=0.0015)
plot.append(histogram1, color=black)
plot.append(histogram2, color=green)
plot.append(Statistics(
    ("sum", "overflows"), histogram2,
    annotation_color=green, annotation_position="left"))
layout[1, 0] = plot

hep.draw.postscript.EPSFile("plot7.eps", (0.23, 0.1)).render(layout)
window = hep.draw.xwindow.FigureWindow(layout, (0.23, 0.1))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
