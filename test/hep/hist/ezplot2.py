#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram1D
from   hep.hist import ezplot
from   random import normalvariate
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

gallery = ezplot.Gallery((2, 1, 2), border=0.01)
for page_number in range(3):
    gallery.nextPage(title="gallery, page %d" % (page_number + 1))

    for n in range(4):
        histogram = Histogram1D(20, (0.0, 1.0), "value")
        for i in range(100):
            histogram << normalvariate(0.5, 0.2)
        gallery << ezplot.simple1D(histogram, overflows=0, cross=1)

    
gallery.toPSFile("ezplot2.ps")


if len(sys.argv) > 1:
    import hep.draw.xwindow
    window = hep.draw.xwindow.FigureWindow(window_size=(0.2, 0.25))
    for page in gallery.pages:
        window.figure = page
        raw_input("hit enter to continue: ")
