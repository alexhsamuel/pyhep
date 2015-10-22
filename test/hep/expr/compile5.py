#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.expr
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

symbols = [
    { 'x': 0, 'y': 0.0 },
    { 'x': 1, 'y': 2.0 },
    { 'x': 2, 'y': 1.0 },
    { 'x': 2, 'y': 1.5 },
    { 'x': 2, 'y': 2.5 },
    ]

print repr(hep.expr.parse("if_then(x < y, x, y)"))
expression = hep.expr.asExpression(
    "if_then(x < y, x, y)", types_from=symbols[0], compile=True)
assert hep.expr.isCompiledExpression(expression)
print expression

compare(expression.evaluate(symbols[0]), 0.0)
compare(expression.evaluate(symbols[1]), 1.0)
compare(expression.evaluate(symbols[2]), 1.0)
compare(expression.evaluate(symbols[3]), 1.5)
compare(expression.evaluate(symbols[4]), 2.0)

# Make sure the two arguments' types are coerced.
compare(type(expression.evaluate(symbols[4])), float)
