#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cuts import FisherDiscriminant, optimize
from   hep.draw import *
import hep.hist
from   hep.hist import ezplot
import hep.hist.plot
from   hep.test import compare
import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

samples1 = []
samples2 = []
sc1 = hep.hist.Scatter()
sc2 = hep.hist.Scatter()
h1x = hep.hist.Histogram1D(40, (-2., 6))
h2x = hep.hist.Histogram1D(40, (-2., 6))
h1y = hep.hist.Histogram1D(40, (-5., 15))
h2y = hep.hist.Histogram1D(40, (-5., 15))

for n in xrange(1000):
    x = random.normalvariate(0, 1)
    y = random.normalvariate(0, 1)
    samples1.append(((x, y, ), 1))
    sc1 << (x, y, )
    h1x << x
    h1y << y

for n in xrange(1000):
    x = random.normalvariate(2, 1)
    y = random.normalvariate(3, 2)
    samples2.append(((x, y, ), 1))
    sc2 << (x, y, )
    h2x << x
    h2y << y

gallery = ezplot.Gallery(2 * (2, ), border=0.02, aspect=1)

plot = ezplot.curves1D(h1y, h2y, overflows=False)
colors = [ s.style["line_color"] for s in plot.series ]
gallery << plot

plot = hep.hist.plot.Plot(2, overflows=False,
                          x_axis_range=h1x.axis.range,
                          y_axis_range=h1y.axis.range)
plot.append(sc1, bins="points", marker="filled dot", color=colors[0])
plot.append(sc2, bins="points", marker="filled dot", color=colors[1])
gallery << plot

fisher = FisherDiscriminant(samples1, samples2)

f1 = [ fisher(v) for (v, w) in samples1 ]
f2 = [ fisher(v) for (v, w) in samples2 ]
hf1 = hep.hist.Histogram1D(60, (-12., 6))
map(hf1.accumulate, f1)
hf2 = hep.hist.Histogram1D(60, (-12., 6))
map(hf2.accumulate, f2)

cut, fom = optimize(f1, f2, ">")
description = "cut: $F > %f$,  $S^2/(S+B)$ = %f" % (cut, fom)
print description

hf1.title = description
hf1.axis.name = r"$F=%f\,\times\,x\ +\ %f\,\times\,y$" \
                % tuple(fisher.coefficients)
plot = ezplot.curves1D(hf1, hf2, overflows=False)
y_min = 0
y_max = 1
plot.annotations.append(Line(((cut, y_min), (cut, y_max))))
gallery << plot

gallery << ezplot.curves1D(h1x, h2x, overflows=False)

compare(fisher.coefficients[0], -1, precision=0.2)
compare(fisher.coefficients[1], -0.6, precision=0.2)

gallery.toPSFile("fisherplot1.ps")
