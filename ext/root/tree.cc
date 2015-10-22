//----------------------------------------------------------------------
//
// tree.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <memory>

#include "PyRowDict.hh"
#include "PyTable.hh"
#include "python.hh"
#include "table.hh"
#include "tree.hh"
#include "value.hh"

#include "TDirectory.h"
#include "TFile.h"
#include "TIterator.h"
#include "TLeaf.h"
#include "TObject.h"
#include "TTree.h"

using namespace Py;
using namespace table;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

struct TypeInfo {
  ColumnType type_;
  char type_character_;
};

TypeInfo 
types[] = {
  { TYPE_BOOL,     'B' },
  { TYPE_INT_8,    'B' },
  { TYPE_INT_16,   'S' },
  { TYPE_INT_32,   'I' },
  { TYPE_FLOAT_32, 'F' },
  { TYPE_FLOAT_64, 'D' },
};


char 
getRootTypeCharacterForColumnType(ColumnType type)
{
  for (unsigned i = 0; i < sizeof(types) / sizeof(TypeInfo); ++i) {
    const TypeInfo& ti = types[i];
    if (ti.type_ == type)
      return ti.type_character_;
  }

  return 0;
}


Schema*
buildSchemaForTree(TTree* tree)
{
  // Construct a schema for the tree.
  std::auto_ptr<AutoSchema> schema(new AutoSchema);

  // Loop over columns.
  std::auto_ptr<TIterator> 
    leaf_iter(tree->GetIteratorOnAllLeaves());
  for (TObject* leaf = leaf_iter->Next();
       leaf != NULL;
       leaf = leaf_iter->Next()) {
    // Get the leaf's name.
    const char* leaf_name = leaf->GetName();
    // Determine the column type from the leaf's class.
    ColumnType type;
    if (leaf->InheritsFrom("TLeafD"))
      type = TYPE_FLOAT_64;
    else if (leaf->InheritsFrom("TLeafF"))
      type = TYPE_FLOAT_32;
    else if (leaf->InheritsFrom("TLeafI"))
      type = TYPE_INT_32;
    else if (leaf->InheritsFrom("TLeafS"))
      type = TYPE_INT_16;
    else if (leaf->InheritsFrom("TLeafB"))
      type = TYPE_INT_8;
    else 
      // FIXME.
      throw Exception(PyExc_NotImplementedError,
		      "type '%s' of tree leaf '%s' not supported",
		      leaf->ClassName(), leaf_name);

    // Add the column to the schema.
    schema->addColumn(Column(leaf_name, type));
  }

  return schema.release();
}


//----------------------------------------------------------------------
// helper classes
//----------------------------------------------------------------------

class Tree
  : public Table
{
public:

  /* Connect to an existing tree.  */
  Tree(TTree* tree, bool writable);

  virtual ~Tree();

  virtual int64_t getNumRows() const;
  virtual void read(int64_t row_number, Row* row);
  virtual int append(const Row* row);
  virtual std::string getMetadata() const;
  virtual void setMetadata(const std::string& data);

protected:

  TTree* ttree_;
  std::auto_ptr<Row> row_;

};


Tree::Tree(TTree* tree, 
	   bool writable)
  : Table(NULL, writable),
    ttree_(tree)
{
  assert(ttree_ != NULL);
  // Construct a schema from the tree leaves.
  schema_ = buildSchemaForTree(tree);
  // Allocate a row for this schema.  This is a private row, which will
  // be used as the staging area for data read to and written from the
  // tuple. 
  {
    std::auto_ptr<Row> row(new Row(schema_));
    row_ = row;
  }
  // Register the leaves to column addresses in the row.
  char* row_buffer = row_->getBuffer();
  for (int c = 0; c < schema_->getNumColumns(); ++c) {
    // Get the next column in the schema.
    const Column& column = schema_->getColumn(c);
    const char* column_name = column.getName().c_str();
    // Look up the corresponding leaf.
    TLeaf* leaf = ttree_->GetLeaf(column_name);
    // Set the leaf's address.
    size_t column_offset = schema_->getColumnOffset(c);
    leaf->SetAddress(row_buffer + column_offset);
  }
}


Tree::~Tree()
{
  // We need to write the tree now, if necessary.
  if (isWritable()) {
    ttree_->GetDirectory()->cd();
    ttree_->Write();
  }

  delete ttree_;
}


inline int64_t
Tree::getNumRows()
  const
{
  return (int64_t) ttree_->GetEntries();
}


void
Tree::read(int64_t row_number,
	   Row* row)
{
  // Read the tree into our staging 'Row'.
  int result = ttree_->GetEntry(row_number);
  // Did that succeed?
  if (result == -1) {
    // An I/O occurred.
    char message[64];
    snprintf(message, sizeof(message), 
	     "I/O error loading tree row %lld", (long long) row_number);
    throw FileError(message);
  }
  else if (result == 0) {
    // No such row.
    throw NoRow(row_number);
  }
  else
    // Got the row into our staging 'Row'.  Copy it into the provided
    // 'Row' object.
    memcpy(row->getBuffer(), row_->getBuffer(), getSchema()->getSize());
}


int
Tree::append(const Row* row)
{
  assert(isWritable());
  assert(row->getSchema() == getSchema());
  // Copy the row into our private, registered 'row_'.
  memcpy(row_->getBuffer(), row->getBuffer(), getSchema()->getSize());
  // Fill the ntuple from there.
  ttree_->Fill();
  // Return the new index.
  return ttree_->GetEntries();
}


std::string
Tree::getMetadata()
  const
{
  return std::string();
}


void
Tree::setMetadata(const std::string& data)
{
}


}  // anonymous namespace


//----------------------------------------------------------------------
// Python functions
//----------------------------------------------------------------------

PyObject*
function_createTree(PyObject* self,
		    Arg* args)
try {
  // Parse arguments.
  long tdirectory_ptr;
  const char* name;
  const char* title;
  Object* schema;
  Object* separate_branches_arg;
  const char* branch_name;
  int buffer_size = 8192;
  Object* with_metadata = (Object*) Py_True;
  args->ParseTuple
    ("lssOOs|iO", &tdirectory_ptr, &name, &title, &schema, 
     &separate_branches_arg, &branch_name, &buffer_size, &with_metadata);
  TDirectory* tdirectory = (TDirectory*) tdirectory_ptr;
  if (tdirectory == NULL)
    throw Exception(PyExc_ValueError, "directory is NULL");
  bool separate_branches = separate_branches_arg->IsTrue();
 
  // Create the tree.
  tdirectory->cd();
  TTree* ttree = new TTree(name, title);
  ttree->SetDirectory(tdirectory);

  // Extract a sequence of names of columns from the schema.
  Ref<Object> columns_obj = schema->GetAttrString("columns");
  Sequence* columns = cast<Sequence>(columns_obj);
  int num_columns = columns->Size();
  // Construct a string describing the leaves created for the columns.
  std::string leaflist;
  for (int c = 0; c < num_columns; ++c) {
    // Get the column.
    Ref<Object> column = columns->GetItem(c);
    // Get the column name, as a string.
    Ref<Object> name_obj = column->GetAttrString("name");
    Ref<String> name_str = name_obj->Str();
    const char* name = name_str->AsString();
    // Get the column's type name.
    Ref<Object> type_name_obj = column->GetAttrString("type");
    Ref<String> type_name_str = type_name_obj->Str();
    const char* type_name = type_name_str->AsString();
    ColumnType type = getTypeByName(type_name);
    if (type == TYPE_NONE)
      throw Exception
	(PyExc_ValueError, "unknown column type '%s'", type_name);
    // Get the Root type specification character for this type.
    char root_type_character = getRootTypeCharacterForColumnType(type);
    if (root_type_character == 0)
      throw Exception
	(PyExc_NotImplementedError, 
	 "column type '%s' not supported for Root trees", type_name);
    
    // If we are not using separate branches, accumulate the leaf
    // specifiers into one string, separated by colons. 
    if (! separate_branches && c > 0)
      leaflist += ':';

    // Construct the leaf specification.
    leaflist += name;
    leaflist += '/';
    leaflist += root_type_character;

    // If we are using separate branches, build a branch for this leaf.
    if (separate_branches) {
      ttree->Branch(name, NULL, leaflist.c_str(), buffer_size);
      // Start anew with the leaf specification.
      leaflist = "";
    }
  }

  // If we are not using separate branches, build the branch for all the
  // leaves together.
  if (! separate_branches && num_columns > 0)
    ttree->Branch(branch_name, NULL, leaflist.c_str(), buffer_size);

  // Return a Python table object.
  ttree->Write();
  Table* table = new Tree(ttree, /*writable=*/ true);
  Callable* default_row_type = (Callable*) &PyRowDict::type;
  return PyTable::New(table, schema, default_row_type, 
		      with_metadata->IsTrue());
}
catch (Exception) {
  return NULL;
}


PyObject*
function_openTree(PyObject* self,
		  Arg* args)
try {
  long ttree_ptr;
  Object* writable = 0;
  Object* row_type_arg = (Object*) &PyRowDict::type;
  Object* with_metadata = (Object*) Py_True;
  args->ParseTuple("l|OOO", &ttree_ptr, &writable, &row_type_arg,
		   &with_metadata);
  TTree* ttree = (TTree*) ttree_ptr;
  if (ttree == NULL)
    throw Exception(PyExc_ValueError, "TTree pointer is NULL");
  Callable* row_type = cast<Callable>(row_type_arg);
  
  // Construct the Python tree object.
  Table* table = new Tree(ttree, writable->IsTrue());
  Ref<Object> schema = buildSchemaObject(table->getSchema());
  Ref<Object> result = 
    PyTable::New(table, schema, row_type, with_metadata->IsTrue());
  // Set the name and title.
  Ref<String> name = String::FromString(ttree->GetName());
  result->SetAttrString("name", name);
  Ref<String> title = String::FromString(ttree->GetTitle());
  result->SetAttrString("title", title);
  // All done.
  return result.release();
}
catch (Exception) {
  return NULL;
}
