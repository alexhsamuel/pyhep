#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.expr
from   hep.test import compare

#-----------------------------------------------------------------------
# main script
#-----------------------------------------------------------------------

i1 = 42
f1 = 0.5
f2 = 3.0
symbols = { "i1": i1, "f1": f1, "f2": f2 }

tests = [
    ("40 < i1 < 45", True),
    ("40 < i1 < 42", False),
    ("40 < i1 <= 42", True),
    ("42 < i1 < 45", False),
    ("42 <= i1 < 45", True),
    ("42 <= i1 <= 42", True),
    ("1 > f1 > 0", True),
    ("1 > f1 == 0", False),
    ("1 > f1 == f2 / 6", True),
    ("3.1 > f2 > 2.9", True),
    ("3.1 > f2 >= 3.0", True),
    ]

for expression, expected in tests:
    compiled = hep.expr.asExpression(
        expression, types_from=symbols, compile=True)
    assert hep.expr.isCompiledExpression(compiled)
    value = compiled.evaluate(symbols)
    compare(value, expected)

