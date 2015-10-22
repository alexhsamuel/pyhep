from   hep.expr import *
from   hep.test import compare

compare(
    Add(Symbol('x'), Symbol('y')),
    parse("x + y")
    )

compare(
    And(LessThan(Symbol('x'), Constant(10)),
        Equal(Symbol('y'), Subtract(Symbol('z'), Constant(3.0)))),
    parse("x < 10 and y == z - 3.0")
    )

