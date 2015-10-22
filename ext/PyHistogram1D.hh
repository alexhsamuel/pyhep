//----------------------------------------------------------------------
//
// PyHistogram1D.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Extension classes for one-dimensional histograms.  */

#ifndef __PYHISTOGRAM1D_HH__
#define __PYHISTOGRAM1D_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <memory>

#include "PyHist.hh"
#include "python.hh"

//----------------------------------------------------------------------
// Python type
//----------------------------------------------------------------------

class PyHistogram1D
  : public Py::Object
{
public:

  // Python type support  ----------------------------------------------

  static PyTypeObject type;
  static PyHistogram1D* New(Py::Object*, Py::Object*, 
			    ErrorModel error_model);
  static bool Check(PyObject* object);

  // Methods  ----------------------------------------------------------

  PyHistogram1D(Py::Object* axis, Py::Object* bin_type, 
		ErrorModel error_model);
  ~PyHistogram1D();

  /* Get the bin index for the numbered bin.  */
  unsigned mapNumber(BinNumber bin_number);

  /* Get bin numbers for coordinates as a Python pair.  */
  BinNumber mapCoordinate(Py::Object* arg);

  /* Get the bin numbers from a Python argument.  */
  BinNumber parseBinNumber(Py::Object* arg);
  
  // Data  -------------------------------------------------------------

  /* The Python axis object.  */
  Py::Ref<Py::Object> axis_obj_;

  /* A one-element sequence of the Python axis object describing the axis.  */
  Py::Ref<Sequence> axes_;

  /* The axis objects we use ourselves for converting coordinates.  */
  std::auto_ptr<BinnedAxis> axis_;

  /* The Python type used to store bin contents.  */
  Py::Ref<Py::Object> bin_type_;

  /* Bin contents.  */
  std::auto_ptr<HistogramBins> bins_;

  /* Number of accumulations.  */
  int number_of_samples_;

  /* Dictionary for additional attributes.  */
  Py::Ref<Py::Dict> dict_;

};


//----------------------------------------------------------------------
// inline methods
//----------------------------------------------------------------------

inline PyHistogram1D*
PyHistogram1D::New(Py::Object* axis,
		   Py::Object* bin_type, 
		   ErrorModel error_model)
{
  // Construct the Python object.
  PyHistogram1D* result = Py::allocate<PyHistogram1D>();
  // Perform C++ initialization.
  try {
    new(result) PyHistogram1D(axis, bin_type, error_model);
  }
  catch (Exception) {
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
PyHistogram1D::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYHISTOGRAM1D_HH__
