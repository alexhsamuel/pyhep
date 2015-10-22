#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.draw import *
import hep.draw.postscript
import hep.draw.xwindow
from   hep.fn import enumerate
import hep.hist
import hep.hist.plot
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

layout = GridLayout(1, 2, border=0.01)

histogram = hep.hist.Histogram1D(
    30, (-1.0, 2.0), "position", "m",
    bin_type=int, error_model="gaussian")
for b, v in enumerate([7, 12, 28, 27, 29, 48, 60, 50, 71, 71, 73, 85,
                       66, 58, 59, 44, 53, 39, 38, 27, 18, 13, 7, 5, 3,
                       2, 0, 0, 0, 0]):
    histogram.setBinContent(b, v)
histogram.setBinContent("underflow", 15)

plot = hep.hist.plot.Plot(
    1,
    histogram,
    bins="skyline",
    errors=True,
    fill_color=Gray(0.7),
    line_color=None)
layout[0, 0] = plot

plot = hep.hist.plot.Plot(
    1,
    histogram,
    bins="skyline",
    errors=True,
    fill_color=None,
    line_color=black,
    error_hatch_thickness=0.2 * point)
layout[0, 1] = plot

window = hep.draw.xwindow.FigureWindow(layout, (0.2, 0.2))
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

hep.draw.postscript.EPSFile("plot1d3.eps", window.size).render(layout)
