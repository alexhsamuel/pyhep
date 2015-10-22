#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

grey = Color(0.85, 0.85, 0.85)
canvas = Canvas((-1, -1, 1, 1), aspect=1)
canvas.append(Line(((-1,-1),(-1,1),(1,1),(1,-1),(-1,-1))))
canvas.append(Polygon(
    ((-0.8, 0), (0, -0.7), (0.5, 0.1), (0.45, 0.85)),
    color=Color(1, 0.92, 0.96)))
canvas.append(Line(((1,-1),(-1,1)), color=grey))
canvas.append(Line(((0.2,-0.2),(-.1,-.5)), color=grey))
canvas.append(Text((0.2, -0.2), r"$f(x)=x_\alpha+O(x^2)$",
                   alignment=(0.5, 0.5)))
figure = GridLayout(2, 2)
for i in range(2):
    for j in range(2):
        figure[i, j] = canvas

postscript.EPSFile("draw3.eps", (0.15, 0.10)).render(figure)
metafile.EnhancedMetafile("draw3.emf", (0.15, 0.10)).render(figure)
window = xwindow.FigureWindow(figure, (0.15, 0.1))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
