import hep.expr
import hep.table

def cut(energy):
    return energy > 2.5

t = hep.table.open("tracks.table")
e = hep.expr.Function(cut)

for r in t.rows():
    if e.evaluate(r):
        print r["energy"]

