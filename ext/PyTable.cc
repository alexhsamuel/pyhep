//----------------------------------------------------------------------
//
// PyTable.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <cfloat>
#include <limits>
#include <memory>

#include "PyBoolArray.hh"
#include "PyExpr.hh"
#include "PyIterator.hh"
#include "PyRowDict.hh"
#include "PyTable.hh"
#include "instcount.hh"
#include "python.hh"
#include "table.hh"

#include <structmember.h>

using namespace Py;
using namespace table;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

const static bool debug = false;

InstanceCounter<PyTable>
instances;


inline Object*
asExpression(Object* arg)
{
  return callByNameObjArgs("hep.expr", "asExpression", arg, NULL);
}


/* Construct a C++ column descriptor from a Python 'Column' object.

   'column_object' -- An instance of a subclass of 'hep.table.Column'.

   returns -- A 'Column' column descriptor.

   throws -- 'PythonException', after setting the global Python
   exception, if something goes wrong.
*/

Column
makeColumnFromObject(PyObject* column_object)
{
  // Extract the column name and the type name.
  Object* column = (Object*) column_object;
  Ref<Object> name_object = column->GetAttrString("name");
  Ref<String> name_string = name_object->Str();
  const char* name = name_string->AsString();
  Ref<Object> type_name_object = column->GetAttrString("type");
  Ref<String> type_name_string = type_name_object->Str();
  const char* type_name = type_name_string->AsString();
  // Loop over the list of type names, looking for a match.
  ColumnType type = getTypeByName(type_name);
  // Did we fail to match the column name?  If so, throw an exception.
  if (type == TYPE_NONE) 
    throw Exception(PyExc_NotImplementedError, 
		    "column type %s not supported", type_name);

  // Construct the column.
  return Column(name, type);
}


Schema*
buildSchema(Object* schema_obj)
{
  Ref<Object> columns_attr = schema_obj->GetAttrString("columns");
  Sequence* columns = cast<Sequence>(columns_attr);

  // Create a new schema.
  std::auto_ptr<AutoSchema> schema(new AutoSchema);

  // Loop over columns.
  int num_columns = columns->Size();
  for (int c = 0; c < num_columns; ++c) {
    // Get the corresponding column object.
    Ref<Object> column_object = columns->GetItem(c);
    // Generate a corresponding C++ column instance.
    Column column = makeColumnFromObject(column_object);
    // Add the column to the schema.
    schema->addColumn(column);
  }

  return schema.release();
}


inline void
setColumn(Row* row,
	  ColumnType type,
	  int column_index,
	  Object* value)
{
  Value set_value;

  switch (type) {
  case TYPE_BOOL:
    set_value = Value::make(value->IsTrue());
    break;

  case TYPE_INT_8: {
    long long_value = value->IntAsLong();
    if (long_value < CHAR_MIN || long_value > CHAR_MAX)
      throw Exception(PyExc_OverflowError,
		      "%d is not an \"int8\"", long_value);
    set_value = Value::make(long_value);
    break;
  }

  case TYPE_INT_16: {
    long long_value = value->IntAsLong();
    if (long_value < SHRT_MIN || long_value > SHRT_MAX)
      throw Exception(PyExc_OverflowError,
		      "%d is not an \"int16\"", long_value);
    set_value = Value::make(long_value);
    break;
  }

  case TYPE_INT_32:
    set_value = Value::make(value->IntAsLong());
    break;
	
  case TYPE_FLOAT_32: {
    double dbl_value = value->FloatAsDouble();
    if (-dbl_value > std::numeric_limits<float>::max()
	|| dbl_value > std::numeric_limits<float>::max())
      throw Exception(PyExc_OverflowError, 
		      "%lf is not a \"float32\"", dbl_value);
    set_value = Value::make(dbl_value);
    break;
  }

  case TYPE_FLOAT_64: {
    set_value = Value::make(value->FloatAsDouble());
    break;
  }

  case TYPE_COMPLEX_64: {
    std::complex<double> cmplx = value->AsComplex();
    if (-std::real(cmplx) > std::numeric_limits<float>::max()
	|| std::real(cmplx) > std::numeric_limits<float>::max()
	|| -std::imag(cmplx) > std::numeric_limits<float>::max()
	|| std::imag(cmplx) > std::numeric_limits<float>::max())
      throw Exception(PyExc_OverflowError, 
		      "%lf+%lfj is not a \"complex64\"", 
		      std::real(cmplx), std::imag(cmplx));
    set_value = Value::make(cmplx);
    break;
  }    

  case TYPE_COMPLEX_128: 
    set_value = Value::make(value->AsComplex());
    break;

  default:
    throw Exception(PyExc_NotImplementedError, 
		    "unsupported column type %d", (int) type);
  }

  row->setValue(column_index, set_value);
}


inline void
setColumns(PyTable* table,
	   Row* row,
	   Mapping* mapping)
{
  // Get the names of all specified column values.
  Ref<Sequence> keys = mapping->Keys();
  int num_keys = keys->Size();
    
  for (int k = 0; k < num_keys; ++k) {
    // Get the next key.
    Ref<Object> key_obj = keys->GetItem(k);
    Ref<String> key = key_obj->Str();
    internInPlace(key);
    // Find the column in the table.
    ColumnType type;
    int column_index = table->findColumn(key, type);
    if (column_index == -1) 
      // Couldn't find the column.
      throw Exception(PyExc_KeyError, "%s", key->AsString());
    // Get the value for this column.
    Ref<Object> value = mapping->GetItem(key_obj);
    // Set it in the row.
    setColumn(row, type, column_index, value);
  }
}


void
setPath(Object* table,
	const char* path)
{
  char real_path[PATH_MAX];
  char* result = realpath(path, real_path);
  if (result == NULL)
    // The call to realpath failed; just use the original path.
    strcpy(real_path, path);

  Ref<String> path_str = String::FromString(real_path);
  table->SetAttrString("path", path_str);
}


/* Opens an existing table at 'path' with 'mode'.

   returns -- A 'PyTable' object for the table.

   raises -- 'FileError' if the table cannot be opened.  
*/

inline PyTable*
loadTable(const char* path,
	  const char* mode,
	  Callable* row_type=(Callable*) &PyRowDict::type,
	  bool with_metadata=true)
{
  // Open the table itself.
  Table* table;
  table = FileTable::open(path, mode);
  // Build a Python schema object for its schema.
  Ref<Object> schema(buildSchemaObject(table->getSchema()));
  // Construct the Python table object.
  Ref<PyTable> result = 
    PyTable::New(table, schema, row_type, with_metadata);
  // Store the path in it.
  setPath(result, path);
  // All done.
  return result.release();
}


}  // anonymous namespace


//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyTable::PyTable(Table* table,
		 PyObject* schema_obj,
		 Callable* row_type,
		 bool with_metadata)
  : table_(table),
    row_cache_max_size_(16),
    attribute_dict_(NULL),
    row_type_(newRef(row_type)),
    expression_cache_(Dict::New()),
    compiled_expressions_(Dict::New()),
    schema_(Ref<Object>::create(schema_obj).release()),
    weak_references_(NULL),
    file_object_(newRef(None)),
    with_metadata_(with_metadata)
{
  assert(table != NULL);

  if (with_metadata_) {
    std::string metadata = table->getMetadata();
    if (metadata.length() > 0) {
      // Import the standard Python unpickling function.
      // FIXME: Module 'cPickle' seems to have problems with
      // PyBoolVector's '__reduce__' method, so use 'pickle' instead.
      Ref<Object> unpickle_obj = Py::import("pickle", "loads");
      Callable* unpickle_fn = cast<Callable>(unpickle_obj); 
      Ref<Tuple> metadata_tuple;
      try {
	// Unpickle the metadata.
	Ref<Object> metadata_obj = 
	  unpickle_fn->CallFunction("s#", metadata.data(), 
				    metadata.length());
	// The result should be a tuple.
	metadata_tuple.set(cast<Tuple>(metadata_obj));

	if (metadata_tuple->Size() >= 1) 
	  // The first element is the attribute dictionary.
	  attribute_dict_ = metadata_tuple->GetItem(0);

	if (metadata_tuple->Size() >= 2) {
	  // The second element is the table schema.
	  Ref<Object> new_schema = metadata_tuple->GetItem(1);
	  // Call 'checkSchema' to make sure the loaded schema is
	  // compatible with what's really in the table.
	  Ref<Object> checkSchema_obj = 
	    Py::import("hep.table", "checkSchema");
	  Callable* checkSchema_fn = cast<Callable>(checkSchema_obj);
	  Ref<Object> ignored = checkSchema_fn->CallFunctionObjArgs
	    (schema_, (Object*) new_schema, NULL);
	  // Use the new schema.
	  schema_.set(new_schema.release());
	}

	if (metadata_tuple->Size() >= 3) {
	  // The third item is the expression cache.
	  Ref<Object> expression_cache = metadata_tuple->GetItem(2);
	  cast<Dict>(expression_cache_)->Update(expression_cache);
	}
      }
      catch (Exception exception) {
	// Extract the exception state.
	Ref<Object> type;
	Ref<Object> value;
	Ref<Object> traceback;
	exception.Get(type, value, traceback);
	// Print a warning.
	Ref<String> exc_string = value->Str();
	Warn(PyExc_RuntimeWarning, "error extracting table metadata: %s",
	     exc_string->AsString());
	// Clear the exception.
	exception.Clear();
      }
    }
  }

  // Import, and save a reference to, the pickling function.  We will
  // need in the destructor, which may be called during Python cleanup
  // when imports are not allowed.
  // FIXME: Module 'cPickle' seems to have problems with PyBoolVector's
  // '__reduce__' method, so use 'pickle' instead.
  Ref<Object> pickle_obj = import("pickle", "dumps");
  Callable* pickle_fn = cast<Callable>(pickle_obj);
  pickle_fn_ = Ref<Callable>::create(pickle_fn);

  // Construct a sequence of column keys (names in the schema).  This
  // will be handy for rows to use.
  const Schema* schema = table->getSchema();
  unsigned num_columns = schema->getNumColumns();
  Ref<Tuple> keys = Tuple::New(num_columns);
  // Loop over columns in the schema.
  for (unsigned c = 0; c < num_columns; ++c) {
    const Column& column = schema->getColumn(c);
    const char* column_name = column.getName().c_str();
    Ref<String> key = String::InternFromString(column_name);
    keys->InitializeItem(c, key);

    column_lookup_[key] = ColumnData_t(c, column.getType());

    // Associate the column index with name index in 'symbol_name_table'.
    int column_index = symbol_name_table.find(key);
    if (column_index >= (int) column_index_map_.size())
      column_index_map_.resize(column_index + 1, -1);
    column_index_map_[column_index] = c;
  }
  keys_.set(keys.release());

  instances.add(this);
}


PyTable::~PyTable()
{
  if (with_metadata_) {
    // Construct a tuple containing all the metadata we want to persist. 
    Ref<Tuple> metadata_tuple = Tuple::New(3);
    if (attribute_dict_ == NULL) {
      Ref<Dict> empty_dict = Dict::New();
      metadata_tuple->InitializeItem(0, empty_dict);
    }
    else 
      metadata_tuple->InitializeItem(0, attribute_dict_);
    metadata_tuple->InitializeItem(1, schema_);
    metadata_tuple->InitializeItem(2, expression_cache_);
    // Pickle it to obtain a persistent representation.
    Ref<Object> metadata_obj;
    try {
      // The second argument specifies the binary pickle format.
      metadata_obj = 
	pickle_fn_->CallFunction("Oi", (PyObject*) metadata_tuple, 1);
    }
    catch (Exception ex) {
      // Failed to pickle the metadata.
      // FIXME: For now, print a warning, the exception, and the
      // metadata itself, and continue on without writing it.
      std::cerr << "WARNING: Failed to pickle table metadata:\n";
      // printException(std::cerr);
      // std::cerr << "\n";
      ex.Print();
      ex.Clear();
    }
    // Did we manage to pickle the metadata?
    if (metadata_obj != NULL) {
      // Yup.  Store the metadata in the table.
      String* metadata_str = cast<String>(metadata_obj);
      std::string metadata(metadata_str->AsString(), 
			   metadata_str->Size());
      table_->setMetadata(metadata);
      // We don't need the metadata tuple any more.
      metadata_tuple.clear();
    }
  }

  assert(row_cache_.size() == 0);
  schema_.clear();

  // Let go (close and delete) the underlying table here.  Do this
  // before deleting the attribute dictionary, since the latter may
  // carry the last reference to a file containing the table.
  table_.reset();
  // Delete the attribute dictionary.
  if (attribute_dict_ != NULL)
    Py_DECREF(attribute_dict_);

  PyObject_ClearWeakRefs((PyObject*) this);
  
  instances.remove(this);
}


Row*
PyTable::getRow(int index)
{
  if (index < 0 || index >= table_->getNumRows())
    throw Exception(PyExc_IndexError, "%d", index);

  // Look for a cache entry that matches this index.  
  RowCache_t::iterator iter = row_cache_.find(index);
  if (iter != row_cache_.end()) {
    ++iter->second->ref_count_;
    return iter->second;
  }

  // No row from cache?  Make a new one.
  CachedRow* row = new CachedRow(table_->getSchema(), index);
  // Add this row to the cache.
  row_cache_[index] = row;
  // Read the row contents.
  table_->read(index, row);
  // All done.
  ++row->ref_count_;
  return row;
}


void
PyTable::returnRow(Row* row_arg)
{
  CachedRow* row = (CachedRow*) row_arg;
  assert(row->index_ >= 0);
  assert(row->index_ < table_->getNumRows());
  assert(row->ref_count_ > 0);

  --row->ref_count_;

  // Only kill it when the reference count drops to zero.
  if (row->ref_count_ > 0)
    return;

  // Find the row in the cache.
  RowCache_t::iterator iter = row_cache_.find(row->index_);
  assert(iter != row_cache_.end());
  assert(iter->second == row);
  // Remove it.
  row_cache_.erase(iter);
  // Deallocate it.
  delete row;
}


PyRow*
PyTable::getRowObject(int index,
		      Py::Callable* constructor)
{
  // Use the default row type, if none was specified explicitly.
  if (constructor == NULL)
    constructor = row_type_;
  // Build it.
  return cast<PyRow>(constructor->CallFunction("Oi", this, index));
}



Object*
PyTable::findExpression(String* name)
  const
{
  assert(name != NULL);

  Ref<Object> expressions_arg = schema_->GetAttrString("expressions");
  Sequence* expressions = cast<Sequence>(expressions_arg);

  int num_expressions = expressions->Size();
  for (int e = 0; e < num_expressions; ++e) {
    // Get the next expression entry.
    Ref<Object> expr_item = expressions->GetItem(e);
    // Does the name match?
    Ref<Object> expr_name = expr_item->GetAttrString("name");
    if (! name->Compare(expr_name))
      // Nope.  Try the next one.
      continue;

    // Yes.  But we need to return a compiled expression.  Do we already
    // have one?
    if (compiled_expressions_->HasKey(name)) 
      // Yes.  Return it.
      return compiled_expressions_->GetItem(name);
    else {
      // No.  Compile the expression.
      Ref<Object> expr = expr_item->GetAttrString("expression");
      Ref<Object> compiled = compile(expr);
      // Store it for next time.
      compiled_expressions_->SetItem(name, compiled);
      // Return it.
      return compiled.release();
    }
  }

  // No match.
  return NULL;
}


Object*
PyTable::expand(Object* expr)
  const
{
  Ref<Object> expanded_expr = callByNameObjArgs
    ("hep.table", "expand", (PyObject*) this, expr, NULL);

  return expanded_expr.release();
}


Object*
PyTable::cacheExpand(Object* expr)
  const
{
  Ref<Object> compiled_expr = callByNameObjArgs
    ("hep.table", "cacheExpand", 
     (PyObject*) this, (PyObject*) expr, NULL);
  return compiled_expr.release();
}


Object*
PyTable::compile(Object* expr)
  const
{
  Ref<Object> compiled_expr = callByNameObjArgs
    ("hep.table", "compile", 
     (PyObject*) this, (PyObject*) expr, NULL);
  return compiled_expr.release();
}


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

namespace {

void
tp_dealloc(PyTable* self)
try {
  // Perform C++ deallocation.
  self->~PyTable();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
tp_str(PyTable* self)
try {
  return String::FromFormat("<Table at %p>", (void*) self);
}
catch (Exception) {
  return NULL;
}


int
mp_length(PyTable* self)
try {
  return self->table_->getNumRows();
}
catch (Exception) {
  return -1;
}


PyObject* 
mp_subscript(PyTable* self, 
	     Object* key)
try {
  // Otherwise, the index should be an integer.  
  Ref<Int> index_object = key->Int();
  int index = index_object->AsLong();

  // Check that the index is in range.
  if (index < 0 || index >= self->table_->getNumRows()) 
    throw Exception
      (PyExc_IndexError, "row index %d out of range", index);

  // Return the requested row.
  return self->getRowObject(index);
}
catch (Exception) {
  return NULL;
}


PyMappingMethods
tp_as_mapping = {
  (inquiry) mp_length,                  // mp_length
  (binaryfunc) mp_subscript,            // mp_subscript
  NULL,                                 // mp_ass_subscript
};


PyObject*
method_append(PyTable* self,
	      Arg* args,
	      Dict* kw_args)
try {
  Object* map_obj = NULL;
  args->ParseTuple("|O", &map_obj);

  Table* table = self->table_.get();

  // Make a row object for this table.  
  // FIXME: We could use the cached row object, if there is one.
  Row row(table->getSchema());
  // Fill the row from the map object, if provided.
  if (map_obj != NULL) 
    setColumns(self, &row, cast<Mapping>(map_obj));
  // Fill in the row from keyword arguments.
  if (kw_args != NULL) 
    setColumns(self, &row, kw_args);

  // Append the row.
  int index = table->append(&row);
  // Return the index of the new row.
  return Int::FromLong(index);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_cache(PyTable* self,
	     Arg* args)
try {
  Object* expr_arg;
  Object* clear_arg = (Object*) Py_False;
  args->ParseTuple("O|O", &expr_arg, &clear_arg);
  Ref<Object> expr_obj = asExpression(expr_arg);

  // Expand the expression.
  Ref<Object> expanded_expr = self->expand(expr_obj);
  // For now, only boolean expressions may be cached.  Make sure it is.
  Ref<Object> expr_type = expanded_expr->GetAttrString("type");
  Ref<Object> bool_type = import("hep.bool", "bool");
  if (! expr_type->Compare(bool_type))
    throw Exception(PyExc_NotImplementedError, 
		    "only bool expressions may be cached");

  // Is this expression already cached?
  if (self->expression_cache_->HasKey(expanded_expr)) {
    // If requested to clear it, do so.
    if (clear_arg->IsTrue()) {
      Ref<Object> cache_entry = 
	self->expression_cache_->GetItem(expanded_expr);
      // Clear the mask bits.
      Ref<Object> mask_array = cast<Tuple>(cache_entry)->GetItem(0);
      cast<PyBoolArray>(mask_array)->clear();
    }
    else 
      // Did not request to clear the bits, and it's already cached, so
      // do nothing.
      ;
  }

  else {
    // Compile the expression.
    Ref<Object> compiled_expr = self->compile(expanded_expr);

    // Construct a tuple containing a bit mask for the cache, the cached
    // values themselves, and the compiled expression to use in case of a
    // cache miss.
    int num_rows = self->table_->getNumRows();
    Ref<Object> mask_array = PyBoolArray::New(num_rows);
    Ref<Object> value_array = PyBoolArray::New(num_rows);
    Ref<Tuple> cache_entry = 
      Tuple::New(2, (Object*) mask_array, (Object*) value_array);
    // Set the entry.  The key is the expanded expression.
    self->expression_cache_->SetItem(expanded_expr, cache_entry);
  }

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_compile(PyTable* self,
	       Object* expr_arg)
try {
  Ref<Object> expr(asExpression(expr_arg));
  if (expr == None)
    return expr.release();
  else {
    Ref<Object> compiled_expr = self->compile(expr);
    return compiled_expr.release();
  }
}
catch (Exception) {
  return NULL;
}


PyObject*
method_expand(PyTable* self,
	      Object* expr_arg)
try {
  Ref<Object> expr(asExpression(expr_arg));
  if (expr == None)
    return expr.release();
  else {
    Ref<Object> expanded_expr = self->expand(expr);
    return expanded_expr.release();
  }
}
catch (Exception) {
  return NULL;
}


PyObject*
method_select(PyTable* self,
	      Arg* args,
	      PyObject* kw_args)
try {
  static char* kw_arg_list[] = {
    "selection", 
    "columns", 
    NULL 
  };
  Object* selection_arg = None;
  Object* columns = NULL;
  if (! PyArg_ParseTupleAndKeywords(args, kw_args, "|OO", kw_arg_list,
				    &selection_arg, &columns))
    throw Exception();
  Ref<Object> selection;
  if (selection_arg != None) 
    selection.set(asExpression(selection_arg));
  
  // Construct the iterator.
  PyIterator* iter = PyIterator::New(self, selection);
  
  return (PyObject*) iter;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_uncache(PyTable* self,
	       Arg* args)
try {
  Object* expr_arg;
  args->ParseTuple("O", &expr_arg);
  Ref<Object> expr_obj = asExpression(expr_arg);

  // Expand the expression.
  Ref<Object> expanded_expr = self->expand(expr_obj);
  // Remove it from the cache.
  self->expression_cache_->DelItem(expanded_expr);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "append", (PyCFunction) method_append, 
    METH_VARARGS | METH_KEYWORDS, NULL },
  { "cache", (PyCFunction) method_cache, METH_VARARGS, NULL },
  { "compile", (PyCFunction) method_compile, METH_O, NULL },
  { "expand", (PyCFunction) method_expand, METH_O, NULL },
  { "get", (PyCFunction) mp_subscript, METH_O, NULL },
  { "select", (PyCFunction) method_select, 
    METH_VARARGS | METH_KEYWORDS, NULL },
  { "uncache", (PyCFunction) method_uncache, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


PyObject*
tp_iter(PyTable* self)
try {
  // Construct the iterator.
  return PyIterator::New(self, NULL);
}
catch (Exception) {
  return NULL;
}


struct PyMemberDef
tp_members[] = {
  { "expression_cache",
    T_OBJECT, offsetof(PyTable, expression_cache_), 0, NULL },
  { "file",
    T_OBJECT, offsetof(PyTable, file_object_), 0, NULL },
  { "row_cache_max_size", 
    T_INT, offsetof(PyTable, row_cache_max_size_), 0, NULL },
  { NULL, 0, 0, 0, NULL }
};


PyObject*
get_row_type(PyTable* self,
	     void* /* closure */)
try {
  RETURN_OBJ_REF(self->row_type_);
}
catch (Exception) {
  return NULL;
}


int
set_row_type(PyTable* self,
	     Object* row_type,
	     void* /* closure */)
try {
  if (! row_type->IsSubclassOf(&PyRow::type)) {
    Ref<String> row_type_repr = row_type->Repr();
    throw Exception(PyExc_ValueError, 
		    "row type '%s' is not a subclass of 'Row'",
		    row_type_repr->AsString());
  }

  self->row_type_ = newRef(cast<Callable>(row_type));

  return 0;
} 
catch (Exception) {
  return 1;
}


PyObject*
get_rows(PyTable* self,
	 void* /* closure */)
try {
  // Construct the iterator.
  return PyIterator::New(self, NULL);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_schema(PyTable* self,
	   void* /* closure */)
try {
  RETURN_OBJ_REF(self->schema_);
}
catch (Exception) {
  return NULL;
}


int 
set_schema(PyTable* self,
	   Object* new_schema,
	   void* /* closure */)
try {
  // Call 'checkSchema' to make sure the loaded schema is
  // compatible with what's really in the table.
  Ref<Object> checkSchema_obj = Py::import("hep.table", "checkSchema");
  Callable* checkSchema_fn = cast<Callable>(checkSchema_obj);
  Ref<Object> ignored = checkSchema_fn->CallFunctionObjArgs
    (self->schema_, (Object*) new_schema, NULL);
  
  // Use the new schema object from now on.
  self->schema_.set(newRef(new_schema));

  return 0;
}
catch (Exception) {
  return 1;
}


PyObject*
get_with_metadata(PyTable* self,
		  void* /* closure */)
try {
  return newBool(self->with_metadata_);
}
catch (Exception) {
  return NULL;
}


int 
set_with_metadata(PyTable* self,
		  Object* with_metadata,
		  void* /* closure */)
try {
  self->with_metadata_ = with_metadata->IsTrue();
  return 0;
}
catch (Exception) {
  return 1;
}


PyGetSetDef
tp_getset[] = {
  { "row_type", (getter) get_row_type, (setter) set_row_type, NULL, NULL },
  { "rows", (getter) get_rows, NULL, NULL, NULL },
  { "schema", (getter) get_schema, (setter) set_schema, NULL, NULL },
  { "with_metadata", (getter) get_with_metadata, 
    (setter) set_with_metadata, NULL, NULL },
  { NULL, NULL, NULL, NULL },
};


}  // anonymous namespace

PyTypeObject
PyTable::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Table",                              // tp_name
  sizeof(PyTable),                      // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_str,                    // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  &tp_as_mapping,                       // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  (reprfunc) tp_str,                    // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT 
  | Py_TPFLAGS_BASETYPE,                // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clear
  NULL,                                 // tp_richcompare
  offsetof(PyTable, weak_references_),  // tp_weaklistoffset
  (getiterfunc) tp_iter,                // tp_iter
  NULL,                                 // tp_iternext
  tp_methods,                           // tp_methods
  tp_members,                           // tp_members
  tp_getset,                            // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  offsetof(PyTable, attribute_dict_),   // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  NULL,                                 // tp_new
};


PyTable*
PyTable::New(Table* table,
	     PyObject* schema,
	     Callable* row_type,
	     bool with_metadata)
{
  assert(schema != NULL);

  // Allocate a table.
  PyTable* result = Py::allocate<PyTable>();
  // Perform C++ construction.
  try {
    new(result) PyTable(table, schema, row_type, with_metadata);
  }
  catch (Py::Exception) {
    // The table is not correctly initialized, so don't allow it to be
    // deallocated normally.
    Py::deallocate(result);
    throw;
  }

  return result;
}


PyObject*
function_table_create(Object* /* self */,
		      Arg* args)
try {
  // Parse arguments.
  char* path;
  Object* schema_arg;
  Object* with_metadata;
  args->ParseTuple("sOO", &path, &schema_arg, &with_metadata);

  // Copy the schema.
  Ref<Object> schema_obj = 
    callByNameObjArgs("copy", "copy", schema_arg, NULL);

  // Construct a C++ schema from the Python schema.
  std::auto_ptr<Schema> schema(buildSchema(schema_obj));
  // Create the new table.
  std::auto_ptr<Table> table;
  try {
    table.reset(FileTable::create(schema.get(), path));
  }
  catch (FileError error) {
    throw Exception(PyExc_RuntimeError, "error creating %s: %s", 
		    path, error.message_.c_str());
  }
  // Wrap it in a Python table object.
  Callable* default_row_type = (Callable*) &PyRowDict::type;
  Ref<Object> result = 
    PyTable::New(table.release(), schema_obj, 
		 default_row_type, with_metadata->IsTrue());
  // Store the path on the Python table object.
  setPath(result, path);

  return result.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
function_table_open(Object* /* self */,
		    Arg* args)
try {
  // Parse arguments.
  char* path;
  char* mode;
  Object* row_type_arg;
  Object* with_metadata;
  args->ParseTuple("ssOO", &path, &mode, &row_type_arg, &with_metadata);
  // Check that the mode is recognized.
  if (strcmp(mode, "r") != 0
      && strcmp(mode, "w") != 0) 
    throw Exception(PyExc_ValueError, "unrecognized mode '%s'", mode);
  // Check that the row type is callable.
  Callable* row_type = cast<Callable>(row_type_arg);

  // Open the table.
  try {
    return loadTable(path, mode, row_type, with_metadata->IsTrue());
  }
  catch (FileError error) {
    // Open failed; raise an exception.
    throw Exception(PyExc_IOError, "%s", error.message_.c_str());
  }
}
catch (Exception) {
  return NULL;
}


PyObject*
buildSchemaObject(const Schema* schema)
{
  // Construct an empty schema.
  Ref<Object> schema_obj = callByNameObjArgs("hep.table", "Schema", NULL);

  // Loop over columns.
  int num_columns = schema->getNumColumns();
  for (int c = 0; c < num_columns; ++c) {
    // Get the next column descriptor and name.
    const Column& column = schema->getColumn(c);
    // Extract the column name and type name.
    std::string name = column.getName();
    const char* type_name = getTypeName(column.getType());
    // Add the column to the schema.
    Ref<Object> ignored = 
      schema_obj->CallMethod("addColumn", "ss", name.c_str(), type_name);
  }

  return schema_obj.release();
}
