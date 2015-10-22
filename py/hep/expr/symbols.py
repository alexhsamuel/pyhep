#-----------------------------------------------------------------------
#
# module hep.expr.symbols
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Standard mathematical symbols."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   classes import *
from   hep.bool import *
import hep.num
import math

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

math_constants = {
    "abs": abs,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan2,
    "ceil": math.ceil,
    "complex": complex,
    "cos": math.cos,
    "cosh": math.cosh,
    "e": math.e,
    "exp": math.exp,
    "float": float,
    "floor": math.floor,
    "gaussian": hep.num.gaussian,
    "get_bit": hep.num.get_bit,
    "hypot": hep.num.hypot,
    "if_then": hep.num.if_then,
    "in_range": hep.num.in_range,
    "int": int,
    "log": math.log,
    "max": max,
    "min": min,
    "near": hep.num.near,
    "pi": math.pi,
    "sin": math.sin,
    "sinh": math.sinh,
    "sqrt": math.sqrt,
    "tan": math.tan,
    "tanh": math.tanh,
    }

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def _substituteConstants(expression, constants):
    """Attempt to replace symbol 'expression' with a constant.

    If 'expression' is a 'Symbol' whose name is a key in 'constants',
    returns a 'Constant' with the corrpesonding value from 'constants'.
    Otherwise returns a copy of 'expression'."""
    
    if isinstance(expression, Symbol):
        name = expression.symbol_name
        if name in constants:
            return Constant(constants[name])
    return expression.copy(lambda e: _substituteConstants(e, constants))


def substituteConstants(expression, constants={}, use_math=True):
    """Return a copy of 'expression' with constant substitution.

    Returns a copy of 'expression' with 'Symbol' subexpressions replaced
    with 'Constant' subexpressions.  Symbol names and corresponding
    constant values are taken from 'constants'.  If 'use_math' is true,
    standard math functions are included too."""

    # Copy the supplied dictionary.
    constants = dict(constants)
    # Include math constants, if requested.
    if use_math:
        constants.update(math_constants)
    # Perform substitution.
    return _substituteConstants(expression, constants)


