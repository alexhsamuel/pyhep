#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep import test
import hep.table

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

# Open the table, and get the first row.
row = hep.table.open("table3.table")[0]
# Check that the '_dict' attribute works.
keys = list(row.keys())
keys.sort()
test.compare(keys, ["as_double", "cycle", "index", "twice"])
# Check that the 'items' method works.
items = list(row.items())
items.sort(lambda (k0, v0), (k1, v1): cmp(k0, k1))
test.compare(items, [
    ('as_double', 0.0),
    ('cycle', 16),
    ('index', 0),
    ('twice', 0)
    ])
