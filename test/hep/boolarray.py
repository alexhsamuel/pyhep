from   hep.bool import *
from   hep.test import compare

b = BoolArray(10)
for i in range(10):
    compare(b[i], False)
for i in range(1, 10, 2):
    b[i] = True
compare(tuple(b),
        (False, True, False, True, False, True, False, True, False, True))
