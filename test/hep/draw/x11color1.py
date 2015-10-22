#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import xwindow
import sys
import time

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

canvas = Canvas((0, 0, 0.24, 0.07))
for r in range(0, 4):
    for g in range(0, 4):
        for b in range(0, 4):
            color = Color(r / 3, g / 3, b / 3)
            x0 = 0.012 + r * 0.012 + b * 0.055
            x1 = x0 + 0.01
            y0 = 0.012 + g * 0.012
            y1 = y0 + 0.004
            canvas.append(Polygon(
                ((x0, y0), (x0, y1), (x1, y1), (x1, y0)),
                color=color))
            canvas.append(Text((x0, y0 + 0.005), "%d%d%d" % (r, g, b)))

window = xwindow.FigureWindow(canvas)

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

