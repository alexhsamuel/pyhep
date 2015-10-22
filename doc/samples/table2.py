import hep.table
from   math import sqrt

table = hep.table.open("tracks.table")

for track in table:
    energy = track["energy"]
    momentum = sqrt(track["p_x"] ** 2 + track["p_y"] ** 2 + track["p_z"] ** 2)
    mass = sqrt(energy ** 2 - momentum ** 2)

    print "energy=%8.6f  momentum=%8.6f  mass=%8.6f" \
          % (energy, momentum, mass)

