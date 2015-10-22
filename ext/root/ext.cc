//----------------------------------------------------------------------
//
// root/ext.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension module for access to Root libraries.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <cstdio>
#include <iostream>
#include <string>

#include "TDirectory.h"
#include "TObject.h"
#include "TROOT.h"
#include "TSystem.h"
#include "python.hh"
#include "tree.hh"

using namespace Py;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

#if 0
TObject*
unwrapTObject(Object* obj)
{
  // A Python object wrapping a TObject has a 'this' attribute
  // containing the TObject's address.
  Ref<Object> this_obj = obj->GetAttrString("this");
  Ref<String> this_str = this_obj->Str();
  // The 'this' attribute should be a string of the format
  // "_xxxxxxxx_Class_p" where "xxxxxxxx" is the hex representation of
  // the object's address. 
  TObject* result = NULL;
  int matches = sscanf(this_str->AsString(), "_%x_", (unsigned*) &result);
  if (matches != 1)
    throw Exception(PyExc_RuntimeError, 
		    "malformed 'this' attribute in TObject: '%s'",
		    this_str->AsString());
  
  return result;
}
#elif 0
TObject*
unwrapTObject(Object* obj)
{
  Ref<Object> this_obj = obj->GetAttrString("this");
  TObject* result;
  int success = SWIG_ConvertPtr(this_obj, &result, SWIGTYPE_p_TObject, 
				SWIG_POINTER_EXCEPTION);
  if (success == 0)
    return NULL;

  return result;
}
#else
TObject*
unwrapTObject(Object* obj)
{
  Ref<Object> this_obj = obj->GetAttrString("this");

  static Ref<Object> getPointerValue_obj = 
    import("hep.root.rootc", "getPointerValue");
  static Callable* getPointerValue = cast<Callable>(getPointerValue_obj);

  Ref<Object> result = getPointerValue->CallFunctionObjArgs(this_obj, NULL);
  return (TObject*) result->IntAsLong();
}
#endif


void
resetSignalHandlers()
{
  // Disable the F#@%ING ANNOYING Root signal handlers.  
  ESignals all_signals[] = {
    kSigBus,
    kSigSegmentationViolation,
    kSigSystem,
    kSigPipe,
    kSigIllegalInstruction,
    kSigQuit,
    kSigInterrupt,
    kSigWindowChanged,
    kSigAlarm,
    kSigChild,
    kSigUrgent,
    kSigFloatingException,
    kSigTermination,
    kSigUser1,
    kSigUser2
  };
  for (unsigned s = 0; s < sizeof(all_signals) / sizeof(ESignals); ++s)
    gSystem->ResetSignal(all_signals[s]);
}


}  // anonymous namespace


//----------------------------------------------------------------------
// Python functions
//----------------------------------------------------------------------

PyObject*
function_getRootVersion(PyObject* /* cookie */,
			Arg* args)
try {
  return String::FromString(gROOT->GetVersion());
}
catch (Exception) {
  return NULL;
}


//----------------------------------------------------------------------
// Python module definition
//----------------------------------------------------------------------

namespace {

PyMethodDef
functions[] = {
  { "createTree", (PyCFunction) function_createTree, METH_VARARGS, NULL },
  { "getRootVersion", 
    (PyCFunction) function_getRootVersion, METH_VARARGS, NULL },
  { "openTree", (PyCFunction) function_openTree, METH_VARARGS, NULL },

  { NULL, NULL, 0, NULL }
};


PyTypeObject*
types[] = {
  NULL
};


}  // anonymous namespace


extern "C" {

void initext()
try {
  // Initialize root.
  static TROOT root("root", "root");
  resetSignalHandlers();

  Module::Initialize("ext", functions, types, "");
}
catch (Exception) {
  std::cerr << "could not initialize module 'ext'" << std::endl;
}


}  // extern "C"
