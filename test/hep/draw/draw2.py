#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow, imagefile
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

canvas = Canvas((-1, -1, 1, 1), aspect=1)
canvas.append(Line(((-1,-1),(-1,1),(1,1),(1,-1),(-1,-1))))
canvas.append(Polygon(
    ((-0.8, 0), (0, -0.7), (0.5, 0.1), (0.45, 0.85)),
    color=Color(1, 0.92, 0.96)))
canvas.append(Line(((1,-1),(-1,1))))
canvas.append(Line(((0,0),(-.3,-.3))))
canvas.append(SimpleText((0, 0), "Hello, world!", alignment=(0.5, 0.5)))
figure = BrickLayout((2, 4))
map(figure.append, 6 * (canvas, ))

postscript.EPSFile("draw2.eps", (0.15, 0.10)).render(figure)
metafile.EnhancedMetafile("draw2.emf", (0.15, 0.10)).render(figure)
imagefile.render(figure, "draw2.png", (600, 400))
window = xwindow.FigureWindow(figure, (0.15, 0.1))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

