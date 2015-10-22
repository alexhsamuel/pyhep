#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
from   hep.draw import metafile, postscript, xwindow
from   hep.fn import enumerate
import sys

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

texts = [
    r"$x^2 + y^2 = z^2$",
    r"$x\ =\ r\ \sin\theta\cos\phi$",
    r"$\Lambda_{a+b} = \Lambda_a\cdot\Lambda_b$",
    r"The result is, $H^\dagger\sim\infty$.",
    r"en--dash, em---dash",
    r"$10-20 GeV/c^2$",
    r"$\Upsilon(4S)\rightarrow B^+B^-$, $B^\pm\rightarrow K_S\pi^0\pi^\pm$",
    ]

canvas = Canvas((0, 0, 1, 1))
for i, text in enumerate(texts):
    y = (len(texts) - i) / (len(texts) + 2)
    canvas.append(Text((0.1, y), text))

postscript.EPSFile("latex1.eps", (0.15, 0.10)).render(canvas)
metafile.EnhancedMetafile("latex1.emf", (0.15, 0.10)).render(canvas)
window = xwindow.FigureWindow(canvas, (0.15, 0.10))

if len(sys.argv) > 1:
    raw_input("hit enter to end: ")
