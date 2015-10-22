//----------------------------------------------------------------------
//
// PyIterator.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>

#include "PyIterator.hh"
#include "PyRow.hh"
#include "PyTable.hh"
#include "python.hh"

using namespace Py;

#define IGNORE_EXCEPTIONS_IN_SELECTION 0

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyIterator::PyIterator(PyTable* table,
		       Object* sel)
  : table_(Ref<PyTable>::create(table)),
    index_(0)
{
  assert(table_ != NULL);

  // Expand cached subexpressions in the selection expression, if any.
  Ref<Object> selection = (sel == NULL) ? NULL : table->cacheExpand(sel);
  Ref<Object> cached_expr_type = import("hep.table", "CachedExpression");

  if (selection == NULL)
    // No selection.
    selection_.clear();

  // If 'selection' is a 'CachedExpression', look up the underlying
  // cache data buffers here so we can use them for efficient row
  // selection. 
  else if (selection->IsInstance((PyObject*) cached_expr_type)) {
    // Get the 'cache' attribute.  It contains the tuple
    // '(length, mask, data)'.
    Ref<Object> cache_obj = selection->GetAttrString("cache");
    Tuple* cache = cast<Tuple>(cache_obj);
    // Extract tuple contents.
    Object* mask_obj;
    Object* data_obj;

    cache->ParseTuple("OO", &mask_obj, &data_obj);

    if (! PyBoolArray::Check(mask_obj))
      throw Exception(PyExc_TypeError, "mask must be a BoolArray");
    PyBoolArray* mask = cast<PyBoolArray>(mask_obj);
    cache_mask_ = Ref<PyBoolArray>::create(mask);

    if (! PyBoolArray::Check(data_obj))
      throw Exception(PyExc_TypeError, "data must be a BoolArray");
    PyBoolArray* data = cast<PyBoolArray>(data_obj);
    cache_data_ = Ref<PyBoolArray>::create(data);

    if (cache_mask_->length_ != cache_data_->length_)
      throw Exception(PyExc_TypeError, "data length != mask length");

    // Get the underlying expression.
    Ref<Object> subexprs = selection->GetAttrString("subexprs");
    // It should have one element.
    Sequence* subexprs_seq = cast<Sequence>(subexprs);
    if (subexprs_seq->Size() != 1)
      throw Exception
	(PyExc_ValueError, 
	 "'CachedExpression' should have a single subexpression");
    // Get the subexpression.
    Ref<Object> subexpr = subexprs_seq->GetItem(0);
    // Compile it, and store it as the expression to evaluate.
    selection_.set(table->compile(subexpr));
  }

  // Otherwise, just compile the selection.
  else 
    selection_.set(table->compile(selection));
}


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

namespace {

void
tp_dealloc(PyIterator* self)
try {
  // Perform C++ deallocation.
  self->~PyIterator();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
tp_str(PyIterator* self)
try {
  return String::FromFormat("<Iterator at %p>", (void*) self);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_iter(PyIterator* self)
try {
  Py_INCREF(self);
  return (PyObject*) self;
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_iternext(PyIterator* self)
try {
  int num_rows = self->table_->table_->getNumRows();

  while (true) {
    // First, find the index of the next row to consider.
    int index;

    // Do we have a cache for the selection expression?
    if (self->cache_mask_ != NULL) {
      // Yes.  Scan forward to find a row for which the cached value is
      // true, skipping rows for which the cached value is false.  But
      // stop at rows for which the cache does not contain a value.
      while ((index = self->index_++) < num_rows) {
	if (index >= self->cache_mask_->length_
	    || ! self->cache_mask_->get(index))
	  // No cache information for this row; fall through and proceed
	  // with normal selection.
	  break;
	if (self->cache_data_->get(index))
	  // Cached result: this row passes the selection.  Return the
	  // row. 
	  return self->table_->getRowObject(index);
	else 
	  // Cached result: this row fail the selection.  Continue on to
	  // the next row.
	  continue;
      }
    }
    else 
      // No cache.  Use the next index value.
      index = self->index_++;

    // At the end?
    if (index >= num_rows) 
      // Yes.
      throw Exception(PyExc_StopIteration, "end of iteration");

    // Allocate a row.
    Ref<PyRow> row = self->table_->getRowObject(index);
    
    // Is there a selection?
    if (self->selection_ == NULL) 
      // No selection.  Use this row.
      return row.release();

    // Evaluate the selection expression.
    Callable* selection = cast<Callable>(self->selection_);
    bool selection_result;
// FIXME
#if IGNORE_EXCEPTIONS_IN_SELECTION
    try {
#endif
      Ref<Object> selection_return = selection->Call(NULL, row);
      selection_result = selection_return->IsTrue();
#if IGNORE_EXCEPTIONS_IN_SELECTION
    }
    catch (Exception ex) {
      // Fetch the Python exception state.
      Ref<Object> type;
      Ref<Object> value;
      Ref<Object> traceback;
      PyErr_Fetch
	((PyObject**) &type, (PyObject**) &value, (PyObject**) &traceback);
      // If it's a keyboard interrupt, let it through.
      if (type == PyExc_KeyboardInterrupt)
	throw;

      std::cerr << "Exception during expression evaluaton:\n";
      ex.Print();

      // FIXME: Ignore it.  Is that right?  FIXME: Definitely, we need
      // to be more specific about which exceptions we catch here.
      ex.Clear();
      selection_result = false;
    }
#endif

    if (self->cache_mask_ != NULL
	&& index < self->cache_mask_->length_) {
      self->cache_mask_->set(index, true);
      self->cache_data_->set(index, selection_result);
    }

    if (selection_result) 
      // Selection function returned a true value.  Use this row.
      return row.release();
    else
      // Selection function returned a false value.  Continue to the
      // next row.
      ;
  }
}
catch (Exception) {
  return NULL;
}


}  // anonymous namespace

PyTypeObject
PyIterator::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Iterator",                           // tp_name
  sizeof(PyIterator),                   // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  NULL,                                 // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
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
  0,                                    // tp_weaklistoffset
  (getiterfunc) tp_iter,                // tp_iter
  (iternextfunc) tp_iternext,           // tp_iternext
  NULL,                                 // tp_methods
  NULL,                                 // tp_members
  NULL,                                 // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  NULL,                                 // tp_new
};


