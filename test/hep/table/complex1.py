#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from   hep.test import compare
import hep.table

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Create a new table.
schema = hep.table.Schema()
schema.addColumn("a", "float32")
schema.addColumn("b", "complex128")
schema.addColumn("c", "int16")
schema.addColumn("d", "complex64")
schema.addColumn("e", "complex128")
table = hep.table.create("complex1.table", schema)

# Fill in some rows.
for i in xrange(0, 1000):
    row = {
        "a": i * 52.467,
        "b": 1.8577928723e-12 * i - (i + 4.3) * 1j,
        "c": i,
        "d": 1500000 + 6j * i,
        "e": i,
        }
    table.append(row)

# Write and close the table.
del schema, row, table

# Reopen the table.
table = hep.table.open("complex1.table")
# Check that the columns were restored correctly.
compare(table.schema["a"].type, "float32")
compare(table.schema["a"].Python_type, float)
compare(table.schema["a"].size, 4)
compare(table.schema["b"].type, "complex128")
compare(table.schema["b"].Python_type, complex)
compare(table.schema["b"].size, 16)
compare(table.schema["c"].type, "int16")
compare(table.schema["c"].Python_type, int)
compare(table.schema["c"].size, 2)
compare(table.schema["d"].type, "complex64")
compare(table.schema["d"].Python_type, complex)
compare(table.schema["d"].size, 8)
compare(table.schema["e"].type, "complex128")
compare(table.schema["e"].Python_type, complex)
compare(table.schema["e"].size, 16)

# Check all rows.
for i in xrange(0, 1000):
    row = table[i]
    compare(row["_table"], table)
    compare(row["_index"], i)
    compare(row["a"], i * 52.467, precision=i * 1e-5);
    compare(row["b"], 1.8577928723e-12 * i - (i + 4.3) * 1j)
    compare(row["c"], i)
    compare(row["d"], 1500000 + 6j * i)
    compare(row["e"], i)
