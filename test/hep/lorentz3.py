from   hep import test
import hep.lorentz
from   hep.lorentz import lab
from   math import sqrt

cm_frame = hep.lorentz.Frame(lab.Boost(0, 0, 0.5))
p4 = cm_frame.Momentum( 4.0,  1.0,  0.0, -1.0)
q4 = cm_frame.Momentum( 4.0, -1.0,  0.0,  1.0)
t, x, y, z = cm_frame.coordinatesOf(p4 + q4)
test.compare(t, 8.0)
test.compare(x, 0.0)
test.compare(y, 0.0)
test.compare(z, 0.0)
test.compare(p4.mass, sqrt(14.0), precision=1e-8)
test.compare(q4.mass, sqrt(14.0), precision=1e-8)
test.compare(p4 ^ q4, 18.0, precision=1e-8)

tl, xl, yl, zl = lab.coordinatesOf(p4 + q4)
test.assert_(tl > t)
test.compare(xl, 0.0)
test.compare(yl, 0.0)

