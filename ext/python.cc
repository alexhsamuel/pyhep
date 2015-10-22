//----------------------------------------------------------------------
//
// python.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cfloat>
#include <iostream>
#include <stdarg.h>

#include "python.hh"

#ifndef va_copy
# define va_copy __va_copy
#endif

namespace Py {

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

Object*
None = (Object*) Py_None;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

Tuple*
buildArgsFromVaFormat(char* format,
		      va_list args)
{
  if (format == NULL || *format == '\0')
    // Empty format.
    return Tuple::New();

  // Use Python's routine to construct the arguments.
  Ref<Object> args_obj(Py_VaBuildValue(format, args));
  if (args_obj == NULL)
    // Format error.
    throw Exception();

  // Did we get a tuple back?
  if (Tuple::Check(args_obj)) 
    // Yes.  Return it.
    return (Tuple*) args_obj.release();
  else
    // Not a tuple.  This happens if the format contained a single
    // argument.  Wrap the argument in a tuple.
    return Tuple::New(1, args_obj);
}


Tuple*
buildArgsFromVa(PyObject* arg0, 
		va_list vargs)
{
  if (arg0 == NULL)
    return Tuple::New(0);
  else {
    va_list copy;
    va_copy(copy, vargs);
    int object_count = 1;
    while (va_arg(copy, PyObject*) != NULL) 
      ++object_count;
    va_end(copy);

    Ref<Tuple> args = Tuple::New(object_count);
    args->InitializeItem(0, arg0);
    for (int i = 1; i < object_count; ++i) {
      Object* object = (Object*) va_arg(vargs, PyObject*);
      args->InitializeItem(i, object);
    }
    return args.release();
  }
}


}  // anonymous namespace

//----------------------------------------------------------------------
// member definitions
//----------------------------------------------------------------------

/* Python type information for C++ type 'double'.  */

template<>
PyTypeObject* const
PythonType<double>::type = &PyFloat_Type;


template<>
const char
PythonType<double>::code = 'f';


/* Python type information for C++ type 'int'.  */

template<>
PyTypeObject* const
PythonType<long>::type = &PyInt_Type;


template<>
const char
PythonType<long>::code = 'l';


//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

void
Exception::Get(Ref<Object>& type, 
	       Ref<Object>& value, 
	       Ref<Object>& traceback)
{
  // Get the exception state.
  PyObject* ptype;
  PyObject* pvalue;
  PyObject* ptraceback;
  PyErr_Fetch(&ptype, &pvalue, &ptraceback);
  PyErr_NormalizeException(&ptype, &pvalue, &ptraceback);
  // Set the return arguments.
  type = Ref<Object>::create(ptype);
  value = Ref<Object>::create(pvalue);
  traceback = Ref<Object>::create(ptraceback);
  // Reset the exception state to its value.
  PyErr_Restore(ptype, pvalue, ptraceback);
}


//----------------------------------------------------------------------

void
Sequence::split(Ref<Object>& ref0)
{
  if (Size() != 1)
    throw Exception(PyExc_TypeError, "sequence must have 1 element");
  ref0 = GetItem(0);
}


void
Sequence::split(Ref<Object>& ref0,
		Ref<Object>& ref1)
{
  if (Size() != 2)
    throw Exception(PyExc_TypeError, "sequence must have 2 elements");
  ref0 = GetItem(0);
  ref1 = GetItem(1);
}


void
Sequence::split(Ref<Object>& ref0,
		Ref<Object>& ref1,
		Ref<Object>& ref2)
{
  if (Size() != 3)
    throw Exception(PyExc_TypeError, "sequence must have 3 elements");
  ref0 = GetItem(0);
  ref1 = GetItem(1);
  ref2 = GetItem(2);
}


//----------------------------------------------------------------------

inline Tuple*
Tuple::New(int size,
	   PyObject* object0, 
	   ...)
{
  va_list vargs;
  va_start(vargs, object0);

  Ref<Tuple> result = Tuple::New(size);
  result->InitializeItem(0, object0);
  for (int i = 1; i < size; ++i)
    result->InitializeItem(i, va_arg(vargs, PyObject*));
  va_end(vargs);

  return result.release();
}


//----------------------------------------------------------------------

Module*
Module::Initialize(const char* name,
		   PyMethodDef* functions,
		   PyTypeObject** types,
		   const char* doc_string)
{
  // Create the module.  This function also adds the functions to the
  // module's dictionary. 
  Ref<Module> module
    (Py_InitModule3((char*) name, functions, (char*) doc_string));
  if (module == NULL)
    throw Exception();

  // Add types to the module's dictionary.
  Dict* dict = module->GetDict();
  for (PyTypeObject* type = *types;
       type != NULL;
       type = *++types) {
    // Set up the type.
    if (PyType_Ready(type) < 0)
      throw Exception();
    // Add it to the module.
    dict->SetItemString(type->tp_name, (PyObject*) type);
  }

  return module.release();
}


//----------------------------------------------------------------------

Object*
Callable::CallFunction(char* format, 
		       ...)
{
  va_list va;

  va_start(va, format);
  Ref<Object> args(buildArgsFromVaFormat(format, va));
  va_end(va);
  return Call(args);
}


Object*
Object::CallMethod(char* method_name,
		   char* format,
		   ...)
{
  va_list va;

  assert(method_name != NULL);

  Ref<Object> func_obj(GetAttrString(method_name));
  if (func_obj == NULL) 
    throw Exception(PyExc_AttributeError, "%s", method_name);
  Callable* func = cast<Callable>(func_obj);

  va_start(va, format);
  Ref<Object> args(buildArgsFromVaFormat(format, va));
  va_end(va);

  return func->Call(args);
}


Object*
Object::CallMethodObjArgs(char* method_name,
			  PyObject* arg0,
			  ...)
{
  assert(method_name != NULL);

  Ref<Object> func_obj = GetAttrString(method_name);
  Callable* func = cast<Callable>(func_obj);

  va_list vargs;
  va_start(vargs, arg0);
  Ref<Tuple> args = buildArgsFromVa(arg0, vargs);
  va_end(vargs);
  
  return func->Call(args);
}


Object*
Callable::CallFunctionObjArgs(PyObject* arg0, 
			      ...)
{
  va_list vargs;
  va_start(vargs, arg0);
  Ref<Tuple> args = buildArgsFromVa(arg0, vargs);
  va_end(vargs);

  return Call(args);
}


List*
List::New(Sequence* sequence)
{
  int num_elements  = sequence->Size();
  Ref<List> result = List::New(num_elements);
  for (int e = 0; e < num_elements; ++e) {
    Ref<Object> item = sequence->GetItem(e);
    result->InitializeItem(e, item);
  }

  return result.release();
}


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

Object*
import(const char* module_name, 
       const char* name)
{
  Ref<Module> module = Module::Import(module_name);
  Dict* module_dict = module->GetDict();
  return module_dict->GetItemString(name);
}


Object*
callByNameObjArgs(const char* module,
		  const char* name,
		  PyObject* arg0,
		  ...)
{
  va_list vargs;
  va_start(vargs, arg0);
  Ref<Tuple> args = buildArgsFromVa(arg0, vargs);
  va_end(vargs);

  Ref<Object> function_obj = import(module, name);
  Callable* function = cast<Callable>(function_obj);
  Ref<Object> result = function->Call(args);
  return result.release();
}


void
printException(std::ostream& os)
{
  // Fetch the Python exception state.
  Ref<Object> type;
  Ref<Object> value;
  Ref<Object> traceback;
  PyErr_Fetch
    ((PyObject**) &type, (PyObject**) &value, (PyObject**) &traceback);

  // Is there an exception set?
  if (type == NULL) {
    // Nope.
    os << "no exception" << std::flush;
    return;
  }
  
  // Print the exception type.
  Ref<Object> type_name_obj = type->GetAttrString("__name__");
  os << type_name_obj << ": ";
  // Print the exception value, if present.
  if (value != NULL) {
    Ref<String> value_str = value->Str();
    os << value;
  }
  else
    os << "NULL value";
}


void
Warn(PyObject* warning_type,
     const char* format,
     ...)
{
  // Construct the exception message from the format arguments.
  char message[1024];
  va_list vargs;
  va_start(vargs, format);
  vsnprintf(message, sizeof(message), format, vargs);
  va_end(vargs);
  // Emit the warning.
  if (PyErr_Warn(warning_type, message) == -1)
    throw Exception();
}


void
registerReduce(PyTypeObject* type,
	       Object* reduce_fn)
{
  Ref<Object> register_obj = import("copy_reg", "pickle");
  Callable* register_fn = cast<Callable>(register_obj);
  Ref<Object> result = 
    register_fn->CallFunctionObjArgs((PyObject*) type, reduce_fn, NULL);
}


std::pair<double, double>
getPoissonErrors(int value)
{
  const static double errors[100][2] = {
    {  0.0000000,  1.1478745 },
    {  1.0000000,  1.3597372 },
    {  2.0000000,  1.5192005 },
    {  2.1433734,  1.7242284 },
    {  2.2968057,  1.9818581 },
    {  2.4899673,  2.2106630 },
    {  2.6792144,  2.4185941 },
    {  2.8595224,  2.6105048 },
    {  3.0307020,  2.7896162 },
    {  3.1935073,  2.9581952 },
    {  3.3488269,  3.1179092 },
    {  3.4974864,  3.2700271 },
    {  3.6402065,  3.4155408 },
    {  3.7776054,  3.5552434 },
    {  3.9102102,  3.6897810 },
    {  4.0384722,  3.8196880 },
    {  4.1627797,  3.9454123 },
    {  4.2834682,  4.0673343 },
    {  4.4008302,  4.1857797 },
    {  4.5151215,  4.3010302 },
    {  4.6265675,  4.4133314 },
    {  4.7353679,  4.5228990 },
    {  4.8417002,  4.6299237 },
    {  4.9457235,  4.7345747 },
    {  5.0475804,  4.8370034 },
    {  5.1473997,  4.9373458 },
    {  5.2452981,  5.0357246 },
    {  5.3413815,  5.1322506 },
    {  5.4357467,  5.2270250 },
    {  5.5284821,  5.3201398 },
    {  5.6196689,  5.4116793 },
    {  5.7093817,  5.5017209 },
    {  5.7976894,  5.5903358 },
    {  5.8846557,  5.6775899 },
    {  5.9703398,  5.7635439 },
    {  6.0547965,  5.8482544 },
    {  6.1380768,  5.9317739 },
    {  6.2202285,  6.0141512 },
    {  6.3012960,  6.0954320 },
    {  6.3813211,  6.1756590 },
    {  6.4603428,  6.2548721 },
    {  6.5383978,  6.3331088 },
    {  6.6155207,  6.4104045 },
    {  6.6917440,  6.4867922 },
    {  6.7670985,  6.5623032 },
    {  6.8416130,  6.6369672 },
    {  6.9153149,  6.7108119 },
    {  6.9882304,  6.7838638 },
    {  7.0603839,  6.8561479 },
    {  7.1317987,  6.9276879 },
    {  7.2024972,  6.9985063 },
    {  7.2725004,  7.0686245 },
    {  7.3418283,  7.1380630 },
    {  7.4105002,  7.2068411 },
    {  7.4785342,  7.2749773 },
    {  7.5459478,  7.3424892 },
    {  7.6127576,  7.4093938 },
    {  7.6789796,  7.4757071 },
    {  7.7446289,  7.5414445 },
    {  7.8097202,  7.6066209 },
    {  7.8742674,  7.6712502 },
    {  7.9382839,  7.7353461 },
    {  8.0017827,  7.7989216 },
    {  8.0647759,  7.8619891 },
    {  8.1272758,  7.9245604 },
    {  8.1892931,  7.9866477 },
    {  8.2508394,  8.0482615 },
    {  8.3119250,  8.1094125 },
    {  8.3725602,  8.1701111 },
    {  8.4327548,  8.2303673 },
    {  8.4925182,  8.2901904 },
    {  8.5518595,  8.3495897 },
    {  8.6107876,  8.4085742 },
    {  8.6693109,  8.4671523 },
    {  8.7274377,  8.5253324 },
    {  8.7851759,  8.5831225 },
    {  8.8425333,  8.6405303 },
    {  8.8995172,  8.6975633 },
    {  8.9561348,  8.7542287 },
    {  9.0123931,  8.8105337 },
    {  9.0682989,  8.8664848 },
    {  9.1238587,  8.9220889 },
    {  9.1790788,  8.9773522 },
    {  9.2339654,  9.0322809 },
    {  9.2885244,  9.0868810 },
    {  9.3427617,  9.1411584 },
    {  9.3966829,  9.1951187 },
    {  9.4502934,  9.2487674 },
    {  9.5035985,  9.3021099 },
    {  9.5566034,  9.3551513 },
    {  9.6093132,  9.4078967 },
    {  9.6617325,  9.4603510 },
    {  9.7138664,  9.5125190 },
    {  9.7657192,  9.5644050 },
    {  9.8172956,  9.6160140 },
    {  9.8685998,  9.6673500 },
    {  9.9196363,  9.7184180 },
    {  9.9704090,  9.7692210 },
    { 10.0209221,  9.8197640 },
    { 10.0711795,  9.8700510 },
  };

  assert(value >= 0);

  if (value < 100) 
    return std::pair<double, double>(errors[value][0], errors[value][1]);
  else {
    double error = sqrt(value);
    return std::pair<double, double>(error, error);
  }
}


//----------------------------------------------------------------------

}  // namespace Py
