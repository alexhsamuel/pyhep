#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.expr
from   hep.num import *
from   hep.test import compare
from   math import *

#-----------------------------------------------------------------------
# main script
#-----------------------------------------------------------------------

i1 = 42
i2 = -4
f1 = 0.5
f2 = 3.0
symbols = { "i1": i1, "i2": i2, "f1": f1, "f2": f2 }

tests = [
    ("e", e),
    ("pi", pi),
    ("abs(i1)", abs(i1)),
    ("abs(i2)", abs(i2)),
    ("abs(f1)", abs(f1)),
    ("acos(f1)", acos(f1)),
    ("asin(f2 / 4)", asin(f2 / 4)),
    ("atan(i1)", atan(i1)),
    ("atan2(f1, f2)", atan2(f1, f2)),
    ("ceil(f1)", ceil(f1)),
    ("cos(i1)", cos(i1)),
    ("cosh(i1)", cosh(i1)),
    ("exp(i2)", exp(i2)),
    ("floor(f1)", floor(f1)),
    ("gaussian(f1, f2, i2)", gaussian(f1, f2, i2)),
    ("get_bit(i1, 1)", get_bit(i1, 1)),
    ("get_bit(i1, 2)", get_bit(i1, 2)),
    ("hypot(i1, i2)", hep.num.hypot(i1, i2)),
    ("hypot(i1, i2, f1)", hep.num.hypot(i1, i2, f1)),
    ("in_range(i2, 0, i1)", in_range(i2, 0, i1)),
    ("in_range(i2, -6, i1)", in_range(i2, -6, i1)),
    ("in_range(f1, f2, i1)", in_range(f1, f2, i1)),
    ("in_range(i2, f2, f1)", in_range(i2, f2, f1)),
    ("log(i1)", log(i1)),
    ("max(i1, i2)", max(i1, i2)),
    ("max(f1, f2)", max(f1, f2)),
    ("min(i1, i2, 10, 20)", min(i1, i2, 10, 20)),
    ("min(-17.0, f1, f2, 10)", min(-17.0, f1, f2, 10)),
    ("near(40, 3, i1)", near(40, 3, i1)),
    ("near(0, 1, f2)", near(0, 1, f2)),
    ("sin(i1)", sin(i1)),
    ("sinh(i2)", sinh(i2)),
    ("sqrt(f1)", sqrt(f1)),
    ("tan(f2)", tan(f2)),
    ("tanh(f2)", tanh(f2)),
    ]

for expression, expected in tests:
    compiled = hep.expr.asExpression(
        expression, types_from=symbols, compile=True)
    assert hep.expr.isCompiledExpression(compiled)
    print compiled
    
    value = compiled.evaluate(symbols)
    compare(value, expected)
    compare(type(value), type(expected))

