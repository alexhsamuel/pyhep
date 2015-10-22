#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow
import hep.fn
from   math import *
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

grey = Color(0.85, 0.85, 0.85)
figure = Canvas((0, 0, 1, 1), aspect=1)
count = len(marker_shapes)
for i, shape in hep.fn.enumerate(marker_shapes):
    y = (count - i) / (count + 2)
    figure.append(Text((0.1, y), shape))
    figure.append(Markers(((0.5, y), ), shape=shape, size=1 * point))
    figure.append(Markers(((0.6, y), ), shape=shape, size=2 * point))
    figure.append(Markers(((0.7, y), ), shape=shape, size=4 * point))
    figure.append(Markers(((0.8, y), ), shape=shape, size=8 * point))

postscript.EPSFile("marker1.eps", (0.15, 0.10)).render(figure)
metafile.EnhancedMetafile("marker1.emf", (0.15, 0.10)).render(figure)
window = xwindow.FigureWindow(figure, (0.15, 0.10))
 
if len(sys.argv) > 1:
    raw_input()

