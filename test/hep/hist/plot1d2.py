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

histogram1 = hep.hist.Histogram1D(
    30, (-1.0, 2.0), "position", "m",
    bin_type=int, error_model="gaussian")
map(lambda (b, v): histogram1.setBinContent(b, v),
    enumerate([7, 12, 28, 27, 29, 48, 60, 50, 71, 71, 73, 85, 66, 58,
               59, 44, 53, 39, 38, 27, 18, 13, 7, 5, 3, 2, 0, 0, 0, 0]))
histogram1.setBinContent("underflow", 15)

histogram2 = hep.hist.Histogram1D(
    30, (-1.0, 2.0), "position", "m",
    bin_type=int, error_model="gaussian")
map(lambda (b, v): histogram2.setBinContent(b, v),
    enumerate([6, 12, 18, 28, 31, 38, 56, 64, 67, 62, 74, 82, 75, 59,
               68, 69, 44, 42, 25, 15, 28, 10, 7, 7, 4, 3, 2, 0, 0, 0]))
histogram2.setBinContent("underflow", 11)

layout = GridLayout(2, 2)

plot = hep.hist.plot.Plot(
    1,
    border=0.01)
plot.series.append(hep.hist.plot.Histogram1DPlot(
    histogram1,
    bins="skyline",
    fill_color=Color(1.0, 0.8, 0.9),
    line_color=Color(1.0, 0.6, 0.8)))
plot.series.append(hep.hist.plot.Histogram1DPlot(
    histogram2,
    bins="points",
    marker="empty dot",
    marker_size=5 * point,
    cross=False,
    color=Color(0.3, 0.6, 0.4)))
layout[0, 0] = plot

plot = hep.hist.plot.Plot(
    1,
    border=0.01)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram1))
layout[1, 0] = plot

plot = hep.hist.plot.Plot(
    1,
    border=0.01)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram2))
layout[0, 1] = plot

plot = hep.hist.plot.Plot(
    1,
    border=0.01)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram1))
layout[1, 1] = plot

window = hep.draw.xwindow.FigureWindow(layout, (0.25, 0.15))
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

hep.draw.postscript.EPSFile("plot1d2.eps", window.size).render(layout)
