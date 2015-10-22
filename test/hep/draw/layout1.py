#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.draw import *
import hep.draw.postscript
import hep.draw.xwindow
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

canvas = Canvas((0, 0, 1, 1))
canvas.append(Line(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0), (1, 1))))
canvas.append(Line(((1, 0), (0, 1))))

grid = GridLayout(5, 3, margin=0.005, border=0.01, aspect=1.67)
for c in range(5):
    for r in range(3):
        grid[c, r] = canvas

hep.draw.postscript.PSFile("layout1.ps").render(grid)

window = hep.draw.xwindow.FigureWindow(grid)
if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
