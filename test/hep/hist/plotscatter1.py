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

scatter = hep.hist.Scatter((float, "mass", "GeV/$c^2$"),
                           (float, "momentum", "GeV/$c$"))

for i in range(200):
    x = random() * 2
    y = random() + random() + random() + random() - 2
    scatter << (x, y)

layout = GridLayout(2, 1, aspect=1)

plot = hep.hist.plot.Plot(2, overflows=False,
                          marker="*", marker_size=5 * point)
plot.append(scatter)
layout[0, 0] = plot
plot = hep.hist.plot.Plot(2)
plot.append(scatter, overflows=True, x_range=(0, 1.8), y_range=(-1, 1))
layout[1, 0] = plot

hep.draw.postscript.PSFile("plotscatter1.ps").render(layout)
window = hep.draw.xwindow.FigureWindow(layout, (0.23, 0.1))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
