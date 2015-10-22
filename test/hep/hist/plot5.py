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

x_axis = hep.hist.UnevenlyBinnedAxis(
    (0, 2, 3, 4, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0),
    float, name="$m_{ES}$", units="GeV/$c^2$")
y_axis = hep.hist.UnevenlyBinnedAxis(
    (-1, -0.5, 0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0),
    float, name=r"$\Delta E$", units="GeV")
histogram = hep.hist.Histogram(x_axis, y_axis, title="Test Histogram")

for i in range(10000):
    # Generate a flat distribution.
    m = random() * 5
    e = random() * 2 - 1
    histogram << (m, e)

layout = GridLayout(2, 2)

plot = hep.hist.plot.Plot(2, overflows=False)
plot.append(histogram, normalize_bin_size=None)
layout[0, 0] = plot
plot = hep.hist.plot.Plot(2, overflows=False)
plot.append(histogram)
layout[1, 0] = plot

plot = hep.hist.plot.Plot(2, overflows=False)
plot.append(histogram, bins="box", normalize_bin_size=None)
layout[0, 1] = plot
plot = hep.hist.plot.Plot(2, bins="box", overflows=False)
plot.append(histogram)
layout[1, 1] = plot

window = hep.draw.xwindow.FigureWindow(layout, (0.2, 0.2))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
