from   hep import test
import hep.lorentz
from   hep.lorentz import lab
from   math import sqrt

p4 = lab.Momentum(5.0, 3.0, 2.0, 1.0)
test.compare(p4.mass, sqrt(11.0))
q4 = lab.Momentum(5.0, -3.0, -2.0, -1.0)
test.compare(q4.mass, sqrt(11.0))
test.compare(type(p4 + q4), hep.lorentz.Momentum)
