import hep.table

def textFileToTable(input_file_name, table_file_name):
    """Convert a text file containing tabular values to a table.

    'input_file_name' -- The file name of a text file containing a table
    of floating-point values.  The first line is assumed to contain the
    column names.  All additional lines are assumed to contain values
    for each column.

    'table_file_name' -- The file name of the table to create."""

    lines = iter(file(input_file_name))

    # Read the first line in the file, and split it into column names.
    heading_row = lines.next()
    column_names = heading_row.split()

    # Construct the schema from these column names.
    schema = hep.table.Schema()
    for column_name in column_names:
        schema.addColumn(column_name, "float32")
    # Create the table.
    table = hep.table.create(table_file_name, schema)

    # Scan over remaining lines in the file.
    for line in lines:
        # Split the line into values and convert them to numbers.
        values = map(float, line.split())
        # Make sure the line contains the right number of values.
        if len(values) != len(column_names):
            raise RuntimeError, "format error"
        # Construct a dictionary mapping column names to values.
        row = dict(zip(column_names, values))
        # Add the row to the table.
        table.append(row)

    del row, table


if __name__ == "__main__":
    # This file was invoked as a script.  Convert a text file as
    # specified on the command line.
    import sys
    textFileToTable(sys.argv[1], sys.argv[2])

