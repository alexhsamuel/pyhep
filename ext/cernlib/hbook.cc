//----------------------------------------------------------------------
//
// hbook.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <cstring>
#include <memory>

#include "PyRowDict.hh"
#include "PyTable.hh"
#include "cernlib.hh"
#include "hbook.hh"
#include "python.hh"
#include "table.hh"
#include "value.hh"

using namespace Py;
using namespace table;

//----------------------------------------------------------------------
// global variables
//----------------------------------------------------------------------

// HBOOK requires these symbols.
int 
xargc;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

/* Return the top directory containing 'path'.  */

std::string
getTopDir(const std::string& path)
{
  // Find the first slash, not counting a leading double slash.
  std::string::size_type slash = 
    path.find('/', (path[0] == '/' && path[1] == '/') ? 2 : 0);
  return path.substr(0, slash);
}


/* Association between column types and Fortran format specifiers.  */

struct TypeInfo {
  ColumnType type_;
  const char* format_specifier_;
}
types[] = {
  { TYPE_BOOL,     NULL  },
  { TYPE_INT_8,    "I*1" },
  { TYPE_INT_16,   "I*2" },
  { TYPE_INT_32,   "I*4" },
  { TYPE_FLOAT_32, "R*4" },
  { TYPE_FLOAT_64, "R*8" },
};


/* Return the column type corresponding to Fortran format 'specifier'.  */

ColumnType
getColumnTypeForFormatSpecifier(const char* specifier)
{
  // Look up the type code.
  for (unsigned i = 0; i < sizeof(types) / sizeof(TypeInfo); ++i) {
    const TypeInfo& ti = types[i];
    if (ti.format_specifier_ != NULL
	&& strcmp(specifier, ti.format_specifier_) == 0)
      return ti.type_;
  }

  return TYPE_NONE;
}


/* Return the Fortran format specifier corresponding to column 'type'.  */

const char* 
getFormatSpecifierForColumnType(ColumnType type)
{
  for (unsigned i = 0; i < sizeof(types) / sizeof(TypeInfo); ++i) {
    const TypeInfo& ti = types[i];
    if (ti.type_ == type)
      return ti.format_specifier_;
  }

  return NULL;
}


/* Construct a schema describing an HBOOK ntuple.

   'id' -- The RZ ID of the ntuple to examine.

   'block_name' -- Output argument: filled with the name of the ntuple
   block containing the columns.

   returns -- A new schema object describing the columns in the ntuple.
*/

Schema*
buildSchemaForNtuple(int id,
		     std::string& block_name)
{
  // Get the number of columns in the tuple.
  char chtitl[128];
  int num_columns = 0;
  hgiven_(&id, chtitl, &num_columns, NULL, NULL, NULL, sizeof(chtitl), 0);
  
  // Construct a schema for the tuple.
  std::auto_ptr<AutoSchema> schema(new AutoSchema);
  // Loop over columns.  HBOOK numbers them from one.
  for (int c = 1; c <= num_columns; ++c) {
    // Get column information.
    char chtag[128];
    char block[12];
    int itype;
    hntvdef_(&id, &c, chtag, block, &itype, sizeof(chtag), sizeof(block));
    std::string tag = stringFromFortran(chtag, sizeof(chtag));
    std::string column_in_block = stringFromFortran(block, sizeof(block));

    if (c == 1)
      block_name = column_in_block;
    else if (block_name != column_in_block) {
      // FIXME: Handle blocks more gracefully.
      std::cerr << "column with tag '" << chtag 
		<< "' is in secondary block '" << column_in_block 
		<< "'; skipping\n";
      continue;
    }

    // The content of 'chtag' is in the format 'NAME:TAG', where TAG is
    // a Fortran format type specifier indicating the type of the
    // column.  Divide 'chtag' into these two parts.
    std::string::size_type colon = tag.find(':');
    assert(colon != std::string::npos);
    std::string name = tag.substr(0, colon);
    std::string type_spec = tag.substr(colon + 1, tag.size() - (colon + 1));

    // Convert the column type to our own type codes.
    ColumnType type = getColumnTypeForFormatSpecifier(type_spec.c_str());
    assert(type != TYPE_NONE);

    // Add the column to our schema.
    schema->addColumn(Column(name, type));
  }

  // Return the schema we just built.
  return schema.release();
}


//----------------------------------------------------------------------
// helper classes
//----------------------------------------------------------------------

/* Implementation of the 'Table' interface for an HBOOK row-wise
   ntuple.  */

class RowWiseNtuple
  : public Table
{
public:

  /* Connect to an exiting ntuple.

    'rz_id' -- The ntuple RZ ID.

    'rz_dir' -- The name of the RZ directory containing the ntuple.

    'writable' -- Whether to connect in read-write mode.
  */
  RowWiseNtuple(int rz_id, const std::string& rz_dir, bool writable);

  virtual ~RowWiseNtuple();

  virtual int64_t getNumRows() const;
  virtual void read(int64_t row_number, Row* row);
  virtual int append(const Row* row);
  virtual std::string getMetadata() const;
  virtual void setMetadata(const std::string& data);

protected:

  const int rz_id_;
  const std::string rz_dir_;
  std::string block_name_;

};


RowWiseNtuple::RowWiseNtuple(int rz_id,
			     const std::string& rz_dir,
			     bool writable)
  : Table(NULL, writable),
    rz_id_(rz_id),
    rz_dir_(rz_dir)
{
  schema_ = buildSchemaForNtuple(rz_id_, block_name_);
  hgnpar_(&rz_id_, "", 0);
}


RowWiseNtuple::~RowWiseNtuple()
{
  if (isWritable()) {
    // Write out the ntuple.
    hcdir_(rz_dir_.c_str(), " ", rz_dir_.length(), 1);
    int icycle;
    hrout_(&rz_id_, &icycle, " ", 1);
  }
  // Clean the ntuple out of global memory.
  hcdir_("//PAWC", " ", 6, 1);
  hdelet_(&rz_id_);
}


int64_t
RowWiseNtuple::getNumRows()
  const
{
  int num_rows;
  hnoent_(&rz_id_, &num_rows);
  return num_rows;
}


void
RowWiseNtuple::read(int64_t row_number,
		    Row* row)
{
  assert(row->getSchema() == getSchema());

  // HBOOK indexes rows from one.
  ++row_number;

  // Load the row directly into 'row's buffer.
  int error;
  int rn = (int) row_number;
  hgnf_(&rz_id_, &rn, row->getBuffer(), &error);
  // Any problems?
  if (error != 0) 
    // Yes; throw.
    throw Exception(PyExc_IOError, "cannot load row %d (%d)", 
		    row_number, error);
}


int
RowWiseNtuple::append(const Row* row)
{
  assert(isWritable());
  assert(row->getSchema() == getSchema());
  // Add the row.
  hfn_(&rz_id_, row->getBuffer());
  // Compute the index of the row we just added.
  return getNumRows() - 1;
}


std::string
RowWiseNtuple::getMetadata()
  const
{
  // Metadata currently not supported.
  return std::string();
}


void
RowWiseNtuple::setMetadata(const std::string& data)
{
  // Metadata currently not supported.
}


//----------------------------------------------------------------------

/* Implementation of the 'Table' interface for an HBOOK column-wise
   ntuple.  */

class ColumnWiseNtuple
  : public Table
{
public:

  /* Connect to an existing ntuple.

    'rz_id' -- The ntuple RZ ID.

    'rz_dir' -- The name of the RZ directory containing the ntuple.

    'writable' -- Whether to connect in read-write mode.
  */
  ColumnWiseNtuple(int rz_id, const std::string& rz_path, bool writable);

  virtual ~ColumnWiseNtuple();

  virtual int64_t getNumRows() const;
  virtual void read(int64_t row_number, Row* row);
  virtual int append(const Row* row);
  virtual std::string getMetadata() const;
  virtual void setMetadata(const std::string& data);

protected:

  const int rz_id_;
  const std::string rz_path_;
  std::string block_name_;
  std::auto_ptr<Row> row_;
  bool first_read_;

};


ColumnWiseNtuple::ColumnWiseNtuple(int rz_id,
				   const std::string& rz_path,
				   bool writable)
  : Table(NULL, writable),
    rz_id_(rz_id),
    rz_path_(rz_path),
    first_read_(false)
{
  // Construct a schema for the ntuple columns.
  schema_ = buildSchemaForNtuple(rz_id_, block_name_);
  // Allocate a row for this schema.  This is a private row, which will
  // be used as the staging area for data read to and written from the
  // tuple. 
  std::auto_ptr<Row> row(new Row(schema_));
  row_ = row;
  // Register our private row as the place data is read into and written
  // from. 
  const char* chblok = block_name_.c_str();
  char* address = row_->getBuffer();
  char* chform = "$SET";
  hbname_(&rz_id_, chblok, address, chform, strlen(chblok), strlen(chform));
}


ColumnWiseNtuple::~ColumnWiseNtuple()
{
  if (isWritable()) {
    // Write out the ntuple.
    hcdir_(rz_path_.c_str(), " ", rz_path_.length(), 1);
    int cycle;
    hrout_(&rz_id_, &cycle, " ", 1);
  }
  // Clean the ntuple out of global memory.
  hcdir_("//PAWC", " ", 6, 1);
  hdelet_(&rz_id_);
}


int64_t
ColumnWiseNtuple::getNumRows()
  const
{
  int num_rows;
  hnoent_(&rz_id_, &num_rows);
  return num_rows;
}


void 
ColumnWiseNtuple::read(int64_t row_number, 
		       Row* row)
{
  assert(row->getSchema() == getSchema());

  // HBOOK indexes rows from one.
  ++row_number;

  // Read the data into 'row_', which was previously registered.  Use
  // 'hgnt' for the first read, 'hgntf' for subsequent reads.
  int ierr;
  int rn = row_number;
  if (first_read_)
    hgntf_(&rz_id_, &rn, &ierr);
  else {
    hgnt_(&rz_id_, &rn, &ierr);
    first_read_ = true;
  }

  // If the call succeeded, copy the row data into 'row_'.
  if (ierr == 0) 
    memcpy(row->getBuffer(), row_->getBuffer(), getSchema()->getSize());
  else {
    // An error occurred.
    char message[64];
    snprintf(message, sizeof(message), "cannot load row %d (%d)", 
	     rn, ierr);
    throw FileError(message);
  }
}


int 
ColumnWiseNtuple::append(const Row* row)
{
  assert(isWritable());
  assert(row->getSchema() == getSchema());
  // Copy the row into our private, registered 'row_'.
  memcpy(row_->getBuffer(), row->getBuffer(), getSchema()->getSize());
  // Fill the ntuple from there.
  hfnt_(&rz_id_);
  // Compute the index of the row we just added.
  return getNumRows() - 1;
}


std::string
ColumnWiseNtuple::getMetadata()
  const
{
  // Metadata not currently supported.
  return std::string();
}


void
ColumnWiseNtuple::setMetadata(const std::string& data)
{
  // Metadata not currently supported.
}


/* Create a Python table object for an ntuple.

   'rz_id' -- The RZ ID of the ntuple.
   
   'rz_path' -- The RZ directory path containing this ntuple.

   'writable' -- True if the ntuple can be modified.

   'column_wise' -- True if this is a CWN; otherwise, an RWN.

   returns -- A new 'PyTable' object.
*/

PyObject*
createTable(int rz_id,
	    const std::string& rz_path,
	    bool writable,
	    bool column_wise)
{
  // Connect to the ntuple.
  Table* table;
  if (column_wise)
    table = new ColumnWiseNtuple(rz_id, rz_path, writable);
  else
    table = new RowWiseNtuple(rz_id, rz_path, writable);
  
  // Construct a Python table object.
  Ref<Object> schema = buildSchemaObject(table->getSchema());
  Callable* default_row_type = (Callable*) &PyRowDict::type;
  Ref<PyTable::PyTable> result = 
    PyTable::New(table, schema, default_row_type, false);
  // Note the ntuple type.
  Object* column_wise_value = 
    (Object*) (column_wise ? Py_True : Py_False);
  column_wise_value->IncRef();
  result->SetAttrString("column_wise", column_wise_value);
  // Note the RZ ID in the table.
  Ref<Int> rz_id_obj = Int::FromLong(rz_id);
  result->SetAttrString("rz_id", rz_id_obj);

  // All set.
  return result.release();
}


}  // anonymous namespace

//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

PyObject*
function_createRowWiseNtuple(PyObject* self,
			     Arg* args)
try {
  int id;
  const char* title;
  const char* path;
  Object* schema;
  args->ParseTuple("issO", &id, &title, &path, &schema);
  
  // Extract a sequence of names of columns from the column mapping.
  Ref<Object> columns_obj  = schema->GetAttrString("columns");
  Sequence* columns = cast<Sequence>(columns_obj);
  int num_columns = columns->Size();
  // Construct a Fortran character array containing column names.
  char chtags[num_columns * 8];
  for (int c = 0; c < num_columns; ++c) {
    Ref<Object> column = columns->GetItem(c);

    // Get the column name, as a string.
    Ref<Object> name_obj = column->GetAttrString("name");
    std::string name = name_obj->StrAsString();
    // Get the column's type name.
    Ref<Object> type_name_obj = column->GetAttrString("type");
    std::string type_name = type_name_obj->StrAsString();
    // Make sure it's "float32".  That's the only column type supported
    // by RWNs. 
    if (type_name != "float32") 
      throw Exception(PyExc_ValueError, 
	 "only \"float32\" column type allowed for row-wise ntuples");

    // RWN column tags may be up to eight characters long.
    makeFortranString(name, chtags + c * 8, 8);
  }

  // For the primary allocation, choose enough for 1024 rows.
  int nwbuff = 1024 * num_columns;
  // Book the ntuple.
  hbookn_(&id, title, &num_columns, path, &nwbuff, chtags, 
	  strlen(title), strlen(path), /*chtags length=*/ 8);

  // Connect and return a table object for the new ntuple.
  return createTable(id, path, /*writable=*/ true, /*column_wise=*/ false);
}
catch (Exception) {
  return NULL;
}


PyObject*
function_createColumnWiseNtuple(PyObject* self,
				Arg* args)
try {
  int id;
  const char* title;
  const char* path;
  Object* schema;
  args->ParseTuple("issO", &id, &title, &path, &schema);

  // Extract a sequence of names of columns from the schema.
  Ref<Object> columns_obj = 
    callByNameObjArgs("hep.cernlib.hbook", "_getColumnsInOrder", schema, NULL);

  Sequence* columns = cast<Sequence>(columns_obj);
  int num_columns = columns->Size();
  // Construct a Fortran character array containing column names.
  std::string chform;
  for (int c = 0; c < num_columns; ++c) {
    // Get the column.
    Ref<Object> column = columns->GetItem(c);
    // Get the column name, as a string.
    Ref<Object> name_obj = column->GetAttrString("name");
    Ref<String> name_str = name_obj->Str();
    const char* name = name_str->AsString();
    // Get the column's type.
    Ref<Object> type_name_obj = column->GetAttrString("type");
    Ref<String> type_name_str = type_name_obj->Str();
    const char* type_name = type_name_str->AsString();
    ColumnType type = getTypeByName(type_name);
    if (type == TYPE_NONE)
      throw Exception(PyExc_ValueError, 
		      "unknown column type '%s'", type_name);

    // Construct an element in the column format string.
    if (c > 0)
      chform += ", ";
    chform += name;
    chform += ':';
    chform += getFormatSpecifierForColumnType(type);
  }

  // Create the CWN.
  hcdir_(path, " ", strlen(path), 1);
  hbnt_(&id, title, "D", strlen(title), 1);
  // Describe the rows.
  hbname_(&id, "default", NULL, chform.c_str(), 7, chform.length());

  // Connect and return a table object for the new ntuple.
  return createTable(id, path, /*writable=*/ true, /*column_wise=*/ true);
}
catch (Exception) {
  return NULL;
}


PyObject*
function_openTuple(PyObject* self,
		   Arg* args)
try {
  int id;
  char* path;
  Object* writable_arg;
  args->ParseTuple("isO", &id, &path, &writable_arg);
  bool writable = writable_arg->IsTrue();
  
  // Load the ntuple header into memory.
  hcdir_(path, " ", strlen(path), 1);
  int icycle = 999999;
  int offset = 0;
  hrin_(&id, &icycle, &offset);
  if (quest_[0] != 0) 
    throw 
      Exception(PyExc_IOError, "cannot read ntuple with ID %d", id);

  // Make sure it's an ntuple.
  int kind;
  hkind_(&id, &kind, " ", 1);
  if (kind != 4)
    throw Exception(PyExc_TypeError, "ID %d is not an ntuple", id);
  // Determine whether it is column-wise or row-wise.
  bool column_wise = hntnew_(&id);
  // Open it.
  return createTable(id, path, writable, column_wise);
}
catch (Exception) {
  return NULL;
}

