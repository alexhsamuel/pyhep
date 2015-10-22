#-----------------------------------------------------------------------
#
# function.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Parameterized and decorated functions for fitting and plotting.

A function object represents a single-values function of one or many
arguments.  A function may also be specified using fixed parameters,
which are not considered to be among the formal arguments.  The
function's arguments are specified by axis objects, similarly to
histogram objects. """

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   axis import *
from   hep import popkey
import hep.expr
import hep.ext
import hep.num
import util
import sys

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class _Function:
    """A single-valued function of multiple arguments."""

    def __init__(self, axes, expr, arg_names, parameters):
        if len(axes) != len(arg_names):
            raise ValueError, \
                  "the number of axes and argument names must be the same"
        self.axes = axes
        self.formula = str(expr)
        self.expr = hep.expr.asExpression(expr)
        self.arg_names = arg_names
        self.parameters = parameters

        self.__compile()


    def __repr__(self):
        return "Function(axes=%r, expr=%r, arg_names=%r, " \
               "parameters=%r)" \
               % (self.axes, self.formula, self.arg_names,
                  self.parameters)


    dimensions = property(lambda self: len(self.axes))


    # FIXME: Find the expr type correctly, using the argument and
    # parameter types.
    type = property(lambda self: self.expr.type)


    def __getstate__(self):
        state = dict(self.__dict__)
        del state["compiled_expr"]
        return state


    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__compile()


    def __compile(self):
        """Construct a compiled version of 'expr'."""

        # Infer parameter types from their values.
        parameter_types = dict(
            [ (n, type(v)) for (n, v) in self.parameters.items() ])
        # Compile the expression.  Free symbols are taken as 'float'.
        self.compiled_expr = hep.expr.compile(
            self.expr, float, **parameter_types)


    def __call__(self, args):
        """Evaluate the function.

        'args' -- A sequence of argument values.  Each item in the
        sequence is the coordinate value along the corresponding axis.

        returns -- The result of evaluating the function.  If the
        function has no value at the specified 'args', for instance if
        one of the coordinate values is out of range of its axis,
        returns 'None'."""

        if len(args) != len(self.arg_names):
            raise TypeError, \
                  "function takes %d arguments" % len(self.arg_names)
        
        # Build the symbol table for evaluation.  Start with fixed
        # parameters. 
        symbols = dict(self.parameters)
        # Now the arguments.  
        for i in xrange(len(self.axes)):
            axis = self.axes[i]
            arg_name = self.arg_names[i]
            arg = args[i]
            # Get the axis range, if any.
            lo, hi = getattr(axis, "range", (None, None))
            # If a coordinate value is outside the axis range, the
            # function has no value.
            if (lo is not None and arg < lo) \
               or (hi is not None and arg >= hi):
                return None
            # Store the argument value for this symbol.
            symbols[arg_name] = axis.type(arg)
        # Evaluate the expression.
        try:
            return self.compiled_expr.evaluate(symbols)
        except (ZeroDivisionError, FloatingPointError, OverflowError,
                ValueError), exception:
            print >> sys.stderr, \
                  "warning: exception \"%s\" in \"%s\" at " \
                  % (exception, self.expr) \
                  + ", ".join([ "%s=%s" % i for i in symbols.items() ])
            return None



#-----------------------------------------------------------------------

class _Function1D(_Function):
    """A single-valued function of one argument."""

    def __init__(self, axis, expr, arg_name, parameters):
        _Function.__init__(self, (axis, ), expr, (arg_name, ), parameters)


    def __repr__(self):
        return "Function1D(axis=%r, expr=%r, arg_name=%r, " \
               "parameters=%r)" \
               % (self.axis, self.formula, self.arg_names[0],
                  self.parameters)


    axis = property(lambda self: self.axes[0])


    def __call__(self, arg):
        return _Function.__call__(self, wrap1D(arg))

    

#-----------------------------------------------------------------------

class _SampledFunction1D:

    def __init__(self, axis, type):
        self.axis = axis
        self.axes = ( axis, )
        self.type = type
        self.samples = []



    def __repr__(self):
        return "SampledFunction(axes=%r, type=%r)" \
               % (self.axes, self.type)


    dimensions = property(lambda self: len(self.axes))


    def addSample(self, arg, value, error=0):
        """Add a sample to the function."""

        arg = self.axis.type(arg)
        value = self.type(value)
        # Find the location at which to insert it into the sorted
        # sequence. 
        index = _binarySearch(
            self.samples, arg, lambda a, e: cmp(a, e[0]))
        # Insert it.
        self.samples.insert(index, (arg, value))


    def __call__(self, arg):
        """Return the value of the function at 'arg'.

        The function must have at least two samples, and 'arg' must be
        within the range of samples of the function."""

        arg, = wrap1D(arg)
        arg = self.axis.type(arg)
        # There must be some samples.
        if len(self.samples) < 2:
            raise RuntimeError, "not enough samples to evaluate"
        # Find the position of 'arg' among the samples.
        index = _binarySearch(
            self.samples, arg, lambda a, e: cmp(a, e[0]))
        # Make sure it's in range.
        if index == 0 or index == len(self.samples):
            return None
        # Perform linear interpolation.
        a0, v0 = self.samples[index - 1]
        a1, v1 = self.samples[index]
        return self.type(v0 + (arg - a0) / (a1 - a0) * (v1 - v0))



#-----------------------------------------------------------------------

class _Graph:

    def __init__(self, x_axis, y_axis):
        self.axes = (x_axis, y_axis)
        self.segments = []


    def __str__(self):
        return "Graph(x_axis=%r, y_axis=%r)" % self.axes


    def append(self, x0, y0, x1, y1):
        self.segments.append((x0, y0, x1, y1))



#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _binarySearch(sequence, value, compare=cmp):
    """Find the index at which to insert 'value' in a sorted sequence.

    'sequence' -- A sorted sequence.

    'compare' -- A comparison function between 'value' and an element of
    'sequence', ala 'cmp'.

    returns -- The index of 'sequence' whose element is the smallest that
    is more than 'value'."""

    # Empty sequence case.
    if len(sequence) == 0:
        return 0
    # Handle the cases of 'value' outside the range of elements of
    # 'sequence'. 
    if compare(value, sequence[0]) < 0:
        return 0
    if compare(value, sequence[-1]) > 0:
        return len(sequence) 

    # Perform binary search.
    i0 = 0
    i2 = len(sequence) - 1
    while True:
        if i2 <= i0 + 1:
            return i2
        i1 = (i0 + i2) // 2
        if compare(value, sequence[i1]) < 0:
            i2 = i1
        else:
            i0 = i1


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def isFunction(object):
    return isinstance(object, _Function) \
           or isinstance(object, _SampledFunction1D)


def Function1D(expr, arg_name=None, axis=Axis(float), **kw_args):
    """Create a function of a single argument.

    The function may be specified by an expression object or a string
    formula for one.  The expression must have exactly one symbol name
    appearing in it that does not match a keyword argument; this is
    argument name, and may be specified as 'arg_name'.

    'expr' -- The expression to evaluate the function.  May be an
    expression object, a string formula for an expression, or a
    a callable object.

    'arg_name' -- If 'expr' is an expression or string formula for one,
    the name of the argument variable.  It must be a symbol appearing in
    the expression.

    'axis' -- The axis object; or, a sequence of the form '(type, name,
    units, (lo, hi))', where items after 'type' may be omitted.

    '**kw_args' -- Keyword arguments whose names match symbols in the
    expression are interpreted as parameter values for those symbols.
    Any other keyword arguments are added as attributes to the resulting
    function object.

    returns -- A function object."""

    # Convert arguments appropriately.
    expr = hep.expr.asExpression(expr)
    axis = parseAxisArg(axis)
   
    # Make sure each of the symbols in the expression binds either to
    # the function argument or a value provided as a keyword argument.
    symbol_names = hep.expr.getSymbolNames(expr)
    parameters = {}
    for symbol_name in symbol_names:
        if symbol_name == arg_name:
            # It's the argument name.  That's fine.
            pass
        elif symbol_name in kw_args:
            # Its value was provided as a keyword argument.  Store it as
            # a parameter
            parameters[symbol_name] = popkey(kw_args, symbol_name)
        elif arg_name is None:
            # No argument name was specified.  Since we don't have a
            # value for this symbol name, optimistically assume that it
            # is the argument variable and hope that all other symbol
            # names are resolved.
            arg_name = symbol_name
        else:
            # Couldn't bind this symbol name.
            raise KeyError, \
                  "unknown symbol %s in expression" % symbol_name
    
    # Use the name of the argument variable as the axis name, if no
    # other was provided.
    if not hasattr(axis, "name"):
        axis.name = arg_name
    # Build the function.
    result = _Function1D(
        axis, expr, arg_name, parameters)
    # Set the function name.
    result.name = popkey(kw_args, "name", str(expr))
    # Set other attributes.
    result.__dict__.update(kw_args)
    # All done.
    return result


def SampledFunction1D(axis=Axis(float), **kw_args):
    axis = parseAxisArg(axis)
    type = popkey(kw_args, "type", float)
    
    result = _SampledFunction1D(axis, type)
    result.__dict__.update(kw_args)

    return result


def sampleFunction1D(function, range, number_of_samples=1000,
                     units=None):
    """Construct a sampled function from 'function' over 'range'.

    'function' -- A callable of one argument.

    'range' -- The range of values over which to sample the function.

    returns -- A 'SampledFunction1D' object."""

    # Construct the sampled function.
    axis = Axis(float, range=range)
    if units is not None:
        axis.units = units
    result = SampledFunction1D(axis)
    result.name = str(function)
    # Add samples.
    lo, hi = range
    for x in hep.num.range(lo, hi, (hi - lo) / (number_of_samples - 1)):
        result.addSample(x, function(x))

    return result


def getRange(function, x_range, number_of_samples=100):
    """Return the range of 'function' over domain 'x_range'.

    Estimates the extrema of 'function' by sampling at
    'number_of_samples' points evenly spaced over 'x_range'.

    returns -- '(y_lo, y_hi)'."""

    x_lo, x_hi = x_range
    y_lo = None
    y_hi = None
    for x in hep.num.range(x_lo, x_hi, (x_hi - x_lo) / number_of_samples):
        y = function(x)
        if y is None:
            continue
        if y_lo is None or y < y_lo:
            y_lo = y
        if y_hi is None or y > y_hi:
            y_hi = y
    return y_lo, y_hi


def makeSampled(function, num_samples=1000, range=None):
    assert function.dimensions == 1
    axis = copy.copy(function.axis)
    if not hasattr(axis, "range"):
        if range is None:
            raise ValueError, "no range specified"
        axis.range = range
    
    sampled_function = SampledFunction1D(axis)
    for attr_name in ("name", "expr", "formula", ):
        if hasattr(function, attr_name):
            setattr(sampled_function,
                    attr_name, getattr(function, attr_name))

    lo, hi = axis.range
    for x in hep.num.range(lo, hi, (hi - lo) / num_samples):
        args = { function.arg_names[0]: x }
        sampled_function.append(x, function.compiled_expr.evaluate(args))

    return sampled_function


def isGraph(object):
    return isinstance(object, _Graph)


def Graph(x_axis=Axis(float), y_axis=Axis(float), **kw_args):
    """Create a graph.

    A graph is a collection of line segments approximating curves or
    other mathematical objects.

    'x_axis', 'y_axis' -- The axis object; or, a sequence of the form
    '(type, name, units, (lo, hi))', where items after 'type' may be
    omitted.

    '**kw_args' -- Keyword arguments whose names match symbols in the
    expression are interpreted as parameter values for those symbols.
    Any other keyword arguments are added as attributes to the resulting
    function object.

    returns -- A function object."""
    # Handle sloppy axis arguments.
    x_axis = parseAxisArg(x_axis)
    y_axis = parseAxisArg(y_axis)

    graph = _Graph(x_axis, y_axis)
    graph.__dict__.update(kw_args)
    return graph


def ContourGraph(function, x, y, levels, spacing=32):
    """Construct a contour graph of a two-variable 'function'.

    Builds a contour plot (or level plot) of 'function' in two
    variables, which shows curves of constant value.

    'function' -- The function or expression whose contours are to be
    found.  The function is called with two keyword arguments, whose
    names are given in 'x' and 'y'.

    'x', 'y' -- Tuples specifying the independent variables.  Each is of
    the form '(name, lo, hi)', where 'name' is the name of the variable
    and 'lo' and 'hi' specify the range over which to compute the
    contours.

    'levels' -- A sequence of values specifying the constant levels of
    'function' to find.

    'spacing' -- The granularity of the computation.

    returns -- A 'Graph'."""

    # Parse arguments.
    x_var, x_min, x_max = x
    y_var, y_min, y_max = y
    expr = hep.expr.asExpression(function)

    # Construct an empty graph.
    graph = Graph(Axis(float, range=(x_min, x_max), name=x_var),
                  Axis(float, range=(y_min, y_max), name=y_var),
                  title="contours of %s" % function)
    # Build a callable which calls 'expr' by keyword args.
    callable = lambda x, y: expr(**{ x_var: x, y_var: y })
    # Find line segments in the contour plot.
    segments = hep.ext.contours(
        x_min, x_max, spacing, y_min, y_max, spacing, callable, levels)
    # Add them.
    graph.segments.extend(segments)

    return graph


def makeContourGraphFromHist(histogram, levels=10, spacing=None):
    """Construct a contour graph of two-dimensional 'histogram'.

    'histogram' -- A two-dimensional histogram.

    'levels' -- The number of levels to compute, or a sequence of level
    values.

    'spacing' -- The granularity of the computation, given as the number
    of sample points along each axis.

    returns -- A 'Graph' object."""

    if histogram.dimensions != 2:
        raise ValueError, "histogram must be two-dimensional"

    try:
        # Was a number of levels given?
        levels = int(levels)
    except TypeError:
        # No.  Interpret it as a sequence of level values.
        levels = map(float, levels)
    else:
        # A number of levels was given.  Space them evenly over the
        # range of bin values.
        lo, hi = util.getRange(histogram)
        interval = (hi - lo) / (levels - 1)
        levels = tuple(hep.num.range(lo, hi + interval / 2, interval))

    if spacing is None:
        # By default, use the histogram binning.
        spacing = max([ a.number_of_bins for a in histogram.axes ])

    # Construct an empty graph.
    try:
        title = histogram.title
    except AttributeError:
        title = "histogram"
    graph = Graph(histogram.axes[0], histogram.axes[1],
                  title="contours of %s" % title)

    # Build a function that returns the contents of a histogram.
    def function(x, y):
        return histogram.getBinContent(histogram.map((x, y)))

    # Compute the level graph.
    x_lo, x_hi = histogram.axes[0].range
    y_lo, y_hi = histogram.axes[1].range
    segments = hep.ext.contours(
        x_lo, x_hi, spacing, y_lo, y_hi, spacing, function, levels)
    graph.segments.extend(segments)

    return graph


