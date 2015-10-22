//----------------------------------------------------------------------
//
// python.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* C++ wrappers for the Python C API, and other utilities.  */

#ifndef __PYTHON_HH__
#define __PYTHON_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#undef _POSIX_C_SOURCE

#include <cassert>
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <Python.h>
#include <string>
#include <structmember.h>

#include "config.h"

//----------------------------------------------------------------------
// macros
//----------------------------------------------------------------------

#define RETURN(TYPE, EXPRESSION)                                       \
  do {                                                                 \
    PyObject* object = (EXPRESSION);                                   \
    if (object == NULL)                                                \
      throw Py::Exception();                                           \
    else                                                               \
      return (TYPE*) object;                                           \
  } while (0)

#define RETURN_REF(TYPE, EXPRESSION)                                   \
  do {                                                                 \
    PyObject* object = (EXPRESSION);                                   \
    if (object == NULL)                                                \
      throw Py::Exception();                                           \
    else                                                               \
      return Py::Ref<TYPE >(object);                                   \
  } while (0)

#define RETURN_NEW_REF(TYPE, EXPRESSION)                               \
  do {                                                                 \
    PyObject* object = (EXPRESSION);                                   \
    if (object == NULL)                                                \
      throw Py::Exception();                                           \
    else {                                                             \
      Py_INCREF(object);                                               \
      return (TYPE*) object;                                           \
    }                                                                  \
  } while (0)

#define RETURN_OBJ_REF(EXPRESSION)                                     \
  RETURN_NEW_REF(Py::Object, EXPRESSION)  

#define RETURN_BOOL(EXPRESSION)                                        \
  do {                                                                 \
    int result = (EXPRESSION);                                         \
    if (result == 1)                                                   \
      return true;                                                     \
    else if (result == 0)                                              \
      return false;                                                    \
    else if (result == -1)                                             \
      throw Py::Exception();                                           \
    else                                                               \
      abort();                                                         \
  } while (0)

#define RETURN_TRUE                                                    \
  RETURN_NEW_REF(Object, Py_True)

#define RETURN_FALSE                                                   \
  RETURN_NEW_REF(Object, Py_False)

#define THROW_IF_NULL(OBJECT_PTR)                                      \
  if ((OBJECT_PTR) == NULL) throw Py::Exception()

#define THROW_IF_MINUS_ONE(EXPR)                                       \
  if ((EXPR) == -1) throw Py::Exception()

#define RETURN_NONE                                                    \
  do { return newRef(None); } while(0)

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

namespace Py {

struct Complex;
struct Dict;
struct Float;
struct Int;
struct Iter;
struct Object;
struct String;

template <class SUBCLASS>
inline SUBCLASS* cast(PyObject* object);

template<class CLASS>
inline CLASS* newRef(CLASS* object);

extern Object* None;

inline Dict* getThreadStateDict();

//----------------------------------------------------------------------
// Python reference types
//----------------------------------------------------------------------

class BaseRef_
{
public:

  ~BaseRef_() 
    { dec(); }

  operator Object* () const
    { return object_; }

  void clear();

  Object* release() const
    { Object* object = object_; object_ = NULL; return object; }
  
  bool operator== (Object* object) const
    { return object_ == object; }

  bool operator!= (Object* object) const
    { return object_ != object; }

protected:

  explicit BaseRef_(PyObject* object) : object_((Object*) object) {}

  mutable Object* object_;

  void inc() const;
  void dec() const;

};



template<class CLASS>
class Ref
  : public BaseRef_
{
public:

  static Ref create(PyObject* object)
    { Ref ref(object); ref.inc(); return ref; }

  Ref()
    : BaseRef_(NULL)
  {}

  Ref(CLASS* object)
    : BaseRef_(object)
  {}

  Ref(PyObject* object);

  Ref(const Ref& ref);

  void operator = (const Ref& ref)
    { dec(); object_ = ref.release(); }

  void set(CLASS* object)
    { dec(); object_ = object; }

  operator CLASS* () const
    { return (CLASS*) object_; }

  CLASS* operator -> () const
    { return (CLASS*) object_; }

  Ref copy() const
    { return create(object_); }

  CLASS* release() const
    { return (CLASS*) BaseRef_::release(); }

};


//----------------------------------------------------------------------
// exceptions
//----------------------------------------------------------------------

/* A C++ class representing a Python exception.

   Throw an 'Exception' instance to propagate a Python exception up to
   the boundary of the extension module.
*/

struct Exception 
{
  /* Represent an existing Python exception.

     Use this constructor when throwing an 'Exception' in response to a
     Python exception that is already set (such as when a Python API
     function returns a failure code).
  */
  Exception() {}

  /* Create a new Python exception.

     'exception' -- The Python exception class.

     'format, ...' -- The exception message as 'printf'-style format
     arguments.
  */
  Exception(PyObject* exception, const char* format, ...);

  void vaSetException(PyObject* exception, const char* format, 
		      va_list vars);

  /* Get the exception state.  

     Set the values of 'type', 'value', and 'traceback' to the current
     Python exception's exception type, value, and traceback object,
     respectively.  If no exception is currently set, all three are set
     to NULL.

     Does not clear the exception state.  
  */
  void Get(Ref<Object>& type, Ref<Object>& value, Ref<Object>& traceback);

  /* Print the exception traceback to standard error.  */
  void Print() { PyErr_Print(); }

  /* Clean up the Python exception state.  */
  void Clear() { PyErr_Clear(); }

};


inline
Exception::Exception(PyObject* exception,
		     const char* format,
		     ...)
{
  va_list vargs;
  va_start(vargs, format);
  vaSetException(exception, format, vargs);
  va_end(vargs);
}


inline void
Exception::vaSetException(PyObject* exception,
			  const char* format,
			  va_list vargs)
{
  // Construct the exception message from the format arguments.
  char message[1024];
  vsnprintf(message, sizeof(message), format, vargs);
  // Set the Python expression.
  PyErr_SetString(exception, message);
}


struct ExceptionFromErrno
  : public Exception
{
  ExceptionFromErrno(PyObject* exception=PyExc_IOError);

};


inline
ExceptionFromErrno::ExceptionFromErrno(PyObject* exception)
  : Exception()
{
  PyErr_SetFromErrno(exception);
}


//----------------------------------------------------------------------
// lock objects
//----------------------------------------------------------------------

/* A lock on the Python global interpreter lock.  */

class InterpreterLock
{
public:

  InterpreterLock() { PyEval_AcquireLock(); }
  ~InterpreterLock() { PyEval_ReleaseLock(); }

};


/* A temporary swap of the thread state.

   On construction, sets Python's thread state to the specified thread
   state.  On exit, restores the previous thread state.  Also takes a
   global interpreter lock.

 */

class ThreadStateSwap
{
public:

  ThreadStateSwap(PyThreadState* thread_state);
  ~ThreadStateSwap();

private:

  InterpreterLock interpreter_lock_;
  PyThreadState* previous_state_;

};


inline
ThreadStateSwap::ThreadStateSwap(PyThreadState* thread_state)
  : interpreter_lock_(),
    previous_state_(PyThreadState_Swap(thread_state))
{
}


inline
ThreadStateSwap::~ThreadStateSwap()
{
  PyThreadState_Swap(previous_state_);
}


//----------------------------------------------------------------------
// wrappers for Python type structs
//----------------------------------------------------------------------

struct Object
  : public PyObject
{
  static bool Check(PyObject* object) 
    { return true; }

  int GetRefCount() const
    { return ob_refcnt; }

  void IncRef()
    { Py_INCREF(this); }

  void DecRef()
    { Py_DECREF(this); }

  void Print(FILE* file, int flags) 
    { THROW_IF_MINUS_ONE(PyObject_Print(this, file, flags)); }

  void PrintRepr(FILE* file=stdout)
    { Print(file, 0); }

  void PrintStr(FILE* file=stdout)
    { Print(file, Py_PRINT_RAW); }

  /* Return a new ref to the representation of this object.  */
  String* Repr() 
    { RETURN(String, PyObject_Repr(this)); }

  /* Return the string contents of the representation of this object.  */
  std::string ReprAsString();

  /* Return a new ref to the string name of this object.  */
  String* Str()
    { RETURN(String, PyObject_Str(this)); }

  /* Return the string contents of the string name of this object.  */
  std::string StrAsString();

  /* Return a new ref for the object interpreted as a 'float'.  */
  struct Float* Float()
    { RETURN(struct Float, PyNumber_Float(this)); }

  /* Return the value of the object interpreted as a 'float'.  */
  double FloatAsDouble();

  /* Return an new ref for the object interpreted as an 'int'.  */
  struct Int* Int()
    { RETURN(struct Int, PyNumber_Int(this)); }

  /* Return the value of the object interpreted as an 'int'.  */
  long IntAsLong();

  /* Return a new ref for the object interpreted as a 'complex'.  */
  struct Complex* Complex();

  /* Return the value of the object interpreted as a 'complex'.  */
  std::complex<double> AsComplex();

  Iter* GetIter()
    { RETURN(struct Iter, PyObject_GetIter(this)); }

  /* Return a new ref to the attribute named by 'name'.  */
  Object* GetAttr(PyObject* name)
    { RETURN(Object, PyObject_GetAttr(this, name)); }

  /* Return a new ref to the attribute named by 'name'.  */
  Object* GetAttrString(const char* name) 
    { RETURN(Object, PyObject_GetAttrString(this, (char*) name)); }

  bool HasAttrString(const char* name) 
    { return (bool) PyObject_HasAttrString(this, (char*) name); }

  void SetAttr(PyObject* key, PyObject* value)
    { THROW_IF_MINUS_ONE(PyObject_SetAttr(this, key, value)); }

  void SetAttrString(const char* name, PyObject* value) 
    { THROW_IF_MINUS_ONE(PyObject_SetAttrString(this, (char*) name, value)); }
  
  /* Return a new ref to the item whose key or index is 'key'.  */
  Object* GetItem(PyObject* key)
    { RETURN(Object, PyObject_GetItem(this, key)); }

  void SetItem(PyObject* key, PyObject* value)
    { THROW_IF_MINUS_ONE(PyObject_SetItem(this, key, value)); }

  int Hash()
    { return PyObject_Hash(this); }

  bool IsTrue()
    { return (bool) PyObject_IsTrue(this); }

  bool Not()
    { return (bool) PyObject_Not(this); }

  Object* CallMethod(char* method_name, char* format, ...);

  Object* CallMethodObjArgs(char* method_name, PyObject* arg0, ...);

  bool IsInstance(PyTypeObject* type)
    { return IsInstance((PyObject*) type); }

  bool IsInstance(PyObject* typeOrClass)
    { return (bool) PyObject_IsInstance(this, typeOrClass); }

  bool IsSubclassOf(PyObject* object)
    { RETURN_BOOL(PyObject_IsSubclass(this, object)); }

  bool IsSubclassOf(PyTypeObject* object)
    { return IsSubclassOf((PyObject*) object); }

  bool TypeCheck(PyTypeObject* type)
    { return (bool) PyObject_TypeCheck(this, type); }

  bool Compare(PyObject* other);

  void AsCharBuffer(const char** buffer, int* buffer_len)
    { THROW_IF_MINUS_ONE(PyObject_AsCharBuffer(this, buffer, buffer_len)); }

  void AsReadBuffer(const char** buffer, int* buffer_len);

  void AsWriteBuffer(char** buffer, int* buffer_len);

};


inline void
Object::AsReadBuffer(const char** buffer,
		     int* buffer_len)
{ 
  THROW_IF_MINUS_ONE(
    PyObject_AsReadBuffer(this, (const void**) buffer, buffer_len));
}


inline void
Object::AsWriteBuffer(char** buffer,
		      int* buffer_len)
{ 
  THROW_IF_MINUS_ONE(
    PyObject_AsWriteBuffer(this, (void**) buffer, buffer_len));
}


//----------------------------------------------------------------------

inline void 
BaseRef_::inc() 
  const 
{ 
  if (object_ != NULL) 
    object_->IncRef(); 
}


inline void 
BaseRef_::dec() 
  const 
{ 
  if (object_ != NULL) 
    object_->DecRef(); 
}


//----------------------------------------------------------------------

struct Type
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyType_Check(object); }

  bool IsSubtype(PyObject* type);

  bool IsSubtype(PyTypeObject* type)
    { return (bool) PyType_IsSubtype((PyTypeObject*) this, type); }

  const char* GetName()
    { return ((PyTypeObject*) this)->tp_name; }

};


inline bool 
Type::IsSubtype(PyObject* type)
{ 
  return (bool) 
    PyType_IsSubtype((PyTypeObject*) this, (PyTypeObject*) type); 
}


//----------------------------------------------------------------------

struct Callable
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyCallable_Check(object); }

  Object* Call(PyObject* args=NULL, PyObject* kw_args=NULL);

  Object* CallObject(PyObject* args)
    { RETURN(Object, PyObject_CallObject(this, args)); }

  Object* CallFunction(char* format, ...);

  Object* CallFunctionObjArgs(PyObject* arg0, ...);

};


//----------------------------------------------------------------------

struct Number
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyNumber_Check(object); }

  Object* Negative()
    { RETURN(Object, PyNumber_Negative(this)); }

  Object* Add(PyObject* other)
    { RETURN(Object, PyNumber_Add(this, other)); }

  Object* Subtract(PyObject* other)
    { RETURN(Object, PyNumber_Subtract(this, other)); }

  Object* Multiply(PyObject* other)
    { RETURN(Object, PyNumber_Multiply(this, other)); }

  Object* Divide(PyObject* other)
    { RETURN(Object, PyNumber_Divide(this, other)); }

  Object* TrueDivide(PyObject* other)
    { RETURN(Object, PyNumber_TrueDivide(this, other)); }

  Object* FloorDivide(PyObject* other)
    { RETURN(Object, PyNumber_FloorDivide(this, other)); }

  Object* Remainder(PyObject* other)
    { RETURN(Object, PyNumber_Remainder(this, other)); }

  Object* Power(PyObject* other)
    { RETURN(Object, PyNumber_Power(this, other, None)); }
  
};

//----------------------------------------------------------------------

struct Int
  : public Number
{
  static bool Check(PyObject* object)
    { return (bool) PyInt_Check(object); }

  static Int* FromLong(long value)
    { RETURN(Int, PyInt_FromLong(value)); }

  long AsLong()
    { return PyInt_AS_LONG(this); }

};


//----------------------------------------------------------------------

struct Float
  : public Number
{
  static bool Check(PyObject* object)
    { return (bool) PyFloat_Check(object); }

  static Float* FromDouble(double value)
    { RETURN(Float, PyFloat_FromDouble(value)); }

  double AsDouble()
    { return PyFloat_AS_DOUBLE(this); }

};


//----------------------------------------------------------------------

struct Complex
  : public Number
{
  static bool Check(PyObject* object)
    { return (bool) PyComplex_Check(object); }

  static Complex* FromComplex(std::complex<double> value)
    { RETURN(Complex, PyComplex_FromDoubles(real(value), imag(value))); }

  static Complex* FromDoubles(double re, double im)
    { RETURN(Complex, PyComplex_FromDoubles(re, im)); }

  double RealAsDouble()
    { return PyComplex_RealAsDouble(this); }

  double ImagAsDouble()
    { return PyComplex_ImagAsDouble(this); }

  std::complex<double> AsComplex()
    { return std::complex<double>(PyComplex_RealAsDouble(this), 
 				  PyComplex_ImagAsDouble(this)); }

};


//----------------------------------------------------------------------


struct String
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyString_Check(object); }

  static String* FromStringAndSize(const char* string, int size)
    { RETURN(String, PyString_FromStringAndSize(string, size)); }
  
  static String* FromString(const char* string)
    { RETURN(String, PyString_FromString(string)); }

  static String* FromString(const std::string& string)
    { return FromStringAndSize(string.c_str(), string.size()); }

  static String* InternFromString(const char* string)
    { RETURN(String, PyString_InternFromString(string)); }

  static String* FromFormat(const char* format, ...);

  int Size()
    { return PyString_GET_SIZE(this); }

  const char* AsString()
    { return PyString_AS_STRING(this); }

  operator char* ()
    { return PyString_AS_STRING(this); }

  String* Concat(String* other);

};


inline String*
String::FromFormat(const char* format,
		   ...)
{
  va_list vargs;
  va_start(vargs, format);
  String* result = (String*) PyString_FromFormatV(format, vargs);
  va_end(vargs);
  RETURN(String, result);
}


inline String*
String::Concat(String* other)
{
  String* self = this;
  // PyString_Concat steals a reference to its first arg, so up it
  // first. 
  self->IncRef();
  PyString_Concat((PyObject**) &self, other);
  if (self == NULL)
    throw Exception();
  return self;
}


//----------------------------------------------------------------------

struct Sequence
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PySequence_Check(object); }

  int Size()
    { return PySequence_Size(this); }

  /* Return a new reference to the indexed item.  */
  Object* GetItem(int index)
    { RETURN(Object, PySequence_GetItem(this, index)); }

  void SetItem(int index, PyObject* value)
    { THROW_IF_MINUS_ONE(PySequence_SetItem(this, index, value)); }

  void split(Ref<Object>&);
  void split(Ref<Object>&, Ref<Object>&);
  void split(Ref<Object>&, Ref<Object>&, Ref<Object>&);

};


//----------------------------------------------------------------------

struct Iter
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyIter_Check(object); }

  /* Return the next item from the iterator.

     returns -- A new reference to the next item from the iterator.  If
     there are no remaining items, returns NULL without setting a Python
     exception. 
  */
  Object* Next();

};


inline Object*
Iter::Next()
{
  Object* result = (Object*) PyIter_Next(this);
  if (result == NULL && PyErr_Occurred())
    throw Exception();
  else
    return result;
}


//----------------------------------------------------------------------

struct Tuple
  : public Sequence
{
  static bool Check(PyObject* object)
    { return (bool) PyTuple_Check(object); }

  /* Create a new tuple of 'size' items.

     Each item must be initialized by 'InitializeItem' before the tuple
     is used or deallocated.  
  */ 
  static Tuple* New(int size=0)
    { RETURN(Tuple, PyTuple_New(size)); }

  /* Create a new tuple, initialized with objects.

     Create a new tuple of 'size' elements whose elements are
     initialized to new refs of the objects specified as arguments.  At
     least 'size' object arguments must be provided; additional
     arguments are ignored.
  */
  static Tuple* New(int size, PyObject*, ...); 

  int Size()
    { return PyTuple_Size(this); }

  Object* GetItem(int index)
    { RETURN_NEW_REF(Object, PyTuple_GET_ITEM(this, index)); }

  /* Initialize item 'index' to a new ref of 'object'.  */
  void InitializeItem(int index, PyObject* object)
    { Py_INCREF(object); PyTuple_SET_ITEM(this, index, object); }

  void ParseTuple(char* format, ...);

};


inline void
Tuple::ParseTuple(char* format,
		  ...)
{
  va_list vargs;
  va_start(vargs, format);
  bool result = (bool) PyArg_VaParse(this, format, vargs);
  va_end(vargs);
  if (! result)
    throw Exception();
}


//----------------------------------------------------------------------

struct List
  : public Sequence
{
  static bool Check(PyObject* object)
    { return (bool) PyList_Check(object); }

  static List* New(int size=0)
    { RETURN(List, PyList_New(size)); }

  /* Create a new list by (shallowly) copying 'sequence'.  */
  static List* New(Sequence* sequence); 

  void Append(PyObject* object)
    { THROW_IF_MINUS_ONE(PyList_Append(this, object)); }

  Object* GetItem(int index)
    { RETURN_NEW_REF(Object, PyList_GET_ITEM(this, index)); }

  void InitializeItem(int index, PyObject* object)
    { Py_INCREF(object); PyList_SET_ITEM(this, index, object); }

};


//----------------------------------------------------------------------

struct Mapping
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyMapping_Check(object); }

  int Size()
    { return PyMapping_Size(this); }

  Sequence* Keys();

  Sequence* Items()
    { RETURN(Sequence, PyMapping_Items(this)); }

  bool HasKey(PyObject* key)
    { return PyMapping_HasKey(this, key) == 1; }

  bool HasKeyString(const char* key)
    { return PyMapping_HasKeyString(this, (char*) key) == 1; }

  Object* GetItemString(const char* name)
    { RETURN(Object, PyMapping_GetItemString(this, (char*) name)); }

  /* Look up a value, with a default.

     Returns a new ref to the value corresponding to 'key', or a new ref
     to 'default_value' if 'key' is not in the mapping.  
  */
  Object* GetItemString(const char* key, Object* default_value);

  void SetItemString(const char* name, PyObject* value)
    { THROW_IF_MINUS_ONE(PyMapping_SetItemString(this, (char*) name, value)); }

};


inline Sequence*
Mapping::Keys()
{
  Ref<Object> keys = PyMapping_Keys(this);
  THROW_IF_NULL(keys);
  Sequence* result = cast<Sequence>(keys);
  RETURN_NEW_REF(Sequence, result);
}


inline Object*
Mapping::GetItemString(const char* name, 
		       Object* default_value)
{
  Object* result = (Object*) PyMapping_GetItemString(this, (char*) name);
  if (result == NULL) 
    return newRef(default_value);
  else
    return result;
}


//----------------------------------------------------------------------

struct Dict
  : public Mapping
{
  static bool Check(PyObject* object)
    { return (bool) PyDict_Check(object); }

  static Dict* New()
    { RETURN(Dict, PyDict_New()); }

  static Dict* Copy(PyObject* object)
    { RETURN(Dict, PyDict_Copy(object)); }

  void Clear()
    { PyDict_Clear(this); }

  void Merge(PyObject* object, bool override=true) 
    { THROW_IF_MINUS_ONE(PyDict_Merge(this, object, override ? 1 : 0)); }

  void SetItem(PyObject* key, PyObject* value)
    { THROW_IF_MINUS_ONE(PyDict_SetItem(this, key, value)); }

  void DelItem(PyObject* key)
    { THROW_IF_MINUS_ONE(PyDict_DelItem(this, key)); }

  void DelItemString(const char* name)
    { THROW_IF_MINUS_ONE(PyDict_DelItemString(this, (char*) name)); }

  Object* GetItem(PyObject* key);

  Object* GetItemString(const char* name);

  void Update(PyObject* other) 
    { THROW_IF_MINUS_ONE(PyDict_Update(this, other)); }

  bool Next(int& position, PyObject*& key, PyObject*& value)
    { return PyDict_Next(this, &position, &key, &value) != 0; }

};


inline Object*
Dict::GetItem(PyObject* key)
{
  Object* result = (Object*) PyDict_GetItem(this, key);
  if (result == NULL) {
    Ref<String> key_repr = ((Py::Object*) key)->Repr();
    throw Exception(PyExc_KeyError, "%s", key_repr->AsString());
  }
  else 
    return newRef(result);
}


inline Object* 
Dict::GetItemString(const char* name)
{ 
  Object* result = (Object*) PyDict_GetItemString(this, (char*) name);
  if (result == NULL)
    throw Exception(PyExc_KeyError, "%s", name);
  else 
    return newRef(result);
}


//----------------------------------------------------------------------

struct Module
  : public Object
{
  static bool Check(PyObject* object)
    { return (bool) PyModule_Check(object); } 

  static Module* Import(const char* name)
    { RETURN(Module, PyImport_ImportModule((char*) name)); }

  /* Create a new module.  

     'name' -- The module name.  If the module is initialized from
     function 'initFoo', the module name must be 'Foo'.  

     'functions' -- An array of 'PyMethodDef' describing functions in
     the module.  The last element must be all NULL.  

     'types' -- A NULL-terminated array of Python type objects
     describing types in the module.  

     'doc_string' -- The module's doc string.

     returns -- A new reference to the new module.  */
  static Module* Initialize(const char* name, 
			    PyMethodDef* functions,
			    PyTypeObject** types, 
			    const char* doc_string);

  /* Return the module's dictionary.  */
  Dict* GetDict()
    { RETURN_NEW_REF(Dict, PyModule_GetDict(this)); }

};


//----------------------------------------------------------------------

struct Arg
  : public Tuple
{
};


//----------------------------------------------------------------------
// Additional classes
//----------------------------------------------------------------------

/* Template wrapper for Python type information.

   Python type information corresponding to actual C++ types is provided
   in template specializations.  
*/

template<typename TYPE>
class PythonType
{
public:

  /* The type object for the Python type used to represent values this
     C++ type.  */
  static PyTypeObject* const type;

  /* The character type code (ala the Python 'array' module)
     corresponding to this C++ type.  */
  static const char code;

  /* Conversion function from a Python object to 'TYPE'.  */
  static TYPE fromPyObject(Object* object);

  /* Conversion function from 'TYPE' to a Python object.  */
  static Object* asPyObject(TYPE value);

};


/* Python type information for C++ type 'double'.  */

template<>
inline double
PythonType<double>::fromPyObject(Object* object)
{
  return object->FloatAsDouble();
}


template<>
inline Object*
PythonType<double>::asPyObject(double value)
{
  return Float::FromDouble(value);
}


/* Python type information for C++ type 'int'.  */

template<>
inline long
PythonType<long>::fromPyObject(Object* object)
{
  return object->IntAsLong();
}


template<>
inline Object*
PythonType<long>::asPyObject(long value)
{
  return Int::FromLong(value);
}


//----------------------------------------------------------------------

template<class CLASS, const char* const* KEY>
class ThreadSingleton
{
public:

  ThreadSingleton();
  ~ThreadSingleton();
  static CLASS* getInstance();

};


template<class CLASS, const char* const* KEY>
inline
ThreadSingleton<CLASS, KEY>::ThreadSingleton()
{
  assert(*KEY != NULL);
  Ref<Dict> threadStateDict = getThreadStateDict();
  Ref<String> key = String::FromString(*KEY);
  // Make sure there isn't another instance registered in this thread.
  assert(! threadStateDict->HasKey(key));
  // Register this instance.
  Ref<Int> value = Int::FromLong(reinterpret_cast<long>(this));
  threadStateDict->SetItem(key, value);
}


template<class CLASS, const char* const* KEY>
inline
ThreadSingleton<CLASS, KEY>::~ThreadSingleton()
{
  Ref<Dict> threadStateDict = getThreadStateDict();
  Ref<String> key = String::FromString(*KEY);
  // Make sure this instance is registered in this thread.
  assert(threadStateDict->HasKey(key));
  Ref<Object> value = threadStateDict->GetItem(key);
  assert(value->IntAsLong() == reinterpret_cast<long>(this));
  // Unregister this instance.
  threadStateDict->DelItem(key);
}


template<class CLASS, const char* const* KEY>
inline CLASS*
ThreadSingleton<CLASS, KEY>::getInstance()
{
  Ref<Dict> threadStateDict = getThreadStateDict();
  Ref<String> key = String::FromString(*KEY);
  // Look up the instance.
  assert(threadStateDict->HasKey(key));
  Ref<Object> value = threadStateDict->GetItem(key);
  CLASS* instance = reinterpret_cast<CLASS*>(value->IntAsLong());
  assert(instance != NULL);
  return instance;
}


//----------------------------------------------------------------------
// additional inline methods
//----------------------------------------------------------------------

inline void
BaseRef_::clear()
{ 
  if (object_ == NULL)
    return;
  Object* object = object_; 
  object_ = NULL; 
  object->DecRef(); 
}


template<class CLASS>
Ref<CLASS>::Ref(PyObject* object)
  : BaseRef_(cast<CLASS>(object))
{
}


template<class CLASS>
Ref<CLASS>::Ref(const Ref<CLASS>& ref)
  : BaseRef_(ref.release())
{
}


inline std::string
Object::ReprAsString()
{
  Ref<String> repr = Repr();
  return std::string(repr->AsString());
}


inline std::string
Object::StrAsString()
{
  Ref<String> str = Str();
  return std::string(str->AsString());
}


inline long
Object::IntAsLong()
{
  Ref<Py::Int> number = Int();
  return number->AsLong();
}


inline Complex*
Object::Complex()
{
  // Is it already a complex?
  if (PyComplex_Check(this)) 
    // Yes.  Return a new reference to the same object.
    return newRef((struct Complex*) this);
  else {
    // No.  Try to cast it to a float.
    struct Float* as_float = (struct Float*) PyNumber_Float(this);
    if (as_float == NULL)
      // Didn't work/
      throw Exception(PyExc_ValueError, "invalid value for complex");
    // Use the float value as the real part.
    Ref<struct Complex> result = 
      Complex::FromDoubles(as_float->AsDouble(), 0);
    return result.release();
  }
}


inline std::complex<double>
Object::AsComplex()
{
  Ref<struct Complex> as_complex = this->Complex();
  return as_complex->AsComplex();
}


inline double
Object::FloatAsDouble()
{
  Ref<Py::Float> number = Float();
  return number->AsDouble();
}


inline bool
Object::Compare(PyObject* other)
{
  int cmp;
  THROW_IF_MINUS_ONE(PyObject_Cmp(this, other, &cmp));
  return cmp == 0;
}


inline Object*
Callable::Call(PyObject* args,
	       PyObject* kw_args)
{
  static Ref<Tuple> empty_args = Tuple::New();
  // An empty tuple is required for no positional arguments.
  if (args == NULL)
    args = empty_args;
  RETURN(Object, PyObject_Call(this, args, kw_args));
}


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

template <class SUBCLASS>
inline SUBCLASS* 
cast(PyObject* object)
{ 
  if (SUBCLASS::Check((Object*) object))
    return (SUBCLASS*) object;
  else 
    throw Exception(PyExc_TypeError, "type error, received %s",
		    object->ob_type->tp_name);
}


/* Import a name.

   'module_name' -- The module to import from.

   'name' -- The name of the object to import.

   returns -- A new reference.  */
extern Object* 
import(const char* module_name, const char* name);


/* Import a function by name and call it.

   'module_name' -- The module to import from.

   'name' -- The name of the callabel to import.

   'arg0, ...' -- Object arguments, terminated by NULL.

   returns -- A new reference to the result of the call.  */
extern Object* callByNameObjArgs(const char* module, const char* name, 
				 PyObject* arg0, ...);


/* Print the Python exception state to 'os'.  */
extern void printException(std::ostream& os=std::cerr);

/* Format and print a warning with Python's warning facility.  */
extern void Warn(PyObject* warning_type, const char* format, ...);

/* Register a reduce function 'reduce_fn' for an extension type 'type'.  */
extern void registerReduce(PyTypeObject*, Object* reduce_fn);

/* Return Poisson lower and upper errors on 'value'.  */
extern std::pair<double, double> getPoissonErrors(int value);

//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

/* Allocate memory for an instace of extension class 'CLASS'.

   Uses the 'tp_alloc' method from the static 'type' member of 'CLASS'.
   Note that no C++ construction is performed on the new instance.
*/

template<class CLASS>
inline CLASS*
allocate()
{
  CLASS* result = (CLASS*) CLASS::type.tp_alloc(&CLASS::type, 0);
  THROW_IF_NULL(result);
  return result;
}


inline Object*
allocate(PyTypeObject* type)
{
  Object* result = (Object*) type->tp_alloc(type, 0);
  THROW_IF_NULL(result);
  return result;
}


/* Deallocate memory for a Python object.

   Note that no C++ destruction is performed on the object.
*/

template<class CLASS>
inline void
deallocate(CLASS* object)
{
  assert(object != NULL);
  object->ob_type->tp_free(object);
}


/* Return a new ref to 'object'.

   If 'object' is NULL, just return NULL.  
*/

template<class CLASS>
inline CLASS*
newRef(CLASS* object)
{
  if (object != NULL)
    Py_INCREF(object);
  return object;
}


/* Return a new ref to the object referred to by 'ref'.

   If 'ref' refers to NULL, just return NULL.  
*/

template<class CLASS>
inline CLASS*
newRef(const Ref<CLASS>& ref)
{
  return newRef((CLASS*) ref);
}


inline Object*
newBool(bool value)
{
  if (value) {
    Py_INCREF(Py_True);
    return (Object*) Py_True;
  }
  else {
    Py_INCREF(Py_False);
    return (Object*) Py_False;
  }
}


inline void 
internInPlace(Ref<String>& string)
{
  PyObject* string_ptr = string.release();
  assert(string_ptr != NULL);
  PyString_InternInPlace(&string_ptr);
  assert(string_ptr != NULL);
  string.set(cast<String>(string_ptr));
}


inline std::ostream&
operator<< (std::ostream& os,
	    BaseRef_& ref)
{
  if (ref == NULL)
    os << "NULL";
  else {
    Ref<String> repr = ((Object*) ref)->Repr();
    os << repr->AsString();
  }
  return os;
}


/* Build a C function instance.  */
inline Object* 
newCFunction(PyMethodDef* def, 
	     PyObject* self=NULL)
{
  Object* result = (Object*) PyCFunction_New(def, self);
  THROW_IF_NULL(result);
  return result;
}


inline Object*
buildValue(char* format,
	   ...)
{
  va_list vargs;
  va_start(vargs, format);
  Object* result = (Object*) Py_VaBuildValue(format, vargs);
  va_end(vargs);
  THROW_IF_NULL(result);
  return result;
}


/* Return a new reference to Python's thread-local state dictionary.  */
inline Dict*
getThreadStateDict()
{
  Object* object = (Object*) PyThreadState_GetDict();
  if (object == NULL)
    throw Exception();
  else {
    Dict* dict = cast<Dict>(object);
    return newRef(dict);
  }
}


//----------------------------------------------------------------------

}  // namespace Py


#endif  // #ifndef __PYTHON_HH__
