#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.table
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("x", "float32")
schema.addColumn("y", "float32")
table = hep.table.create("exception1.table", schema)
table.append(x=5, y=2)
table.append(x=3, y=4)
table.append(x=0, y=4)
table.append(x=3, y=0)
table.append(x=4, y=3)

sum = 0

def callback(value, weight):
    global sum
    assert_(weight == 1)
    sum += value

hep.table.project(table, [("x / y", callback)],
                  handle_expr_exceptions=True)

compare(sum, 5 / 2 + 3 / 4 + 0 + 4 / 3)
