#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow
from   hep.fn import enumerate
from   math import *
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

dashes = (
    None,
    (2 * point, 2 * point),
    (4 * point, 4 * point),
    (8 * point, 8 * point),
    (2 * point, 2 * point, 8 * point, 2 * point),
    (2 * point, 2 * point, 8 * point, 8 * point),
    (2 * point, 2 * point, 2 * point, 2 * point, 8 * point, 2 * point),
    )

thicknesses = (
    0.30 * point,
    0.75 * point,
    1.50 * point,
    3.00 * point
    )

canvas = Canvas((0, 0, 1, 1), aspect=1)
color = Color(0.6, 0, 0.2)

for d, dash in enumerate(dashes):
    y = (len(dashes) - d) / (1 + len(dashes))
    for t, thickness in enumerate(thicknesses):
        x0 = (1 + t * 8) / (8 * len(thicknesses))
        x1 = (7 + t * 8) / (8 * len(thicknesses))
        canvas.append(
            Line(((x0, y), (x1, y)),
                 color=color,
                 thickness=thickness,
                 dash=dash))
size = (0.10, 0.10)
postscript.EPSFile("lines1.eps", size).render(canvas)
metafile.EnhancedMetafile("lines1.emf", size).render(canvas)
window = xwindow.FigureWindow(canvas, size)

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
