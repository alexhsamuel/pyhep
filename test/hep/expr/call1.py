"""Test simple function calls (with no keyword arguments)."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.expr
from   hep.test import compare

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def foo(x):
    return x * 2


def bar(x, y, z):
    return x * (y + 1) * (z + 2)


#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

symbols = { "x": 3, "y": 2, "z": 1, }

expr1 = hep.expr.asExpression(
    "foo(x)", types_from=symbols, compile=True, foo=foo)
hep.test.assert_(hep.expr.isCompiledExpression(expr1))
print expr1
compare(expr1.evaluate(symbols), 6)

expr2 = hep.expr.asExpression(
    "bar(x, y, z) + foo(x)", types_from=symbols, compile=True,
    foo=foo, bar=bar)
hep.test.assert_(hep.expr.isCompiledExpression(expr2))
print expr2
compare(expr2.evaluate(symbols), 33)

