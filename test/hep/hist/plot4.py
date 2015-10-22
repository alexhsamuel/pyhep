"""Test plotting of unevenly-binned 1-D histograms."""

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
# test
#-----------------------------------------------------------------------

axis = hep.hist.UnevenlyBinnedAxis(
    (-1, -0.5, 0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0),
    float, name="mass", units="GeV/$c^2$")
histogram = hep.hist.Histogram(axis, title="Test Histogram")

for i in range(1000):
    histogram << (random() + random() + random() - random()) / 2

layout = GridLayout(1, 3)
plot = hep.hist.plot.Plot(1)
plot.append(histogram, marker="empty dot")
layout[0, 0] = plot
plot = hep.hist.plot.Plot(1)
plot.append(histogram, marker="empty dot", normalize_bin_size=None)
layout[0, 1] = plot
plot = hep.hist.plot.Plot(1)
plot.append(histogram, marker="empty dot", normalize_bin_size=0.1)
layout[0, 2] = plot

window = hep.draw.xwindow.FigureWindow(layout, (0.16, 0.18))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

