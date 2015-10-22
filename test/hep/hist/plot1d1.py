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

histogram = hep.hist.Histogram1D(
    30, (-1.0, 2.0), "position", "m",
    bin_type=int, error_model="gaussian")
map(lambda (b, v): histogram.setBinContent(b, v),
    enumerate([7, 12, 28, 27, 29, 48, 60, 50, 71, 71, 73, 85, 66, 58,
               59, 44, 53, 39, 38, 27, 18, 13, 7, 5, 3, 2, 0, 0, 0, 0]))
histogram.setBinContent("underflow", 15)

layout = GridLayout(2, 2)

plot = hep.hist.plot.Plot(
    1,
    border=0.01)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram))
layout[0, 0] = plot

plot = hep.hist.plot.Plot(
    1,
    border=0.01,
    log_scale=True)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram))
layout[0, 1] = plot

plot = hep.hist.plot.Plot(
    1,
    border=0.01,
    x_axis_line=True,
    x_axis_thickness=1.5 * point,
    y_axis_line=True,
    y_axis_thickness=1.5 * point,
    tick_thickness=1 * point,
    zero_line=False,
    offset=0,
    overflows=False,
    font_size=14 * point)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram))
layout[1, 0] = plot

plot = hep.hist.plot.Plot(
    1,
    x_axis_position="top",
    x_axis_thickness=None,
    y_axis_position="right",
    border=0.01)
plot.series.append(hep.hist.plot.Histogram1DPlot(histogram))
layout[1, 1] = plot

window = hep.draw.xwindow.FigureWindow(layout, (0.25, 0.15))
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

hep.draw.postscript.EPSFile("plot1d1.eps", window.size).render(layout)
