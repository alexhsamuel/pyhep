#include <cassert>
#include <cstdlib>
#include <memory>

#include "test.hh"
#include "table.hh"

using namespace Tables;


struct Particle {
  int id;
  float energy;
  double px;
  double py;
  double pz;
};


const Particle
particles[] = 
{
  { 100, 5.4,  2.2, -0.4,  1.2 },
  { 202, 5.3, -0.8, -3.2, -2.2 },
  { 117, 5.1,  3.1,  1.0,  0.1 },
};


int
main()
{
  const char* const path = "test2.table";

  try {
    
    // Create and fill a table.
    {
      StructSchema<Particle>* schema = new StructSchema<Particle>;
      schema->addColumn("id", &Particle::id);
      schema->addColumn("energy", &Particle::energy);
      schema->addColumn("px", &Particle::px);
      schema->addColumn("py", &Particle::py);
      schema->addColumn("pz", &Particle::pz);

      auto_ptr<Table> table(FileTable::create(schema, path));
      auto_ptr<Row> row(new Row(table->getSchema()));

      for (int i = 0; i < 3; ++i) {
	schema->fillRow(row.get(), &particles[i]);
	int row_number = table->append(row.get());
	TEST_COMPARE(row_number, i);
      }
    }

    // Open the table and check its contents.
    {
      auto_ptr<Table> table(FileTable::open(path, "r"));
      auto_ptr<Row> row(new Row(table->getSchema()));

      for (int i = 2; i >= 0; --i) {
	const Particle& p = particles[i];
	table->read(i, row.get());
	TEST_COMPARE(row->getValue<int>("id"), p.id);
	TEST_COMPARE_NUMBERS(row->getValue<float>("energy"), p.energy);
	TEST_COMPARE_NUMBERS(row->getValue<double>("px"), p.px);
	TEST_COMPARE_NUMBERS(row->getValue<double>("py"), p.py);
	TEST_COMPARE_NUMBERS(row->getValue<double>("pz"), p.pz);
      }
    }

  }
  catch (FileError error) {
    TEST_FAIL(error.message_.data());
  }

  return Test::failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
