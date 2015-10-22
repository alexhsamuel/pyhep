#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.expr
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# main script
#-----------------------------------------------------------------------

i1 = 42
i2 = -4
f1 = 0.5
f2 = 3.0
symbols = { "i1": i1, "i2": i2, "f1": f1, "f2": f2 }

# Keep track of the number of times 'foo' was called.
foo_count = 0

# This function will be called as part of our expressions.
def foo(i1):
    # Count calls.
    global foo_count
    foo_count += 1

    assert_(i1 == 42)
    
expression1 = hep.expr.parse("i1 == 41 and foo(i1)", foo=foo)
compiled1 = hep.expr.compile(expression1)
compiled1.evaluate(symbols)
compare(foo_count, 0)

expression2 = hep.expr.parse("i1 == 42 and foo(i1)", foo=foo)
compiled2 = hep.expr.compile(expression2)
compiled2.evaluate(symbols)
compare(foo_count, 1)
