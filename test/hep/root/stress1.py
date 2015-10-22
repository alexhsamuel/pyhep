#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.hist import Histogram1D
import hep.root
import hep.table
from   random import random, randint
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

num_dirs = 100
num_hists = 100
num_tables = 10
num_rows = 10000

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

file = hep.root.create("stress1.root")

subdirs = [ "" ]
for i in xrange(0, num_dirs):
    parent = subdirs[randint(0, len(subdirs) - 1)]
    dir = file.join(parent, "DIR%d" % i)
    file.mkdir(dir)
    subdirs.append(dir)

hists = []
for i in xrange(0, num_hists):
    hist = Histogram1D(randint(1, 100), 0.0, 1.0)
    for j in xrange(0, 100):
        hist << random()
    path = file.join(subdirs[randint(0, len(subdirs) - 1)], "HIST1D%d" % i)
    file.set(path, hist)
    hist.path = path
    hists.append(hist)

schema = hep.table.Schema()
schema.addColumn("index", "int32")
schema.addColumn("value", "float32")

tables = {}
for i in xrange(0, num_tables):
    subdir = subdirs[randint(0, len(subdirs) - 1)]
    name = "TABLE%d" % i
    table = hep.root.createTable(name, file[subdir], schema)
    values = []
    for j in xrange(0, num_rows):
        value = random()
        values.append(value)
        table.append(index=j, value=value)
    tables[file.join(subdir, name)] = values

schema = hep.table.Schema()
for i in xrange(0, 50):
    schema.addColumn("COL%d" % i, "float64")
path = "BIGTABLE";
table = hep.root.createTable(path, file, schema)
table_rows = []
for j in xrange(0, num_rows):
    values = []
    row = {}
    for i in xrange(0, 50):
        value = random()
        row["COL%d" % i] = value
        values.append(value)
    table.append(row)
    table_rows.append(values)

del schema, table, file

#-----------------------------------------------------------------------

file = hep.root.open("stress1.root")

for hist in hists:
    loaded = file[hist.path]
    compare(loaded.axis.number_of_bins, hist.axis.number_of_bins)
    compare(loaded.axis.range, (0.0, 1.0))
    for b in xrange(0, loaded.axis.number_of_bins):
        compare(loaded.getBinContent(b), hist.getBinContent(b))

for table_path, values in tables.items():
    table = file[table_path]
    compare(len(table), num_rows)
    for j in xrange(0, num_rows):
        row = table[j]
        compare(row["index"], j)
        compare(row["value"], values[j], precision=1e-7)

table = file["BIGTABLE"]
compare(len(table.schema), 50)
compare(len(table), num_rows)
for j in xrange(0, num_rows):
    row = table[j]
    values = table_rows[j]
    for i in xrange(0, 50):
        compare(row["COL%d" % i], values[i], precision=1e-8)


