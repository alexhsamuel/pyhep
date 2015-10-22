#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow, imagefile
from   math import *
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

canvas = Canvas((-1, -1, 1, 1), aspect=1)
points = [ (n / 200 * cos(n / 5), sqrt(n / 200) * sin(n / 5))
           for n in xrange(0, 200) ]
canvas.append(Line(points, color=Color(0.3,0.7,1)))
canvas.append(Line(((-1,-1),(-1,1),(1,1),(1,-1),(-1,-1))))
figure = BrickLayout((2, 10))
map(figure.append, 12 * (canvas, ))

postscript.EPSFile("draw1.eps", size=(0.15, 0.10)).render(figure)
metafile.EnhancedMetafile("draw1.emf", (0.15, 0.10)).render(figure)
imagefile.render(figure, "draw1.png", (600, 400))
window = xwindow.FigureWindow(figure, (0.15, 0.1))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
