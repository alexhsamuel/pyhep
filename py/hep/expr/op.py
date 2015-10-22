#-----------------------------------------------------------------------
#
# module hep.expr.op
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Expression operations and optimizations."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
from   hep.expr import *
import hep.lorentz
import hep.num
import math

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

builtin_names = {
    "False":    False,
    "Frame":    hep.lorentz.Frame,
    "None":     None,
    "True":     True,
    "abs":      abs,
    "acos":     math.acos,
    "asin":     math.asin,
    "atan":     math.atan,
    "atan2":    math.atan2,
    "azimuth":  hep.lorentz.azimuth,
    "bool":     bool,
    "ceil":     math.ceil,
    "cos":      math.cos,
    "cos_azimuth": hep.lorentz.cos_azimuth,
    "cosh":     math.cosh,
    "e":        math.e,
    "exp":      math.exp,
    "float":    float,
    "floor":    math.floor,
    "gaussian": hep.num.gaussian,
    "get_bit":  hep.num.get_bit,
    "hypot":    hep.num.hypot,
    "if_then":  hep.num.if_then,
    "in_range": hep.num.in_range,
    "int":      int,
    "lab":      hep.lorentz.lab,
    "log":      math.log,
    "max":      max,
    "min":      min,
    "near":     hep.num.near,
    "pi":       math.pi,
    "sin":      math.sin,
    "sinh":     math.sinh,
    "sqrt":     math.sqrt,
    "tan":      math.tan,
    "tanh":     math.tanh,
    }


builtin_functions = {
    hep.num.gaussian: (float, (float, float, float, )),
    hep.num.get_bit: (bool, (int, int, )),
    math.acos: (float, (float, )),
    math.asin: (float, (float, )),
    math.atan: (float, (float, )),
    math.atan2: (float, (float, float, )),
    math.ceil: (float, (float, )),
    math.cos: (float, (float, )),
    math.cosh: (float, (float, )),
    math.exp: (float, (float, )),
    math.floor: (float, (float, )),
    math.log: (float, (float, )),
    math.sin: (float, (float, )),
    math.sinh: (float, (float, )),
    math.sqrt: (float, (float, )),
    math.tan: (float, (float, )),
    math.tanh: (float, (float, )),
    }


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def getFunctionSignature(function, args):
    """Find the parameter types and return types for a function call.

    'function' -- A Python function.

    'args' -- A sequence of expressions for the function's arguments.

    returns -- A pair '(return_type, parameter_types)', where
    'return_type' is the type returned by 'function' called on 'args',
    and 'parameter_types' is a sequence of types to which the 'args'
    should be cast to match the function's parameters."""
    
    function_name = function.__name__
    arg_types = [ arg.type for arg in args ]

    if function in builtin_functions:
        return_type, parameter_types = builtin_functions[function]
    elif function == abs:
        return_type = arg_types[0]
        parameter_types = (return_type, )
    elif function in (min, max):
        return_type = coerceExprTypes(args)
        parameter_types = len(arg_types) * (return_type, )
    elif function == hep.num.if_then:
        return_type = coerceExprTypes((args[1], args[2], ))
        parameter_types = (bool, return_type, return_type, )
    elif function == hep.num.in_range:
        return_type = bool
        parameter_types = 3 * (coerceExprTypes((args[0], args[2])), )
    elif function == hep.num.near:
        return_type = bool
        parameter_types = 3 * (coerceExprTypes((args[0], args[1])), )
    elif function == hep.num.hypot:
        return_type = float
        parameter_types = len(arg_types) * (float, )
    elif function in (int, float, bool):
        return_type = function
        parameter_types = arg_types
    else:
        return None, len(arg_types) * (None, )

    if len(arg_types) != len(parameter_types):
        raise TypeError, "%s requires %d arguments" \
              % (function_name, len(parameter_types))

    return return_type, parameter_types


def optimize(expression):
    try:
        # Attempt to evaluate the expression using an empty symbol table.
        constant_value = expression.evaluate({})
    except (KeyError, AttributeError):
        # Didn't work; probably an unbound symbol. 
        pass
    else:
        # Remember the expression type.
        expr_type = expression.type
        # The evaluation succeeded, so it must be a constant.  Use this
        # value instead of the expression.
        expression = Constant(constant_value)
        # Make sure the optimized result is of the same type as the
        # original expression.  If not, add a cast.
        if expression.type != expr_type:
            expression = Cast(expr_type, expression)

    # Copy the expression, optimizing subexpressions.
    expression = expression.copy(optimize)

    return expression


def substitute(expression, **names):
    """Substitute values for symbols.

    'expression' -- An 'Expression' object.

    '**names' -- Assignments from names to arbitrary values.

    returns -- A copy of 'expression' in which symbols whose names match
    names in '**names' are replaced by constants of the corresponding
    value."""

    expression = expression.copy(lambda e: substitute(e, **names))
    if isinstance(expression, Symbol):
        name = expression.symbol_name
        if name in names:
            value = names[name]
            if isinstance(value, Expression):
                expression = value
            else:
                expression = Constant(names[name])
    return expression


def _expandCalls(expression):
    # A few functions, 'min', 'max', 'hypot', take two or more
    # arguments.  Do we have one of these calls with more than two
    # arguments? 
    if isinstance(expression, Call) \
       and isinstance(expression.function, Constant) \
       and expression.function.value in (min, max, hep.num.hypot) \
       and len(expression.subexprs) > 2:
        function = expression.function
        # For later convenience, expand it into nested calls of two
        # arguments apiece.
        subexprs = list(expression.subexprs)
        subexpr_type = expression.type
        # Start with the last expression.
        expression = subexprs.pop()
        while len(subexprs) > 0:
            # Take the next-last expression.
            subexpr = subexprs.pop()
            # Combine it with the previous running result.
            expression = Call(
                function, (subexpr, expression),
                type=subexpr_type)
            expression.subexpr_types = (subexpr_type, subexpr_type)
            # Rexpand, as necessary.
            expression = expand(expression)

    return expression


def _expandCasts(expression):
    subexprs = list(expression.subexprs)
    subexpr_types = expression.subexpr_types

    for i in range(len(subexprs)):
        if subexprs[i].type != subexpr_types[i]:
            subexprs[i] = Cast(subexpr_types[i], subexprs[i])

    expression.subexprs = subexprs

    return expression


def _expandAll(expression):
    expression = substitute(expression, **builtin_names)
    # FIXME
    # expression = _expandCalls(expression)
    expression = _expandCasts(expression)
    return expression


def expand(expression):
    expression = _expandAll(expression)
    return expression


def substituteExpressions(expression, expr_map):
    """Replace symbols with subexpressions.

    'expression' -- An 'Expression' object.

    'expr_map' -- A map from expression names to expressions.

    returns -- A copy of 'expression'.  Any symbol in 'expression' whose
    name is a key in 'expr_map' is replaced with the corresponding
    expression."""
    
    # Use this function to expand subexpressions.
    copy_fn = lambda e: substituteExpressions(e, expr_map)
    # Is this a symbol with a name in 'expr_map'?
    if isinstance(expression, Symbol):
        name = expression.symbol_name
        if name in expr_map:
            # Yes.  Return a copy of the expression we found.
            return expr_map[name].copy(copy_fn)
    # Fall through: just copy it.
    return expression.copy(copy_fn)


def setTypes(expression, **types):
    """Set symbol types from 'types'.

    '**types' -- A map from symbol names to types.

    returns -- A copy of 'expression'.  Any symbol in 'expression' whose
    name is in 'types' is replaced by a new symbol expression with
    the same name and with its type given by 'types'."""

    # Make sure values in 'types' are types.
    for name, value in types.items():
        if type(value) is not type:
            raise TypeError, "value for '%s' is not a type" % name
    # Is this a symbol whose name is in 'types'?
    if isinstance(expression, Symbol):
        name = expression.symbol_name
        if name in types:
            # Yes.  Create a new symbol using this type info.
            return Symbol(name, types[name])
    # Fall through: just copy it.
    return expression.copy(lambda e: setTypes(e, **types))

            
def setTypesFrom(expression, **symbols):
    """Set symbol types from values in 'symbols'.

    'symbols' -- A map from symbol names to values.

    returns -- A copy of 'expression'.  Any symbol in 'expression' whose
    name is in 'symbols' is replaced by a new symbol expression
    with the same name and with its type that of the value in
    'symbols'."""

    # Construct the type map.
    types = {}
    for name, value in symbols.items():
        types[name] = type(value)
    return setTypes(expression, **types)


def setTypesFixed(expression, symbol_names, type):
    """Set types of all 'symbol_names' in 'expression' to 'type'.

    'symbol_names' -- A sequence of names of symbols whose type is to be
    changed to 'type'.  If 'None', set all symbol types to 'type'.

    returns -- A copy of expression.  The type of any symbol whose name
    is in 'symbol_names' is set to 'type'."""

    # Is this a symbol whose name is in 'type_map'?
    if isinstance(expression, Symbol):
        name = expression.symbol_name
        if symbol_names is None or name in symbol_names:
            # Yes.  Create a new symbol using this type info.
            return Symbol(name, type)
    # Fall through: just copy it.
    return expression.copy(lambda e: setTypesFixed(e, symbol_names, type))


