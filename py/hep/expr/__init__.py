#-----------------------------------------------------------------------
#
# module hep.expr
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Compiled arithmetical expressions."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   classes import *
import compiler
from   compiler import isCompiledExpression
import expr_parser
from   hep.bool import *
import hep.ext
import inspect
import op
from   op import optimize, substitute, substituteExpressions
from   op import setTypes, setTypesFrom, setTypesFixed
import re
from   symbols import substituteConstants

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def isExpression(object):
    """Return true if 'object' is an expression object."""

    return isCompiledExpression(object) \
           or isinstance(object, Expression)


def asExpression(arg, compile=False, types=None, types_from=None, **names):
    """Interpret 'arg' as an expression.

    For maximum convenience, this function is called by (most)
    user-visible functions which take expression arguments.

    'compile' -- If true, returns a compiled expression.

    '**names' -- Values to substitute for symbol names in the
    expression.

    returns -- If 'arg' is an expression, itself; or 'arg' converted to
    an expression.

    raises -- 'TypeError' if 'arg' is not an expression and cannot be
    converted to one."""

    # If it's already an expression, just use it.
    if isExpression(arg):
        expr = arg

    # If it's a string, parse it.
    elif isinstance(arg, str):
        try:
            expr = parse(arg)
        except expr_parser.ParseError, exception:
            # Make parse exceptions more useful by including the parsed
            # string. 
            raise expr_parser.ParseError, \
                  "%s, while parsing \"%s\"" % (exception, arg)

    # If it's a function, fish out its argument names, make symbols out
    # of these, and wrap it all in a call expression.
    elif callable(arg):
        if inspect.isfunction(arg):
            # An ordinary function.
            symbol_names = inspect.getargspec(arg)[0]
        elif inspect.ismethod(arg):
            # A class method.
            symbol_names = inspect.getargspec(arg.im_func)[0]
            # If it's a bound method, skip the first ('self') argument.
            if arg.im_self is not None:
                symbol_names = symbol_names[1 :]
        elif True:
            symbol_names = ("x", )
        else:
            # Don't know how to get the symbol names.
            raise ValueError, \
                  "don't know how to get argument names for '%r'" \
                  % arg
        # Construct the expression.
        subexprs = map(Symbol, symbol_names)
        expr = Call(Constant(arg), subexprs)

    # If it's numerical, wrap it in a constant.
    elif type(arg) in (int, float, long):
        expr = Constant(arg)

    # Don't know how to handle other things.
    else:
        raise TypeError, "argument must be an expression"

    # Substitute names.
    expr = substitute(expr, **names)
    # Set types.
    if types_from is not None:
        expr = setTypesFrom(expr, **types_from)
    if types is not None:
        expr = setTypes(expr, **types)
    # Compile it, if requested.
    if compile:
        expr = compiler.compile(expr)
    # All done.
    return expr


def parse(expression_string, **names):
    expression = expr_parser.parse(expression_string)
    expression = substitute(expression, **names)
    return expression


def compile(expression, default_type=None, **types):
    """Compile 'expression'.

    'expression' -- """

    if isCompiledExpression(expression):
        # It is already compiled.  
        return expression
    expression = asExpression(expression)
    
    if default_type is not None:
        # Set default symbol types.
        expression = op.setTypesFixed(expression, None, default_type)
    if len(types) != 0:
        # Set specific symbol types.
        expression = op.setTypes(expression, **types)

    # Do the compilation.
    expression = op.optimize(expression)
    return compiler.compile(expression)


def parseFile(lines, symbols={}, expressions=None):
    if expressions is None:
        expressions = {}

    name_regex = re.compile(r"(\w+)\s*=(\s|\Z)")

    name = None
    text = None
    def finish():
        if name is None:
            return
        expression = substituteExpressions(parse(text), expressions)
        expression = substitute(expression, **symbols)
        expressions[name] = expression

    for line in lines:
        line = line.strip()
        # Trim off comments.
        if "#" in line:
            line = line[:line.index("#")]
        # Skip blank lines.
        if line.strip() == "":
            continue

        # Is this the start of a new definition?
        match = name_regex.match(line)
        if match is not None:
            finish()
            name = match.group(1)
            text = line[match.end():]

        elif name is not None:
            text += " " + line

        else:
            raise RuntimeError, "syntax error"
        
    finish()
    return expressions


def _getSymbolNames(expr, result):
    if isinstance(expr, Symbol):
        name = expr.symbol_name
        result[name] = None
    for subexpr in expr.subexprs:
        _getSymbolNames(subexpr, result)


def getSymbolNames(expr):
    """Return a list of names of symbols in 'expr'."""
    
    result = {}
    _getSymbolNames(expr, result)
    return result.keys()
