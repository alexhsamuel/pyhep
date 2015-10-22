#include <cassert>
#include <cstdlib>
#include <memory>

#include "test.hh"
#include "table.hh"

using namespace Tables;

int
main()
{
  const char* const path = "test1.table";

  try {
    
    // Create and fill a table.
    {
      AutoSchema* schema = new AutoSchema;
      schema->addColumn(Column("index", TYPE_INT_32));
      schema->addColumn(Column("as_double", TYPE_FLOAT_64));
      schema->addColumn(Column("twice", TYPE_INT_32));
      schema->addColumn(Column("cycle", TYPE_INT_32));

      auto_ptr<Table> table(FileTable::create(schema, path));
      auto_ptr<Row> row(new Row(table->getSchema()));

      for (int i = 0; i < 1000; ++i) {
	row->setValue<int>("index", i);
	row->setValue<double>("as_double", i);
	row->setValue<int>("twice", 2 * i);
	row->setValue<int>("cycle", (101 + 23 * i) % 17);
	int row_number = table->append(row.get());
	TEST_COMPARE(row_number, i);
      }
    }

    // Open the table and check its contents.
    {
      auto_ptr<Table> table(FileTable::open(path, "r"));
      auto_ptr<Row> row(new Row(table->getSchema()));

      for (int i = 99; i >= 0; --i) {
	table->read(i, row.get());
	TEST_COMPARE(row->getValue<int>("index"), i);
	TEST_COMPARE_NUMBERS(row->getValue<double>("as_double"), (double) i);
	TEST_COMPARE(row->getValue<int>("twice"), 2 * i);
	TEST_COMPARE(row->getValue<int>("cycle"), (101 + 23 * i) % 17);
      }
    }

  }
  catch (FileError error) {
    TEST_FAIL(error.message_.data());
  }

  return Test::failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
