//----------------------------------------------------------------------
//
// PyTable.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension class for flat data tables.  */

#ifndef PYTABLE_HH
#define PYTABLE_HH

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>
#include <map>
#include <memory>

#include "PyRow.hh"
#include "python.hh"
#include "table.hh"

class PyExpr;

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct PyTable
  : public Py::Object
{
  static PyTypeObject type;
  static PyTable* New(table::Table* table, PyObject* schema, 
		      Py::Callable* row_type, bool with_metadata);

  PyTable(table::Table* table, PyObject* schema, 
	  Py::Callable* row_type, bool with_metadata);
  ~PyTable();

  /* Create an new Python row object.  

     returns -- A new reference.  When the row is to be destroyed, it
     MUST be passed to 'returnRow' rather than deallocated
     explicitly.  
  */
  table::Row* getRow(int index);

  /* Return a Python row object that is no longer in use.
   
     'row' -- A Python object that has should be deallocated according
     to Python, i.e. its reference count is zero. 

     Either deallocates the row, or caches it for later use. 
  */
  void returnRow(table::Row* row);

  PyRow* getRowObject(int index, Py::Callable* constructor=NULL);

  /* Return the index of the column named 'name', or -1 if none.  

     'name' -- An interned string.

     'type' -- If the column is found, this is set to the column's type;
     otherwise, unchanged.  
  */
  int findColumn(Py::String* name, table::ColumnType& type) const;

  /* Return the expression named 'name'.

     'name' -- An interned string.

     returns -- A new reference to the expression, or NULL if none is
     found.  
  */
  Py::Object* findExpression(Py::String* name) const;

  /* Expand an expression.

     returns -- A new reference.  
  */
  Py::Object* expand(Py::Object* expression) const;

  /* Substitue cache accessors for cached expressions.

     returns -- A new reference.  
  */
  Py::Object* cacheExpand(Py::Object* expression) const;

  /* Compile an expression for this table.

     returns -- A new reference to a compiled expression object.  
  */
  Py::Object* compile(Py::Object* expression) const;

  /* The underlying table.  */
  std::auto_ptr<table::Table> table_;

  /* A lookup table from interned Python string name to column index.  */
  typedef std::pair<int, table::ColumnType> ColumnData_t;
  typedef std::map<Py::String*, ColumnData_t> ColumnLookup_t;
  ColumnLookup_t column_lookup_;

  /* A lookup from name indices in 'symbol_table_names' to column indices.  

     Expressions store the names of symbols as indices, which are
     associated to  the symbol name by 'symbol_table_names'.  Rather
     than convert back to the symbol name and then look it up in our
     schema, we can get the column faster by associating the name index
     directly with a column index, using this array.  */
  std::vector<short> column_index_map_;
  std::vector<PyExpr*> expr_map_;

  class CachedRow
    : public table::Row
  {
  public:

    CachedRow(const table::Schema* schema, int index)
      : Row(schema), ref_count_(0), index_(index) {}

    int ref_count_;
    const int index_;
  };


  /* 'Row' objects saved for reuse.  */
  typedef std::map<int, CachedRow*> RowCache_t;
  RowCache_t row_cache_;

  /* Maximum size of the row cache.  */
  size_t row_cache_max_size_;

  /* Additional user attributes stored on the table.  */
  PyObject* attribute_dict_;

  Py::Ref<Py::Callable> row_type_;

  /* A dictionary of cached expression values.

     A keys is an expression that can be avaluated on rows of this
     table.  The value is a pair '(mask, values)', where 'mask' is a
     bool array indicating whether the cache is valid for each row, and
     'values' is an array containing the cached value for each row (for
     rows for which the mask bit is set).  
  */
  Py::Ref<Py::Dict> expression_cache_;

  /* A dictionary of compiled expressions.  */
  Py::Ref<Py::Dict> compiled_expressions_;

  /* The Python schema object.  */
  Py::Ref<Py::Object> schema_;

  /* A sequence of Python string names of columns in the table.  */
  Py::Ref<Py::Object> keys_;

  /* We need a pickling function to store metadata when closing the
     table.  The pickling function is imported from another module.
     However, closing a file can happen during cleanup of the Python
     interpreter, at which time new imports are not allowed.  Therefore,
     we import the pickling function at creation time and save a
     reference to it.  
  */
  Py::Ref<Py::Callable> pickle_fn_;

  /* Required to support weak references to instances.  */
  PyObject* weak_references_;

  /* The file containing this table (may be 'None').  */
  Py::Ref<Py::Object> file_object_;

  /* Whether to load and/or store metadata.  */
  bool with_metadata_;

};


inline int
PyTable::findColumn(Py::String* name, 
		    table::ColumnType& type)
  const
{
  assert(name != NULL);
  // 'name' is an interened string, so look it up by pointer value.
  ColumnLookup_t::const_iterator match = column_lookup_.find(name);
  if (match == column_lookup_.end())
    // Not found.
    return -1;
  else {
    // Set the type.
    type = match->second.second;
    // Return the column index.
    return match->second.first;
  }
}


//----------------------------------------------------------------------
// Python extension function declarations
//----------------------------------------------------------------------

extern PyObject* function_table_makeColumn(Py::Object*, Py::Arg* args);
extern PyObject* function_table_makeIndex(Py::Object*, Py::Arg* args);
extern PyObject* function_table_open(Py::Object*, Py::Arg* args);
extern PyObject* function_table_create(Py::Object*, Py::Arg* args);

//----------------------------------------------------------------------
// other useful functions
//----------------------------------------------------------------------

/* Build a Python schema object for a table scheme.  

   returns -- A new reference to a 'hep.table.Schema' object constructed
   to represent the table schema. 
*/
extern PyObject* buildSchemaObject(const table::Schema*);

//----------------------------------------------------------------------

#endif  // #ifndef PYTABLE_HH
