//----------------------------------------------------------------------
//
// PyHistogram2D.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Extension classes for two-dimensional histogams.  */

#ifndef __PYHISTOGRAM2D_HH__
#define __PYHISTOGRAM2D_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "python.hh"

//----------------------------------------------------------------------
// Python type
//----------------------------------------------------------------------

struct PyHistogram2D
  : public Py::Object
{
  // Python type support  ----------------------------------------------
  
  static PyTypeObject type;
  static PyHistogram2D* New(Py::Object*, Py::Object*, Py::Object*, 
			    ErrorModel);
  static bool Check(PyObject* object);

  // Types  ------------------------------------------------------------

  struct BinNumbers
  {
    BinNumbers(BinNumber x, BinNumber y) : x_(x), y_(y) {}
    BinNumber x_;
    BinNumber y_;
  };

  // Methods  ----------------------------------------------------------

  PyHistogram2D(Py::Object*, Py::Object*, Py::Object*, ErrorModel);
  ~PyHistogram2D();

  /* Get the bin index for the numbered bin.  */
  unsigned mapNumbers(BinNumbers bin_numbers);

  /* Get bin numbers for coordinates as a Python pair.  */
  BinNumbers mapCoordinates(Py::Object* arg);

  /* Get the bin numbers from a Python argument.  */
  BinNumbers parseBinNumbers(Py::Object* arg);
  
  // Data  -------------------------------------------------------------

  /* A sequence of the two axis objects describing the axes.  */
  Py::Ref<Py::Sequence> axes_;

  /* The axis objects we use ourselves for converting coordinates.  */
  std::auto_ptr<BinnedAxis> x_axis_;
  std::auto_ptr<BinnedAxis> y_axis_;

  /* The Python type for bin contents and errors.  */
  Py::Ref<Py::Object> bin_type_;

  /* Bin contents.  */
  std::auto_ptr<HistogramBins> bins_;

  /* Number of accumulations.  */
  int number_of_samples_;

  /* Dictionary for user-defined attributes.  */
  Py::Ref<Py::Dict> dict_;

};


//----------------------------------------------------------------------
// inline method definitions
//----------------------------------------------------------------------

inline PyHistogram2D*
PyHistogram2D::New(Py::Object* x_axis,
		   Py::Object* y_axis,
		   Py::Object* bin_type,
		   ErrorModel error_model)
{
  // Construct the Python object.
  PyHistogram2D* result = Py::allocate<PyHistogram2D>();
  // Perform C++ initialization.
  try {
    new(result) PyHistogram2D(x_axis, y_axis, bin_type, error_model);
  }
  catch (Py::Exception) {
    // If the constructor raised an exception, the object wasn't fully
    // constructed, so don't call the destructor.  Simply deallocate
    // memory. 
    Py::deallocate(result);
    throw;
  }
  // All done.
  return result;
}


inline bool
PyHistogram2D::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYHISTOGRAM2D_HH__
