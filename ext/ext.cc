//----------------------------------------------------------------------
//
// ext.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Main Python extension module for PyHEP.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cmath>
#include <iostream>

#include "PyBoolArray.hh"
#include "PyContour.hh"
#include "PyFourVector.hh"
#include "PyHistogram1D.hh"
#include "PyHistogram2D.hh"
#include "PyImageFile.hh"
#include "PyIterator.hh"
#include "PyRandom.hh"
#include "PyRow.hh"
#include "PyRowDict.hh"
#include "PyRowObject.hh"
#include "PyTable.hh"
#include "PyExpr.hh"
#include "PyScatter.hh"
#include "PyTimer.hh"
#include "PyX11Window.hh"
#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// Python functions
//----------------------------------------------------------------------

PyObject*
function_getPoissonErrors(PyObject* /* self */,
			  Arg* args)
try {
  int value;
  args->ParseTuple("i", &value);
  if (value < 0)
    throw Exception(PyExc_ValueError, "negative value");

  std::pair<double, double> errors = getPoissonErrors(value);
  return buildValue("dd", errors.first, errors.second);
}
catch (Exception) {
  return NULL;
}


PyObject*
function_erf(PyObject* /* self */,
	     Object* arg)
try {
  double value = arg->FloatAsDouble();
  return Float::FromDouble(erf(value));
}
catch (Exception) {
  return NULL;
}


PyObject*
function_erfc(PyObject* /* self */,
	      Object* arg)
try {
  double value = arg->FloatAsDouble();
  return Float::FromDouble(erfc(value));
}
catch (Exception) {
  return NULL;
}


//----------------------------------------------------------------------
// module setup
//----------------------------------------------------------------------

namespace {

PyTypeObject*
types[] = {
  &PyBoolArray::type,
  &PyExpr::type,
  &PyFourVector::type,
  &PyHistogram1D::type,
  &PyHistogram2D::type,
  &PyImageFile::type,
  &PyIterator::type,
  &PyShuffledLEcuyerRandom::type,
  &PyRow::type,
  &PyRowDict::type,
  &PyRowObject::type,
  &PyScatter::type,
  &PyTable::type,
  &PyTimer::type,
  &PyX11Window::type,
  NULL
};


PyMethodDef
functions[] = {
  { "X11_getScreenSize",
    (PyCFunction) function_X11_getScreenSize, METH_VARARGS, NULL },
  { "X11_initialize",
    (PyCFunction) function_X11_initialize, METH_VARARGS, NULL },
  { "contours",
    (PyCFunction) function_contours, METH_VARARGS, NULL },
  { "erf", 
    (PyCFunction) function_erf, METH_O, NULL },
  { "erfc", 
    (PyCFunction) function_erfc, METH_O, NULL },
  { "get_symbol_index",
    (PyCFunction) function_get_symbol_index, METH_VARARGS, NULL },
  { "getPoissonErrors",
    (PyCFunction) function_getPoissonErrors, METH_VARARGS, NULL },
  { "table_create", 
    (PyCFunction) function_table_create, METH_VARARGS, NULL },
  { "table_open", 
    (PyCFunction) function_table_open, METH_VARARGS, NULL },
  { "timer_get",
    (PyCFunction) function_timer_get, METH_VARARGS, NULL },
  { "timer_start",
    (PyCFunction) function_timer_start, METH_VARARGS, NULL },
  { "timer_stop",
    (PyCFunction) function_timer_stop, METH_VARARGS, NULL },
  { "timer_stopAll",
    (PyCFunction) function_timer_stopAll, METH_NOARGS, NULL },
  { "timer_printAll",
    (PyCFunction) function_timer_printAll, METH_NOARGS, NULL },
  { NULL, NULL, 0, NULL }
};


const char* const
doc_string = "Extension classes for PyHEP.";


}  // anonymous namespace


extern "C" {

void
initext()
{
  try {
    Module* module = Module::Initialize("ext", functions, types, NULL);
    PyBoolArray::Register(module);

    Ref<String> cxx_flags = String::FromString(CXXFLAGS);
    module->SetAttrString("_cxx_flags", cxx_flags);
  }
  catch (Exception) {
    std::cerr << "module 'ext' initialization failed:\n";

    Ref<Object> exc_info(import("sys", "exc_info"));
    Callable* exc_info_fn = cast<Callable>(exc_info); 
    Ref<Object> exception = exc_info_fn->CallFunctionObjArgs(NULL);

    Ref<Object> excepthook(import("sys", "excepthook"));
    Callable* excepthook_fn = cast<Callable>(excepthook);
    Ref<Object> result = excepthook_fn->CallObject(exception);
  }
}


}  // extern "C"
