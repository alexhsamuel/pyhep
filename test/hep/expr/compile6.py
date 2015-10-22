#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.expr
from   hep.test import compare

#-----------------------------------------------------------------------
# main script
#-----------------------------------------------------------------------

i1 = 42
i2 = -4
f1 = 0.5
f2 = 3.0
symbols = { "i1": i1, "i2": i2, "f1": f1, "f2": f2 }

tests = [
    ("i1", i1),
    ("(i1)", (i1)),
    ("(i1, )", (i1, )),
    ("(i1, i2)", (i1, i2)),
    ("(i1, i2, f1, f2)", (i1, i2, f1, f2)),
    ("(i1 + 2, f1 / f2)", (i1 + 2, f1 / f2)),
    ]

for expression, expected in tests:
    compiled = hep.expr.asExpression(
        expression, types_from=symbols, compile=True)
    assert hep.expr.isCompiledExpression(compiled)
    value = compiled.evaluate(symbols)
    compare(value, expected)
    compare(type(value), type(expected))
