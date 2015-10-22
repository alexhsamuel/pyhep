//----------------------------------------------------------------------
//
// PyBoolArray.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Bit vector extension class.  

   This class is a stand-in until proper boolean types are supported in
   Python and single-bit boolean types are supported in the standard
   'array' module.  Since it's temporary, it's not really complete.
*/

#ifndef __PYBOOLARRAY_HH__
#define __PYBOOLARRAY_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>

#include "python.hh"

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

struct PyBoolArray
  : public Py::Object
{
  static PyTypeObject type;
  static PyBoolArray* New(int length);
  static bool Check(PyObject* object);

  /* Register this type for pickling.
     
    Install the unpickler function into 'module', and register it as a
    constructor with 'copy_reg'..  Register the pickler function with
    'copy_reg'.

    'module' -- The module containing this type.  
  */
  static void Register(Py::Module* module);

  // The function used to unpickle instances of this type.
  // Initizlied by 'Register'.
  static Py::Ref<Object> unpickle_function_;

  PyBoolArray(int length);
  ~PyBoolArray();

  void clear();
  bool get(int index) const;
  void set(int index, bool value);
  void checkIndex(int index) const;

  // The number of bits in the array.
  int length_;

  // The buffer containing the value bits.
  unsigned char* bits_;

  // The number of bytes allocated to store the bits.
  size_t getAllocation() const { return (length_ + 7) / 8; }

};


inline PyBoolArray*
PyBoolArray::New(int length)
{
  // Construct the Python object.
  PyBoolArray* result = Py::allocate<PyBoolArray>();
  // Perform C++ construction.
  try {
    new(result) PyBoolArray(length);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


inline bool
PyBoolArray::Check(PyObject* object)
{
  return ((Object*) object)->IsInstance(&type);
}


inline void
PyBoolArray::clear()
{
  // Zero the bits.
  memset(bits_, 0, getAllocation());
}


inline bool
PyBoolArray::get(int index) 
  const 
{ 
  return (bits_[index / 8] & (1 << (index % 8))) != 0;
}

inline void
PyBoolArray::set(int index, 
		 bool value)
{ 
  if (value)
    bits_[index / 8] |= (1 << (index % 8));
  else
    bits_[index / 8] &= ~(1 << (index % 8));
}


inline void
PyBoolArray::checkIndex(int index)
  const
{
  if (index < 0 || index >= length_)
    throw Py::Exception(PyExc_IndexError, "%d", index);
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYBOOLARRAY_HH__
