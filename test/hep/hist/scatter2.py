#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import cPickle
import hep.hist
from   hep.test import compare

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

# Create a scatter.
scatter = hep.hist.Scatter(
    (int, "track multiplicity"), (float, "missing energy", "GeV"),
    title="trigger distribution")

scatter.accumulate((5, 1.4))
scatter.accumulate((4, 1.1))
scatter << (6, 0.85)
scatter << (3, 0.66)

# Save and delete the scatter.
cPickle.dump(scatter, file("scatter2.pickle", "w"))
del scatter

# Reload the scatter.
scatter = cPickle.load(file("scatter2.pickle"))

# Check its contents.
compare(scatter.axes[0].type, int)
compare(scatter.axes[0].name, "track multiplicity")
compare(scatter.axes[1].type, float)
compare(scatter.axes[1].name, "missing energy")
compare(scatter.axes[1].units, "GeV")
compare(len(scatter.points), 4)

points = list(scatter.points)
points.sort(lambda p0, p1: cmp(p0[0], p1[0]),)
compare(tuple(points[0]), (3, 0.66))
compare(tuple(points[1]), (4, 1.10))
compare(tuple(points[2]), (5, 1.40))
compare(tuple(points[3]), (6, 0.85))

