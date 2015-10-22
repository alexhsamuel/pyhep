# PyHEP XFAIL
# 'Graph' has not been updated to new 'hep.draw' yet.

import hep.draw.postscript
import hep.hist
import hep.hist.plot

ps = hep.draw.postscript.EPSFile("contour1.eps", (0.1, 0.1))
graph = hep.hist.ContourGraph(
    "-2 * x ** 2 - 0.5 * y ** 3 + 4 * x * y", ("y", -8, 8), ("x", -8, 8),
    levels=range(-50, 51, 5))
ps.render(graph)
