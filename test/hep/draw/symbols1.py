#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep import *
from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow, imagefile
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

def symbols():
    f = Canvas((0, 0, 0.18, 0.18))
    for n, symbol_name in enumerate(sort(xwindow.symbol_map.keys())):
        x = 0.01 + (n // 24) * 0.04
        y = (26 - n % 24) * 0.006
        f.append(Symbol((x, y), symbol_name,
                        font="Times", font_size=14 * point))
        f.append(SimpleText((x + 0.008, y), symbol_name,
                            font_size=14 * point))
    return f


f = symbols()

metafile.EnhancedMetafile("symbols1.emf", (0.18, 0.18)).render(f)
postscript.PSFile("symbols1.ps").render(f)
imagefile.render(f, "symbols1.png", virtual_size=(0.18, 0.18))
window = xwindow.FigureWindow(f, (0.18, 0.18))

if len(sys.argv) > 1:
    raw_input()
