from   hep import test
import hep.lorentz
from   hep.lorentz import lab
from   math import sqrt, pi

x = lab.Vector(4.0, 0.0, 0.0, 2.0)

x1 = lab.Rotation(pi / 2, 0.0, 0.0) ^ x
test.compare(lab.coordinatesOf(x1), (4.0, 0.0, 0.0, 2.0))
test.compare(x1.norm, sqrt(12.0))

print lab.Rotation(0.0, pi / 2, 0.0).matrix
x2 = lab.Rotation(0.0, pi / 2, 0.0) ^ x
test.compare(lab.coordinatesOf(x2), (4.0, 2.0, 0.0, 0.0), precision=1e-8)
test.compare(x2.norm, sqrt(12.0))

x3 = lab.Rotation(pi / 2, pi / 2, 0.0) ^ x
test.compare(lab.coordinatesOf(x3), (4.0, 0.0, 2.0, 0.0), precision=1e-8)
test.compare(x3.norm, sqrt(12.0))
