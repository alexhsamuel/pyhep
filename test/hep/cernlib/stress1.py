#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cernlib import hbook
from   hep.hist import Histogram1D
import hep.table
from   random import random, randint
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

file = hbook.create("stress1.hbook")

subdirs = [ "" ]
for i in xrange(0, 100):
    parent = subdirs[randint(0, len(subdirs) - 1)]
    dir = file.join(parent, "dir%d" % i)
    file.mkdir(dir)
    subdirs.append(dir)

del dir

hists = []
for i in xrange(0, 100):
    hist = Histogram1D(randint(1, 100), 0.0, 1.0)
    for j in xrange(0, 100):
        hist << random()
    subdir_name = subdirs[randint(0, len(subdirs) - 1)]
    subdir = file[subdir_name]
    name = "hist1d%d" % i
    subdir[name] = hist
    hist.subdir_name = subdir_name
    hist.name = name
    hists.append(hist)

del hist, subdir_name, subdir, name

schema = hep.table.Schema()
schema.addColumn("index", "int32")
schema.addColumn("value", "float32")

tables = {}
for i in xrange(0, 10):
    subdir_name = subdirs[randint(0, len(subdirs) - 1)]
    subdir = file[subdir_name]
    name = "table%d" % i
    table = hbook.createTable(name, subdir, schema)
    values = []
    for j in xrange(0, 10000):
        value = random()
        values.append(value)
        table.append(index=j, value=value)
    tables[(subdir_name, name)] = values
    # We can't have two tables with the same RZ ID active at the
    # same time, so make sure this table is released before the next
    # is created. 
    del table

del subdir_name, subdir, name, value, values

schema = hep.table.Schema()
for i in xrange(0, 50):
    schema.addColumn("col%d" % i, "float64")
table = hbook.createTable("bigtable", file, schema)
table_rows = []
for j in xrange(0, 10000):
    values = []
    row = {}
    for i in xrange(0, 50):
        value = random()
        row["col%d" % i] = value
        values.append(value)
    table.append(row)
    table_rows.append(values)

del schema, table, values, row
del file

#-----------------------------------------------------------------------

file = hbook.open("stress1.hbook")

for hist in hists:
    loaded = file[hist.subdir_name][hist.name]
    compare(loaded.axis.number_of_bins, hist.axis.number_of_bins)
    compare(loaded.axis.range, (0.0, 1.0))
    for b in xrange(0, loaded.axis.number_of_bins):
        compare(loaded.getBinContent(b), hist.getBinContent(b))

for table_path, values in tables.items():
    subdir_name, name = table_path
    table = file[subdir_name][name]
    compare(len(table), 10000)
    for j in xrange(0, 10000):
        row = table[j]
        compare(row["index"], j)
        compare(row["value"], values[j], precision=1e-7)
    del table, row

table = file["bigtable"]
compare(len(table.schema), 50)
compare(len(table), 10000)
for j in xrange(0, 10000):
    row = table[j]
    values = table_rows[j]
    for i in xrange(0, 50):
        compare(row["col%d" % i], values[i], precision=1e-8)


