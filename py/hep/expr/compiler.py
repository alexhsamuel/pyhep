#-----------------------------------------------------------------------
#
# module hep.expr.compile
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Expression compiler."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   classes import *
from   hep import ext
from   hep.bool import *
import hep.num
import hep.py
import math
import op
import os
import sys

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

operation_map = {
    (Add, None, (None, None)): "OBJECT_ADD",
    (Add, float, (float, float)): "DOUBLE_ADD",
    (Add, int, (int, int)): "LONG_ADD",
    (BitwiseAnd, int, (int, int)): "LONG_BITWISE_AND",
    (BitwiseNot, int, (int, )): "LONG_BITWISE_NOT",
    (BitwiseOr, int, (int, int)): "LONG_BITWISE_OR",
    (BitwiseXor, int, (int, int)): "LONG_BITWISE_XOR",
    (Divide, None, (None, None)): "OBJECT_DIVIDE",
    (Divide, float, (float, float)): "DOUBLE_DIVIDE",
    (Equal, bool, (float, float)): "BOOL_EQUALS_DOUBLE",
    (Equal, bool, (int, int)): "BOOL_EQUALS_LONG",
    (Equal, bool, (None, None)): "BOOL_EQUALS_OBJECT",
    (FloorDivide, None, (None, None)): "OBJECT_FLOOR_DIVIDE",
    (FloorDivide, int, (int, int)): "LONG_FLOOR_DIVIDE",
    (LeftShift, int, (int, int)): "LONG_SHIFT_LEFT",
    (LessThan, bool, (float, float)): "BOOL_LESS_THAN_DOUBLE",
    (LessThan, bool, (int, int)): "BOOL_LESS_THAN_LONG",
    (LessThanOrEqual, bool, (float, float)): "BOOL_LESS_THAN_OR_EQUAL_DOUBLE",
    (LessThanOrEqual, bool, (int, int)): "BOOL_LESS_THAN_OR_EQUAL_LONG",
    (Minus, float, (float, )): "DOUBLE_NEGATE",
    (Minus, int, (int, )): "LONG_NEGATE",
    (Minus, None, (None, )): "OBJECT_NEGATE",
    (Multiply, None, (None, None)): "OBJECT_MULTIPLY",
    (Multiply, float, (float, float)): "DOUBLE_MULTIPLY",
    (Multiply, int, (int, int)): "LONG_MULTIPLY",
    (Not, bool, (bool, )): "BOOL_NOT",
    (Power, None, (None, None)): "OBJECT_EXPONENTIATE",
    (Power, float, (float, float)): "DOUBLE_EXPONENTIATE",
    (Power, int, (int, int)): "LONG_EXPONENTIATE",
    (Remainder, None, (None, None)): "OBJECT_REMAINDER",
    (Remainder, float, (float, float)): "DOUBLE_REMAINDER",
    (Remainder, int, (int, int)): "LONG_REMAINDER",
    (RightShift, int, (int, int)): "LONG_SHIFT_RIGHT",
    (Subscript, None, (None, None)): "OBJECT_SUBSCRIPT",
    (Subtract, None, (None, None)): "OBJECT_SUBTRACT",
    (Subtract, float, (float, float)): "DOUBLE_SUBTRACT",
    (Subtract, int, (int, int)): "LONG_SUBTRACT",
    }

# These built-in functions have return types which vary based on their
# argument types.
function_map_1 = {
    (abs, (float, )): (float, "DOUBLE_ABS"),
    (abs, (int, )): (int, "LONG_ABS"),
    (bool, (None, )): (bool, "BOOL_CAST_FROM_OBJECT"),
    (bool, (bool, )): (bool, "NO_OPERATION"),
    (bool, (float, )): (bool, "BOOL_CAST_FROM_DOUBLE"),
    (bool, (int, )): (bool, "BOOL_CAST_FROM_LONG"),
    (float, (None, )): (float, "DOUBLE_CAST_FROM_OBJECT"),
    (float, (float, )): (float, "NO_OPERATION"),
    (float, (int, )): (float, "DOUBLE_CAST_FROM_LONG"),
    (hep.num.in_range, (float, float, float)): (bool, "BOOL_IN_RANGE_DOUBLE"),
    (hep.num.in_range, (int, int, int)): (bool, "BOOL_IN_RANGE_LONG"),
    (hep.num.near, (float, float, float)): (bool, "BOOL_NEAR_DOUBLE"),
    (hep.num.near, (int, int, int)): (bool, "BOOL_NEAR_LONG"),
    (int, (None, )): (int, "LONG_CAST_FROM_OBJECT"),
    (int, (float, )): (int, "LONG_CAST_FROM_DOUBLE"),
    (int, (int, )): (int, "NO_OPERATION"),
    (max, (float, float)): (float, "DOUBLE_MAX"),
    (max, (int, int)): (int, "LONG_MAX"), 
    (min, (float, float)): (float, "DOUBLE_MIN"),
    (min, (int, int)): (int, "LONG_MIN"),
    }

# These built-in function have fixed argument and return types.
function_map_2 = {
    (hep.num.gaussian, 3): (float, "DOUBLE_GAUSSIAN"),
    (hep.num.get_bit, 2): (bool, "LONG_GET_BIT"),
    (hep.num.hypot, 2): (float, "DOUBLE_HYPOT"),
    (math.acos, 1): (float, "DOUBLE_ACOS"),
    (math.asin, 1): (float, "DOUBLE_ASIN"),
    (math.atan, 1): (float, "DOUBLE_ATAN"),
    (math.atan2, (float, float)): (float, "DOUBLE_ATAN2"),
    (math.ceil, 1): (float, "DOUBLE_CEIL"),
    (math.cos, 1): (float, "DOUBLE_COS"),
    (math.cosh, 1): (float, "DOUBLE_COSH"),
    (math.exp, 1): (float, "DOUBLE_EXP"),
    (math.floor, 1): (float, "DOUBLE_FLOOR"),
    (math.log, 1): (float, "DOUBLE_LOG"),
    (math.sin, 1): (float, "DOUBLE_SIN"),
    (math.sinh, 1): (float, "DOUBLE_SINH"),
    (math.sqrt, 1): (float, "DOUBLE_SQRT"),
    (math.tan, 1): (float, "DOUBLE_TAN"),
    (math.tanh, 1): (float, "DOUBLE_TANH"),
    }

cast_map = {
    (None, bool): "OBJECT_CAST_FROM_BOOL",
    (None, float): "OBJECT_CAST_FROM_DOUBLE",
    (None, int): "OBJECT_CAST_FROM_LONG",
    (bool, None): "BOOL_CAST_FROM_OBJECT",
    (bool, float): "BOOL_CAST_FROM_DOUBLE",
    (bool, int): "BOOL_CAST_FROM_LONG",
    (float, None): "DOUBLE_CAST_FROM_OBJECT",
    (float, bool): "DOUBLE_CAST_FROM_BOOL",
    (float, int): "DOUBLE_CAST_FROM_LONG",
    (int, None): "LONG_CAST_FROM_OBJECT",
    (int, bool): "LONG_CAST_FROM_BOOL",
    (int, float): "LONG_CAST_FROM_DOUBLE",
    }

symbol_map = {
    bool: "BOOL_SYMBOL",
    # FIXME: Support complex operations directly.
    complex: "OBJECT_SYMBOL",
    float: "DOUBLE_SYMBOL",
    int: "LONG_SYMBOL",
    None: "OBJECT_SYMBOL",
    }

cache_get_operation_map = {
    float: "FLOAT_CACHE_GET",
    int: "INT_CACHE_GET",
    bool: "BOOL_CACHE_GET",
    }

cache_set_operation_map = {
    float: "FLOAT_CACHE_SET",
    int: "INT_CACHE_SET",
    bool: "BOOL_CACHE_SET",
    }


#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _compileCachedExpression(expression, compiled):
    type = expression.type
    get_operation = cache_get_operation_map[type]
    set_operation = cache_set_operation_map[type]
    # Get the memory buffers holding the cache mask and cached values.
    mask, values = expression.cache
    mask_info = mask.buffer_info()
    values_info = values.buffer_info()
    # They should be the same length.
    assert mask_info[1] == values_info[1]
    # Compile the cached expression off to the side.  It gets evaluated
    # only when the cache mask bit is not set.
    subexpr_compiled = ext.Expr()
    _compile(expression.subexprs[0], subexpr_compiled)
    # Add an operation to set the value in the cache.
    subexpr_compiled.append(set_operation, type, mask_info[0],
                            values_info[0], values_info[1], )
    # Put the operation to check the cache value here.  It will skip the
    # actual expression if the cache contains a value.
    compiled.append(get_operation, type, mask_info[0], values_info[0],
                    values_info[1], subexpr_compiled.length)
    # Now add the actual expression.
    compiled.extend(subexpr_compiled)


def _compileIfThen(expression, compiled):
    if len(expression.subexprs) != 3:
        raise ValueError, "if_then must take three arguments"
    condition_expr, true_expr, false_expr = expression.subexprs

    # The result should be of the same type, no matter which case is
    # chosen.  Coerce the two cases' types, and add casts as necessary.
    type = coerceExprTypes((true_expr, false_expr, ))
    if true_expr.type != type:
        true_expr = Cast(type, true_expr)
    if false_expr.type != type:
        false_expr = Cast(type, false_expr)
    
    # Compile the cases off to the side.
    true_compiled = ext.Expr()
    _compile(true_expr, true_compiled)
    false_compiled = ext.Expr()
    _compile(false_expr, false_compiled)

    # First, we evaluate the condition.
    _compile(condition_expr, compiled)
    # If it's true, we skip over the next instructions, which would
    # have evaluated the value if the condition were false.
    compiled.append("CONDITIONAL_JUMP", None, false_compiled.length + 1)
    compiled.extend(false_compiled)
    # We just evaluate the false value.  Jump over the next
    # instructions, which would have evaluated the value if the
    # condition were true.
    compiled.append("JUMP", type, true_compiled.length)
    # Now the instructions that evaluate the true value.
    compiled.extend(true_compiled)


def _compile(expression, compiled):
    type = expression.type
    subexprs = list(expression.subexprs)
    subexpr_types = tuple(expression.subexpr_types)
    operation = None
    args = ()

    # Handle 'And' and 'Or' expressions specially.  Their
    # lazy-evaluation semantics require special handling of the compiled
    # subexpressions. 
    if isinstance(expression, And) or isinstance(expression, Or):
        if isinstance(expression, And):
            operation = "BOOL_AND_LAZY"
        else:
            operation = "BOOL_OR_LAZY"
        subexpr1, subexpr2 = subexprs
        # Go ahead and compile the first subexpression.  It will always
        # be evaluated.
        _compile(subexpr1, compiled)
        # Compile the second subexpression off to the side.  It gets
        # evaluated only if the first one is true for 'And' / false for
        # 'Or'. 
        subexpr2_compiled = ext.Expr()
        _compile(subexpr2, subexpr2_compiled)
        # Stick the lazy-evaluation operation between the
        # subexpressions.  The argument is the number of operations that
        # should be skipped if the second subexpression needn't be
        # evaluated.
        compiled.append(operation, bool, subexpr2_compiled.length)
        # Now tack on the second subexpression.
        compiled.extend(subexpr2_compiled)
        return

    # Compile a 'CachedExpression'.
    import hep.table
    if isinstance(expression, hep.table.CachedExpression):
        _compileCachedExpression(expression, compiled)
        return

    # Compile an 'if_then call.
    if isinstance(expression, Call) \
       and isinstance(expression.function, Constant) \
       and expression.function.value == hep.num.if_then:
        _compileIfThen(expression, compiled)
        return

    # Compile casts.
    if isinstance(expression, Cast):
        subexpr_type, = subexpr_types
        operation = cast_map[(type, subexpr_type)]

    # Compile a 'Constant' into a 'PUSH' operation.
    elif isinstance(expression, Constant):
        operation = "PUSH"
        args = (expression.value, )

    # Compile a 'Symbol' operation.
    elif isinstance(expression, Symbol):
        name = expression.symbol_name
        operation = symbol_map[type]
        args = (ext.get_symbol_index(name), )

    elif isinstance(expression, Function):
        operation = "OBJECT_FUNCTION_CALL"
        column_dict = {}
        for arg_name in expression.arg_names:
            column_dict[arg_name] = ext.get_symbol_index(arg_name)
        args = (expression.function, column_dict, )
    
    elif isinstance(expression, Call) \
         and len(expression.kw_args) == 0:
        if isinstance(expression.function, Constant):
            function = expression.function.value
            # Match 'function' to functions with specific argument types.
            result = function_map_1.get((function, subexpr_types), None)
            if result is not None:
                type, operation = result
            # Match 'function' to functions with specific numbers of
            # arguments.  
            if operation is None:
                result = function_map_2.get(
                    (function, len(subexpr_types)), None)
                if result is not None:
                    type, operation = result

        if operation is None:
            operation = "OBJECT_SIMPLE_CALL"
            args = (len(subexprs), )
            subexprs.insert(0, expression.function)

    elif isinstance(expression, GetAttribute):
        if isinstance(subexprs[1], Constant):
            operation = "OBJECT_GET_ATTR_CONST"
            args = (subexprs.pop().value, )

    # Now handle more general cases, based on lookup tables.
    if operation is None:
        # Look for an operation that matches the expression class, the
        # expression type, and the subexpression type.
        operation = operation_map.get(
            (expression.__class__, type, subexpr_types), None)

    # Have we found an operation for this expression?
    if operation is None:
        # No match.  We'll go with the Python expression.  For this, we
        # don't compile subexpressions.
        compiled.append("OBJECT_EXPRESSION", None, expression.evaluate)
        if type is not None:
            compiled.append(cast_map[(type, None)], type)
        return

    # Compile subexpressions.  Do this in reverse order, since operators
    # take their arguments left-to-right from the top of the stack down.
    subexprs.reverse()
    for subexpr in subexprs:
        _compile(subexpr, compiled)

    # Now the main operation.
    if operation == "NO_OPERATION":
        return

    args = (operation, type, ) + args
    compiled.append(*args)


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def isCompiledExpression(expression):
    """Return true if 'expression' is a compiled expression."""
    
    return isinstance(expression, ext.Expr)


def compile(expression):
    """Compile 'expression'

    'expression' -- An expression object.  This function does not accept
    strings, functions, or other types that are elsewhere converted
    automatically into expressions.

    returns -- A compiled expression."""

    if isCompiledExpression(expression):
        # It is already compiled.  
        return expression

    # Make the compiled expression.
    compiled = ext.Expr()
    _compile(expression, compiled)
    # Store the string representation as the expression formula.
    compiled.formula = str(expression)
    # All done.
    return compiled


#-----------------------------------------------------------------------
# script
#-----------------------------------------------------------------------

if __name__ == "__main__":
    import hep.expr

    expression = sys.argv[1]
    symbols = {}
    for arg in sys.argv[2:]:
        key, value = arg.split("=")
        value = eval(value)
        symbols[key] = value

    expression = hep.expr.asExpression(expression)
    print expression
    expression = hep.expr.op.setTypesFrom(expression, **symbols)
    print expression
    compiled = hep.expr.compile(expression)
    print compiled, "->", compiled.type

    try:
        value = compiled.evaluate(symbols)
    except KeyError:
        print 'could not evaluate'
    else:
        print 'result =', value
