#--------------------------------------------------*- coding: Latin1 -*-
#
# fit.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep import enumerate
from   hep.bool import *
import hep.expr
import hep.expr.op
import hep.fn
import hep.hist
from   hep.num import sum, product, factorial
from   math import hypot, sqrt, log
import sys

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

# FIXME: 'NaiveChiSquare' and 'naiveChiSquareFit' are deprecated, and
# are only left here only until another multidimensional fitter is
# available.

class NaiveChiSquare:

    def __init__(self, function, sample_vars, samples):
        self.function = function
        self.sample_vars = tuple(sample_vars)
        self.samples = samples


    def __call__(self, **parameters):
        symbols = dict(parameters)

        result = 0
        for x, y, e in self.samples:
            # FIXME:
            if e == 0:
                continue
            for var, value in zip(self.sample_vars, x):
                symbols[var] = value
            f = self.function(**symbols)
            result += ((f - y) / e) ** 2

        return result



def naiveChiSquareFit(histogram, function, variable_names, parameters):
    import hep.cernlib.minuit

    function = hep.expr.asExpression(function)
    samples = [ (hep.hist.getBinCenter(histogram.axes, bin),
                 histogram.getBinContent(bin),
                 histogram.getBinError(bin))
                for bin in hep.hist.AxesIterator(histogram.axes) ]
    chi_sq = NaiveChiSquare(function, variable_names, samples)
    result = hep.cernlib.minuit.minimize(chi_sq, *parameters)
    result.expression = hep.expr.substitute(function, **result.values)
    return result


#-----------------------------------------------------------------------

class ChiSquare1D:
    """Function object to compute one-dimensional chi-square."""

    def __init__(self, function, sample_var, samples):
        self.function = function
        self.sample_var = sample_var
        self.samples = samples
        self.warned = False


    def __call__(self, **parameters):
        # FIXME: We could save some evaluations on adjacent bins here.
        def eval(x, sample_var=self.sample_var, function=self.function):
            parameters[sample_var] = x
            return function(**parameters)

        # Substitute parameters.
        function = hep.expr.substitute(self.function, **parameters)
        # Compile the function, using 'float' as the type for the
        # independent variable.
        function = hep.expr.compile(function, float)

        eval = lambda v: function.evaluate({ self.sample_var: v })

        chi_sq = 0
        for (x0, x1), y in self.samples:
            # We can't handle non-positive bin values, since we can't
            # compute gaussian errors for them.
            if y <= 0:
                if not self.warned:
                    print >> sys.stderr, \
                      "Warning: non-positive bin values ignored in chi-square"
                    self.warned = True
                continue
            # Do Simpson's rule integration.
            f = (x1 - x0) \
                * (eval(x0) + 4 * eval((x0 + x1) / 2) + eval(x1)) / 6
            # Update the chi-square.
            chi_sq += ((f - y) ** 2) / y

        return chi_sq



def chiSquareFit1D(histogram, function, variable_name, parameters,
                   min_count=7, range=None):
    """Perform a one-dimensional chi-square fit of a PDF to a histogram.
    
    Performs a chi-square fit of PDF 'function' to a one-dimensional
    histogram.  The chi-square is computed using Simpson's rule
    (three-point gaussian quadrature) to integrate the PDF for
    comparison with histogram bins.  Bin errors in 'histogram' are
    ignored; 1/sqrt(N) gaussian couning errors are always used.
    Therefore, histogram contents should be positive integers (though
    zero and small bins are handled; see the 'min_count' parameter
    below).

    'histogram' -- The histogram to fit to.

    'function' -- The PDF.  May be an 'Expression' object or a
    callable.

    'variable_name' -- The name of the variable in 'function'
    corresponding to the dependent quantity in 'histogram' (i.e. the
    quantity along the histogram axis).

    'parameters' -- A sequence of parameters to fit.  Each may be simply
    a variable name in 'function', or a sequence '(name, initial_value,
    step_size, bound_low, bound_hi)'.

    'min_count' -- The minimum value for bins in the fit.  Bins which
    contain a smaller value than this are coalesced with neighboring
    bins until all bins contain at least this value.

    returns -- A 'Result' object."""

    # We'll use this for minimization.
    import hep.minimize
    import hep.cernlib.minuit

    axis = histogram.axis
    function = hep.expr.asExpression(function)
    parameters = hep.minimize.normalizeParameters(parameters)

    num_floating = sum([ 1 for p in parameters if p[2] is not None ])

    # Construct the list of bin samples, coalescing bins as necessary. 
    samples = []
    # Figure out which bins are included in the fit.
    if range is None:
        bins = hep.hist.AxisIterator(axis)
    else:
        lo, hi = range
        bins = xrange(axis(lo), axis(hi))
    # Loop over bins.
    x0 = None
    for bin in bins:
        range = axis.getBinRange(bin)
        # Are we carrying a bin whose contents don't satisfy the minimum
        # so far? 
        if x0 is None:
            # No.  Start a new bin
            x0, x1 = range
            value = histogram.getBinContent(bin)
        else:
            # Yes.  Make sure we are adjacent.
            assert x1 == range[0]
            # Coalesce this bin with the carried one.
            x1 = range[1]
            value += histogram.getBinContent(bin)
        # Doe the bin we're carrying have enough in it?
        if value >= min_count:
            # Yes it does.  Use it as a sample.
            samples.append(((x0, x1), value, ))
            x0 = None

    # If we're still carrying a bin, it must not have enough in it.  But
    # we have to do something with it.
    if x0 is not None:
        # Are there any samples at all so far?
        if len(samples) > 0:
            # Yes there are.  Coalesce the bin we're carrying with the
            # last one. 
            (last_x0, last_x1), last_value = samples.pop(-1)
            assert last_x1 == x0
            samples.append(((last_x0, x1), last_value + value, ))
        else:
            # No samples.  The whole histogram doesn't have enough in it
            # to satisfy the minimum criterion.  Oh well, just use one
            # sample. 
            samples.append(((x0, x1), value, ))

    # Construct the chi-square function.
    chi_sq = ChiSquare1D(function, variable_name, samples)
    # Minimize it.
    result = hep.cernlib.minuit.minimize(chi_sq, parameters)

    # Store the number of degrees of freedom.
    dof = len(samples) - num_floating
    result.degrees_of_freedom = dof
    # Compute the chi-square probability.
    result.chi_square_probability = \
        dof > 0 and hep.num.chiSquareCDF(result.minimum, dof) or None
                                 
    # Substitute the fit parameter values into 'function' and store
    # that. 
    result.expression = hep.expr.substitute(function, **result.values)

    # Construct a function suitable for plotting.  Scale the PDF by the
    # bin size, for sensible comparison to the histogram.
    bin_size = (axis.range[1] - axis.range[0]) / axis.number_of_bins
    scaled_expr = hep.expr.Multiply(
        result.expression, hep.expr.Constant(bin_size))
    notes = "Results of fit to '%s'\n" % str(function)
    notes += "   $\chi^2$ / DOF = %.2f / %d\n" \
             % (result.minimum, result.degrees_of_freedom, )
    if result.chi_square_probability is not None:
        notes += "   $P_{\chi^2}$ = %.3f\n" % result.chi_square_probability
    for name, value in result.values.items():
        notes += "   %s = %.4f ± %.4f\n" \
                 % (name, value, result.errors[name])
    result.function = hep.hist.Function1D(
        scaled_expr, arg_name=variable_name,
        axis=hep.hist.Axis(axis.type, range=axis.range), notes=notes)

    return result


def getChiSquare(histogram, function):
    """Compute the binned chi^2 between 'histogram' and 'function'.

    FIXME: Only works with one-dimensional histograms.

    returns -- 'chi_square, number_of_bins'."""

    def integrate(function, region):
        """Estimate the integral of 'function' over rectangular 'region'."""

        # Average the integrand over the corners of the region.
        sum = 0
        count = 0
        for point in hep.fn.combinations(*region):
            sum += function(*point)
            count += 1
        # Compute the volume of the region.
        volume = reduce(lambda x, (lo, hi): x * (hi - lo), region, 1)
        return volume * sum / count


    def thunk(**kw_args):
        args = []
        for n in xrange(len(kw_args)):
            args.append(kw_args["x%d" % (n, )])
        return function(*args)

    chi_square = 0
    num_bins = 0
    mult = 10 * [0]
    for bin in hep.hist.AxesIterator(histogram.axes, overflows=False):
        # Get the value and error of this histogram in this bin.
        hist_value = histogram.getBinContent(bin)
        lo, hi = histogram.getBinError(bin)
        hist_error = (lo + hi) / 2

#         # Approximate the integral of 'function' over the bin.
#         ranges = [ a.getBinRange(n)
#                    for a, n in zip(histogram.axes, bin) ]
#         # area = product([ b - a for a, b in ranges ])
#         # center = [ (a + b) / 2 for a, b in ranges ]
#         # func_value = area * function(*center)
#         integration_region = [
#             ("x%d" % (n, ), lo, hi)
#             for n, (lo, hi) in enumerate(ranges) ]
#         func_value = hep.cernlib.integrate(
#             thunk, *integration_region,
#             **{ "accuracy": 1e-4 })
        region = hep.hist.getBinRange(histogram.axes, bin)
        func_value = integrate(function, region)

        # Update the chi square.
        if func_value == 0:
            if hist_value != 0:
                print >> sys.stderr, \
                      "WARNING: skipping bin with zero function value"
        else:
            chi_square += ((func_value - hist_value) / hist_error) ** 2
            num_bins += 1
            mult[min(9, hist_value)] += 1

    print mult
    return chi_square, num_bins


def poissonLogLikelihoodRatio(histogram, function):
    """Compute the log likelihood ratio assuming Poisson bin contents.

    Computes the log likelihood ratio between a 'histogram' and a
    likelihood 'function' assuming that bin contents are Poisson
    distributed.

    'histogram' -- A histogram.

    'function' -- A likeihood function, generally produced by a (binned
    or unbinned) maximum likelihood fit."""

    def integrate(function, region):
        """Estimate the integral of 'function' over rectangular 'region'."""

        # Average the integrand over the corners of the region.
        sum = 0
        count = 0
        samples = [ ((1, l), (4, (l + h) / 2), (1, h)) for l, h in region ]
        for sample in hep.fn.combinations(*samples):
            weight = product([ w for w, c in sample ])
            point = [ c for w, c in sample ]
            sum += weight * function(*point)
            count += weight
        # Compute the volume of the region.
        volume = reduce(lambda x, (lo, hi): x * (hi - lo), region, 1)
        return volume * sum / count


    axes = histogram.axes
    log_ratio = 0
    degrees_of_freedom = 0
    for bin in hep.hist.AxesIterator(axes):
        region = hep.hist.getBinRange(axes, bin)
        f = integrate(function, region)
        h = histogram.getBinContent(bin)
        if f == 0:
            if h != 0:
                raise ValueError, \
                      "histogram nonzero where likelihood is zero"
        else:
            if h < 0:
                raise ValueError, "negative bin content"
            # print "%6d %8.1f" % (h, f)

            log_ratio += f
            if h > 0:
                log_ratio -= h * (1 + log(f) - log(h))
            degrees_of_freedom += 1

    return log_ratio, degrees_of_freedom


