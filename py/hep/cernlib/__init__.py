#-----------------------------------------------------------------------
#
# module hep.cernlib
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""CERNLIB library interface."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import ext
from   hep import popkey
from   hep.bool import *

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def integrate(function, *region, **kw_args):
    """Numerically integrate 'function'.

    Performs multidimensional numerical integration of 'function' over a
    rectangular integration 'region'.

    'function' -- A callable or expression.

    '*region' -- One-dimensional ranges specifying a rectangular
    integration region.  Each range is a tuple of the form '(var_name,
    lo, hi)', where 'var_name' is the name of the integration variable
    and 'lo' and 'hi' are 'float' values specifying the interval to
    integrate over.

    'accuracy' -- Specify the desired accuracy with this keyword
    argument.

    returns -- The integral value."""

    # If 'function' isn't already callable, treat it as an expression. 
    import hep.expr
    if not callable(function):
        function = hep.expr.asExpression(function)

    if hep.expr.isExpression(function) \
       and not hep.expr.isCompiledExpression(function):
        function = hep.expr.setTypesFixed(function, None, float)
        function = hep.expr.compile(function)

    accuracy = float(popkey(kw_args, "accuracy", 1e-8))
    if len(kw_args) > 0:
        raise TypeError, \
              "'integrate' got an unexpected keyword argument '%s'" \
              % kw_args.keys()[0]

    # Perform the integration.
    return ext.integrate(function, region, accuracy)


