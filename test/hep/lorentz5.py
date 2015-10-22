import hep.lorentz
from   hep.lorentz import lab
from   hep.test import compare

boost = lab.Boost(0.0, 0.0, 0.5)
moving_frame = hep.lorentz.Frame(boost)
momentum = lab.Momentum(5.0, 1.0, 0.0, -2.0)
boosted_momentum = boost ^ momentum
compare(lab.coordinatesOf(momentum),
        moving_frame.coordinatesOf(boosted_momentum),
        precision=1e-8)

