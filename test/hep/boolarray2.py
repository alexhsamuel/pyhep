# Note: Using cPickle here causes problems with the __reduce__ method on
# amd64.  Use pickle instead.
# from   cPickle import dumps, loads
from   pickle import dumps, loads
from   hep.bool import *
from   hep.test import compare

array = BoolArray(10)
array[3] = True
array[7] = True
array[8] = True
pickle = dumps(array)
del array

array = loads(pickle)
compare(
    tuple(array),
    ( False, False, False, True, False, False, False, True, True, False ))
