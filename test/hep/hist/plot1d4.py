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
for b, v in enumerate([7, 12, 28, 27, 29, 48, 60, 50, 71, 71, 73, 85,
                       66, 58, 59, 44, 53, 39, 38, 27, 18, 13, 7, 5, 3,
                       2, 0, 0, 0, 0]):
    histogram.setBinContent(b, v - 30)
histogram.setBinContent("underflow", -15)


layout = GridLayout(3, 3, border=0.01)
x_ranges = ((-1, 2), (-2, 0), (0, 1))
y_ranges = ((-30, 70), (-80, -5), (10, 50))

for x in range(3):
    for y in range(3):
        plot = hep.hist.plot.Plot(
            1,
            overflows=False,
            x_axis_range=x_ranges[x],
            y_axis_range=y_ranges[y])
        plot.append(histogram,
                    bins="skyline",
                    errors=True,
                    
                    fill_color=Gray(0.7),
                    line_color=None)
        layout[x, y] = plot

window = hep.draw.xwindow.FigureWindow(layout, (0.3, 0.2))
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

hep.draw.postscript.EPSFile("plot1d3.eps", window.size).render(layout)
