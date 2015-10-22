#--------------------------------------------------*- coding: Latin1 -*-
#
# minuit.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Python interface to Minuit function minimizer."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import ext
from   hep.bool import *
import hep.expr
from   hep.minimize import normalizeParameters
import hep.hist
import hep.hist.plot
from   math import log
import sys
import time

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

verbose = False
"""If true, show verbose Minuit ouptut."""

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Result:
    """Results from a Minuit minimization.

    Attributes:

    'minimum' -- The minimum value achieved.

    'minuit_status' -- The Minuit status code; 3 indicates the
    minimization converged."""

    def __str__(self):
        return self.format(True)


    def format(self, show_fixed=False):
        result = "minimum value: %f\n" % self.minimum
        result += "parameter values:\n"
        keys = self.values.keys()
        keys.sort()
        for key in keys:
            value = self.values[key]
            initial, step, (bound_lo, bound_hi) = self.parameters[key]
            if step is None and not show_fixed:
                continue
            result += "  %-28s = %12.4f " % (key, value)
            if step is None:
                result += "(fixed)"
            else:
                result += "± %9.4f" % self.errors[key]
                if bound_lo != bound_hi:
                    if abs(value - bound_lo) < 1e-5:
                        result += " (at lower bound)"
                    elif abs(value - bound_hi) < 1e-5:
                        result += " (at upper bound)"
            result += "\n"
        if hasattr(self, "num_evaluations"):
            result += "number of evaluations: %d\n" % self.num_evaluations
        if hasattr(self, "elapsed_time"):
            result += "elapsed time: %.2f sec\n" % self.elapsed_time
        if hasattr(self, "minuit_status"):
            result += "Minuit status: %d\n" % self.minuit_status
        return result
    


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def minimize(function, parameters, verbose=False, minos=False,
             negate=False):
    """Choose parameters to minimize 'function'.

    Using Minuit, find values of named parameters that minimize the
    value of 'function', which may be any callable (including an
    'Expression' object).

    Note that fixed parameters are *not* registered in Minuit as (fixed)
    parameters; Minuit in fact does not know anything about them.  They
    are still passed to 'function' though.  This permits arbitrarily
    many non-floating parameters to be used without exceeding Minuit's
    limit of 100 parameters.

    'function' -- A callable object.  It will be called with keyword
    arguments (only), whose names are specified in 'parameters'.  All
    required arguments must be satisfied from 'parameters'.

    'parameters' -- One or more parameters to choose.  Each may be
    either a string name of the parameter, or a tuple '(name,
    initial_value, step_size, low, high)'.  The second and subsequent
    elements in the tuple may be omitted.

      'initial_value' -- The starting value for the parameter.  If
      omitted, the default is zero (which may not be appropriate, for
      some functions).

      'step_size' -- The starting step size.  If omitted or 'None', the
      parameter is fixed as a constant.

      'low', 'high' -- Constraints on the parameter value; if they are
      omitted (or both zero), the parameter is unconstrained.

    'verbose' -- If true, print verbose output.

    'minos' -- If true, use the MINOS algorithm to compute a better
    covariance matrix.

    'negate' -- If true, minimizes the value of '-function'.

    returns -- A 'Result' instance."""

    if isinstance(function, str):
        function = hep.expr.parse(function)
    if not callable(function):
        raise TypeError, \
              "'function' must be callable or an expression string"
    parameters = normalizeParameters(parameters)
        
    # Do the fit.
    start_time = time.time()
    result = ext.minuit_minimize(
        function, parameters, verbose, minos, negate)
    end_time = time.time()

    # Store the parameter settings.
    result.parameters = dict([ (p[0], p[1 :]) for p in parameters ])
    # Store the elapsed time.
    result.elapsed_time = end_time - start_time
    # All done.
    return result


def minimizeIteratively(function, *parameters):
    """Choose parameters to minimize 'function'.

    This function is similar to 'minimize', except that it proceeds by
    minimizing the parameters one at a time instead of
    simultaneously."""

    if isinstance(function, str):
        function = hep.expr.parse(function)
    if not callable(function):
        raise TypeError, \
              "'function' must be callable or an expression string"
    parameters = normalizeParameters(parameters)
    num_parameters = len(parameters)
    
    for count in range(4):
        indices = range(num_parameters)
        optimal_values = num_parameters * [ None ]
        for index in indices:
            parameter_name = parameters[index][0]

            min_parms = [
                (name, val, None, (0, 0))
                for (name, val, s, (l, h)) in parameters[: index] ] \
                + [ parameters[index], ] \
                + [
                (name, val, None, (0, 0))
                for (name, val, s, (l, h)) in parameters[index + 1: ] ]
            result = ext.minuit_minimize(function, min_parms, verbose)
        
            # print '  %s = %f' \
            #       % (parameter_name, result.values[parameter_name])
            optimal_values[index] = result.values[parameter_name]
            sys.stdout.flush()
            
        for index in range(num_parameters):
            name, value, step, (lo, hi) = parameters[index]
            value = optimal_values[index]
            parameters[index] = (name, value, step, (lo, hi))

        # print 'figure of merit = %f' % result.minimum
        # print

    return parameters


def maximumLikelihoodFit(likelihood, parameters, samples,
                         normalization_range=None, extended_fn=None,
                         verbose=False, minos=False):
    """Perform an unbinned maximum likelihood fit.

    Fit the 'parameters' of a 'likelihood' function to maximize the
    likelihood of 'samples'.

    If 'extended_fn' is provided, performs an extended maximum
    likelihood fit, where 'extended_fn' is the scale function for
    'likelihood'.  If 'extended_fn' is not provided, performs an
    ordinary maximum likelihood fit.

    'likelihood' -- The likelihood function or expression.

    'parameters' -- A sequence of parameters.  Each is of the form
    '(name, initial_value, step_size, lower_bound, upper_bound)', where
    everything after the 'name' may be omitted.

    'samples' -- An iterable of samples.  Each item is a mapping of
    sample variable name to value.  An iterator must not be used here;
    the function needs to iterate over the samples multiple times.

    'normalization_range' -- The likelihood function in a maximum
    likelihood fit must be normalized over the sample space.  If
    'likelihood' is already normalized, this parameter may be 'None'.
    Otherwise, it is a sequence of integration ranges of the form
    '(var_name, lo, hi)', over which the likelihood function is
    numerically integrated for each choice of parameters.  The 'lo' and
    'hi' values may be constants or expressions involving the
    parameters.

    'extended_fn' -- If provided, the function to use in an extended
    maximum likelihood fit.

    returns -- A minimization 'Result' object."""

    # Convert the likelihood function to an expression object.
    likelihood = hep.expr.asExpression(likelihood)
    # Set the types of the symbols for the sample variables and
    # parameters to 'float'.  This will produce better compiled
    # expressions.
    likelihood = hep.expr.op.setTypesFixed(likelihood, None, float)

    # Clean up the parameters specification.
    parameters = normalizeParameters(parameters)

    if normalization_range is not None:
        # Convert the normalization range bounds to expression objects. 
        normalization_range = [
            (var, hep.expr.asExpression(lo), hep.expr.asExpression(hi))
             for (var, lo, hi) in normalization_range ]

    if extended_fn is not None:
        # Convert the extended function to an expression object.
        extended_fn = hep.expr.asExpression(extended_fn)
        # As with the likelihood function, all symbol types are floats.
        extended_fn = hep.expr.op.setTypesFixed(extended_fn, None, float)
        # Use its evaluate function.
        extended_fn = extended_fn.evaluate

    # Get busy.
    result = ext.minuit_maximumLikelihoodFit(
        likelihood, parameters, samples, normalization_range,
        extended_fn, verbose, minos)
    result.parameters = dict([ (p[0], p[1 :]) for p in parameters ])

    # Construct the resulting likelihood function.
    fit_likelihood = hep.expr.substitute(likelihood, **result.values)
    # Normalize it, if necessary.
    if normalization_range is not None:
        from hep.cernlib import integrate
        integral = integrate(fit_likelihood, *[
            (name, lo(**result.values), hi(**result.values))
            for (name, lo, hi) in normalization_range ])
        fit_likelihood = hep.expr.Multiply(
            fit_likelihood, hep.expr.Constant(1 / integral))
    result.likelihood = fit_likelihood
        
    return result


def plotMaximumLikelihoodFit1D(fit_result, samples, sample_var=None,
                               draw=None):
    """Construct a plot of the results of a 1D maximum likelihood fit.

    Constructs a histogram of the samples that were fit, and plots it
    with the fit likelihood function superimposed.

    'fit_result' -- The result of a maximum likelihood fit.

    'samples' -- The samples to which the likelihood function was fit.

    'sample_var' -- The name of the sample variable.  If the samples
    contain only one variable item, it may be omitted.

    returns -- A 'Plot' object.  Note that the plot is not drawn."""

    if sample_var is None:
        # Guess the sample variable name from the samples.
        sample = samples[0]
        if len(sample) != 1:
            raise ValueError, "samples must have one element unless " \
                  "'sample_var' is specified"
        sample_var = sample.keys()[0]

    # Convert the samples from a sequence of dictionaries to a simple
    # sequence of sample values. 
    samples = [ sample[sample_var] for sample in samples ]
    # Histogram them.
    histogram = hep.hist.autoHistogram1D(samples)
    histogram.axis.name = sample_var
    # Scale the likelihood function to the binning and overall integral
    # of the histogram.
    range = histogram.axis.range
    bin_size = (range[1] - range[0]) / histogram.axis.number_of_bins
    likelihood = hep.expr.Multiply(
        fit_result.likelihood,
        hep.expr.Constant(len(samples) * bin_size))

    # Plot stuff.
    plot = hep.hist.plot.plot(draw, histogram, bin_style="marker")
    likelihood_fn = hep.hist.Function1D(likelihood, sample_var)
    plot.addSeries(likelihood_fn)
    plot.title = "likelihood fit: %s" % fit_result.likelihood
    return plot


