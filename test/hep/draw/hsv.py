#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

num_hue = 26
num_sat = 5
num_val = 10

width = 2 + num_sat * (num_val + 1)
height = num_hue
aspect = width / height
canvas = Canvas((0, 0, width, height), border=0.005, aspect=aspect)

for h in range(num_hue):
    for s in range(num_sat):
        for v in range(num_val):
            hue = h / (num_hue - 1)
            sat = (s + 1) / num_sat
            val = (v + 1) / num_val
            color = HSV(hue, sat, val)
            x0 = 2 + s * (num_val + 1) + v
            x1 = x0 + 0.85
            y0 = h
            y1 = y0 + 0.85
            canvas.append(Polygon(
                ((x0, y0), (x0, y1), (x1, y1), (x1, y0)),
                color=color))

for h in range(num_hue):
    hue = h / (num_hue - 1)
    canvas.append(Text((1.75, h + 0.425), "%.3f" % hue, alignment=(1, 0.5)))
            
postscript.PSFile("hsv.ps").render(canvas)
metafile.EnhancedMetafile("hsv.emf", (0.25, 0.25 / aspect)).render(canvas)

window = xwindow.FigureWindow(canvas, (0.25, 0.25 / aspect))
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")

