from   hep import test
from   hep.lorentz import lab
from   math import sqrt

x4 = lab.Vector(5.0, 3.0, 2.0, 1.0)
t, x, y, z = lab.coordinatesOf(x4)
test.compare(t, 5.0)
test.compare(x, 3.0)
test.compare(y, 2.0)
test.compare(z, 1.0)
test.compare(x4.norm, sqrt(11.0))

y4 = 2 * lab.Vector(4.0, -2.0, -1.0, 0.0)
t, x, y, z = lab.coordinatesOf(x4 + y4)
test.compare(t, 13.0)
test.compare(x, -1.0)
test.compare(y, 0.0)
test.compare(z, 1.0)

test.compare(x4 ^ y4, 56.0)
