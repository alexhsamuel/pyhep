#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   __future__ import division
from   hep.bool import *
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
    ("-17", -17),
    ("982.9283", 982.9283),
    ("i1", i1),
    ("f1", f1),
    ("-i2", -i2),
    ("-f2", -f2),
    ("i1 + i2", i1 + i2),
    ("f1 + f2", f1 + f2),
    ("i1 + f1", i1 + f1),
    ("i2 - i1", i2 - i1),
    ("f2 - f1", f2 - f1),
    ("f2 - i2", f2 - i2),
    ("i1 * i2", i1 * i2),
    ("f1 * f2", f1 * f2),
    ("i1 * f1", i1 * f1),
    ("i1 / i2", i1 / i2),
    ("f2 / f1", f2 / f1),
    ("f2 / i2", f2 / i2),
    ("i1 // i2", i1 // i2),
    ("i1 % i2", i1 % i2),
    ("f2 % f1", f2 % f1),
    ("i2 % f2", i2 % f2),
    ("i1 ** 2", i1 ** 2),
    ("2 ** i2", 2 ** i2),
    ("f1 ** f2", f1 ** f2),
    ("i1 ** f1", i1 ** f1),
    ("i1 << 2", i1 << 2),
    ("i2 >> 2", i2 >> 2),
    ("~i2", ~i2),
    ("i1 & 24", i1 & 24),
    ("i1 | 24", i1 | 24),
    ("i1 ^ 24", i1 ^ 24),
    ("i1 > i2", i1 > i2),
    ("i1 < i2", i1 < i2),
    ("i1 > i1", i1 > i1),
    ("i1 >= i2", i1 >= i2),
    ("i1 <= i2", i1 <= i2),
    ("i1 <= i1", i1 <= i1),
    ("i1 == i1", i1 == i1),
    ("i1 == 41", i1 == 41),
    ("i2 != -4", i2 != -4),
    ("f1 > f2", f1 > f2),
    ("f1 < f2", f1 < f2),
    ("f1 > f1", f1 > f1),
    ("f1 >= f2", f1 >= f2),
    ("f1 <= f2", f1 <= f2),
    ("f1 >= f1", f1 >= f1),
    ("f1 == f1", f1 == f1),
    ("f1 == 0.5", f1 == 0.5),
    ("f1 == 3.0", f1 == 3.0),
    ("f2 != 3.0", f2 != 3.0),
    ("f2 != 0.5", f2 != 0.5),
    ("(f1 == f2) and (i1 == i2)", (f1 == f2) and (i1 == i2)),
    ("(f1 != f2) and (i1 != i2)", (f1 != f2) and (i1 != i2)),
    ("(f1 == f2) and (f1 == i1) and (f1 == i2)",
     (f1 == f2) and (f1 == i1) and (f1 == i2)),
    ("(f1 == f2) or (i1 == i2)", (f1 == f2) or (i1 == i2)),
    ("(f1 != f2) or (i1 != i2)", (f1 != f2) or (i1 != i2)),
    ("(f1 == f2) or (f1 == i1) or (f1 == i2)",
     (f1 == f2) or (f1 == i1) or (f1 == i2)),
    ]

for expression, expected in tests:
    compiled = hep.expr.asExpression(
        expression, types_from=symbols, compile=True)
    assert hep.expr.isCompiledExpression(compiled)
    value = compiled.evaluate(symbols)
    compare(value, expected)
    # Integer exponentiation produces a 'float' expression, even though
    # for certain exponents (i.e. positive ones) the Python result might
    # be an 'int'. 
    if expression in ("i1 ** 2", "2 ** i2"):
        expected_type = float
    else:
        expected_type = type(expected)
    compare(type(value), expected_type)


