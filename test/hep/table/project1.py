#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram1D
import hep.table
from   hep.test import compare
from   math import log

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("x", "int16")
schema.addColumn("x_squared", "int32")
schema.addColumn("log_x_plus_1", "float32")

table = hep.table.create("project1.table", schema)
for x in range(0, 100):
    table.append(x = x, x_squared = x * x, log_x_plus_1 = log(x + 1))

hist1 = Histogram1D(10, (0, 1000), "x**2",
                    expression="x ** 2")
hist2 = Histogram1D(10, (0, 1000), "x**2",
                    expression="x_squared")
hist3 = Histogram1D(101, (-1.0, 1.0),
                    expression="log_x_plus_1 - log(x + 1)")

hep.hist.project(table.rows, (hist1, hist2, hist3, ))

compare(hist1.number_of_samples, 100)
compare(hist1.getBinContent("underflow"), 0)
compare(hist1.getBinContent(0), 10)
compare(hist1.getBinContent(1),  5)
compare(hist1.getBinContent(2),  3)
compare(hist1.getBinContent(3),  2)
compare(hist1.getBinContent(4),  3)
compare(hist1.getBinContent(5),  2)
compare(hist1.getBinContent(6),  2)
compare(hist1.getBinContent(7),  2)
compare(hist1.getBinContent(8),  1)
compare(hist1.getBinContent(9),  2)
compare(hist1.getBinContent("overflow"), 68)

compare(hist2.number_of_samples, 100)
compare(hist2.getBinContent("underflow"), 0)
compare(hist2.getBinContent(0), 10)
compare(hist2.getBinContent(1),  5)
compare(hist2.getBinContent(2),  3)
compare(hist2.getBinContent(3),  2)
compare(hist2.getBinContent(4),  3)
compare(hist2.getBinContent(5),  2)
compare(hist2.getBinContent(6),  2)
compare(hist2.getBinContent(7),  2)
compare(hist2.getBinContent(8),  1)
compare(hist2.getBinContent(9),  2)
compare(hist2.getBinContent("overflow"), 68)

compare(hist3.number_of_samples, 100)
compare(hist3.getBinContent("underflow"), 0)
compare(hist3.getBinContent(hist3.map( 0.0)), 100)
compare(hist3.getBinContent("overflow"), 0)
