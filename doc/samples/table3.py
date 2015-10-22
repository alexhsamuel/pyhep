import hep.table
import hep.table.parse
from   math import sqrt

table = hep.table.open("tracks.table")

momentum = hep.expr.parse(
    "sqrt(momentum_x**2 + momentum_y**2 + momentum_z**2)")
momentum = table.compile(momentum)
print momentum

for track in table:
    energy = track["energy"]
    mass = sqrt(energy ** 2 - momentum ** 2)

    print "energy=%8.6f  momentum=%8.6f  mass=%8.6f" \
          % (energy, momentum(track), mass)

