"""Test that unrecognized expressions are handled when compiled.

This test introduces a new Python expression class, 'TestExpression'.
When compiled for a table, it should be wrapped in an
"OBJECT_EXPRESSION" operation, which calls back to the Python expression
object for evaluation."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.test import compare
import hep.expr

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class TestExpression(hep.expr.Expression):

    type = int


    def evaluate(self, symbols):
        return symbols["x"] * 2


    def copy(self, copy_fn=None):
        return TestExpression()

    

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

symbols = { "x": 21 }
expression = hep.expr.compile(TestExpression())
compare(expression.evaluate(symbols), 42)

