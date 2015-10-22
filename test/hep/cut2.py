#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import cPickle
import hep.cuts
from   hep.draw import Line
import hep.hist
from   hep.hist import ezplot
from   numarray import array, Float32
from   random import normalvariate, random
import os

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

if not os.path.isfile("cut2.pickle"):
    sig_values = array(shape=(1000, 4), type=Float32)
    for i in range(sig_values.shape[0]):
        sig_values[i, 0] = normalvariate(0, 1)
        sig_values[i, 1] = normalvariate(0, 1)
        sig_values[i, 2] = normalvariate(0, 1)
        sig_values[i, 3] = normalvariate(0, 1)

    bkg_values = array(shape=(5000, 4), type=Float32)
    for i in range(bkg_values.shape[0]):
        bkg_values[i, 0] = normalvariate( 0, 2)
        bkg_values[i, 1] = normalvariate( 1, 1)
        bkg_values[i, 2] = normalvariate(-1, 1)
        bkg_values[i, 3] = normalvariate(-1, 1)
    cPickle.dump((sig_values, bkg_values), file("cut2.pickle", "w"), 1)
else:
    sig_values, bkg_values = cPickle.load(file("cut2.pickle"))
    

cuts = [
    (0, "<", random()),
    (0, ">", random()),
    (1, "<", random()),
    (2, ">", random()),
    (3, ">", random()),
    ]    

fom_fn = hep.cuts.s_squared_over_s_plus_b
cuts, fom = hep.cuts.iterativeOptimize(sig_values, bkg_values, cuts, fom_fn)
fom_curves = hep.cuts.makeFOMCurves(sig_values, bkg_values, cuts, fom_fn)

gallery = ezplot.Gallery(3 * (1, ), border=0.03)
print "optimal cuts:"
for (var_index, cut_sense, cut_value), fom_curve in zip(cuts, fom_curves):
    print "  variable #%d %s %f" % (var_index, cut_sense, cut_value)

    sig_hist = hep.hist.Histogram1D(120, (-5.0, 5.0), name="signal")
    map(sig_hist.accumulate, sig_values[:, var_index])
    bkg_hist = hep.hist.Histogram1D(120, (-5.0, 5.0), name="background")
    map(bkg_hist.accumulate, bkg_values[:, var_index])
    fom_curve.name = "cut FoM after other cuts"

    plot = ezplot.curves1D(sig_hist, bkg_hist, fom_curve)
    range = hep.hist.function.getRange(fom_curve, sig_hist.axis.range)
    plot.annotations.append(Line(
        ((cut_value, 0), (cut_value, range[1]))))
    gallery << plot

print "figure of merit =", fom

gallery.toPSFile("cut2.ps")
