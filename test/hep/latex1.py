#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.latex import *
from   hep.num import Statistic
import os
import sys

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

table = Table(
    TextColumn("Label", "center"),
    StatisticColumn("Stat 1", 0, 2, "%"),
    StatisticColumn("Stat 2", 1, 2, 1),
    PatternColumn("Pattern 1", "B |<xxxxxx| M |>xxxxxx| E"),
    )

table.append("first row",  "1.0000+-.120", " 100+-2.1", ("apple", "water"))
table.append("second row", "0.5000+-.012", "  10+-2.2", ("pear", "milk"))
table.append("thrid row",  "0.1000+-.001", "   1+-2.3", ("orange", "beer"))
table.append("fourth row", "0.0100+-.100", "  -1+-2.4", ("banana", "juice"))
table.append("fifth row",  "0.0010+-.020", " -10+-2.5", ("grape", "wine"))
table.append("sixth row",  "0.0061+-.024", "-100+-2.6", ("quince", "coffee"))
table.append("sevent row", "0.0042+-.026", "   0+-2.7", ("plum", "soda"))
table.append("eight row",  "0.0050+-.032", "   0+-2.8", ("apricot", "tea"))
             
output = file("latex1.tex", "w")
print >> output, r"\documentclass{article}"
print >> output, r"\begin{document}"
print >> output, table.generate()
print >> output, r"\end{document}"
del output

os.system("latex --interaction nonstopmode latex1.tex")

