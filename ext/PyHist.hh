//----------------------------------------------------------------------
// 
// PyHist.hh
//
// Copyright (C) 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Helper code for histogram extension class implementations.  */

#ifndef __PYHIST_HH__
#define __PYHIST_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <string>
#include <vector>

#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

/* A particular bin along a single binned axis.  */
typedef int 
BinNumber;

/* Values along a binned axis below the low end of the range.  */
const static int 
BINNUMBER_UNDERFLOW = -1;

/* Values along a binned axis above the high end of the range.  */
const static int 
BINNUMBER_OVERFLOW = -2;

/* 'None' values along a binned axis; for internal use only.  */
const static int
BINNUMBER_NONE = -3;

/* Models for errors on histogram bins.  */
typedef enum {
  ERROR_MODEL_ASYMMETRIC,
  ERROR_MODEL_GAUSSIAN,
  ERROR_MODEL_INVALID,
  ERROR_MODEL_NONE,
  ERROR_MODEL_POISSON,
  ERROR_MODEL_SYMMETRIC,
}
ErrorModel;


/* User-visible names for error models.  */
struct ErrorModelName{
  char* name_;
  ErrorModel model_;
};


extern struct ErrorModelName
error_model_names[];


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

struct BinnedAxis;
struct HistogramBins;

template<typename TYPE> 
std::pair<TYPE, TYPE> extractRange(Object* range_obj);

extern BinnedAxis* makeBinnedAxis(Object* axis);

/* Parse a name of an error model.  */
extern ErrorModel errorModelFromString(const char* name);

/* Return the name of an error model.  */
extern const char* errorModelAsString(ErrorModel model);

/* Factory for 'HistogramBins' instances.

   Return a new 'HistogramBins' instance suitable for storing
   'number_of_bins' bin values and errors of Python type 'type'.

   Raises 'NotImplementedError' if no 'HistogramBins' is available for
   this type.  
*/
extern HistogramBins* makeHistogramBins(
    Object* type, int number_of_bins, ErrorModel error_model);

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

/* Abstract base class for a binned axis

   A 'BinnedAxis' object maps coordinate values from a one-dimensional
   interval to a set of bins.

   Coordinate values are always specified as Python objects, so the user
   of this class need not be concerned with the actual type of
   coordinate values along the axis.
*/

class BinnedAxis
{
public:

  BinnedAxis(int number_of_bins) : number_of_bins_(number_of_bins) {}
  virtual ~BinnedAxis() {}

  /* Extract a bin number from a Python object.

     Return the bin number represented by Python object 'arg', which may
     be a (positive) integer, or the strings '"underflow"' or
     '"overflow"'. 
  */
  BinNumber parseBinNumber(Object* arg) const;

  /* Return the bin number cooresponding to 'coordinate'.  */
  virtual BinNumber map(Object* coordinate) const = 0;

  /* Return a Python pair containing the interval covered by a bin.  */
  virtual Object* getBinRange(BinNumber bin_number) const = 0;

  const int number_of_bins_;

};


inline BinNumber
BinnedAxis::parseBinNumber(Object* arg)
  const
{
  if (arg == None)
    return BINNUMBER_NONE;

  Ref<String> arg_str = arg->Str();
  if (strcmp(arg_str->AsString(), "underflow") == 0)
    return BINNUMBER_UNDERFLOW;
  else if (strcmp(arg_str->AsString(), "overflow") == 0)
    return BINNUMBER_OVERFLOW;

  long arg_val = arg->IntAsLong();
  if (arg_val < 0)
    throw Exception(PyExc_ValueError, "bin number must be positive");
  if (arg_val >= number_of_bins_)
    throw Exception(PyExc_ValueError, "bin number is too large");
  return arg_val;
}


//----------------------------------------------------------------------

/* 'BinnedAxis' implementation for numeric types.  */

template<typename TYPE>
class BinnedAxisGeneric
  : public BinnedAxis
{
public:

  /* Construct an evenly-binned axis.

     'number_of_bins' -- The number of bins along the axis.

     'range' -- The low and high values of the binned interval.  
  */
  BinnedAxisGeneric(int number_of_bins, Object* range);

  virtual ~BinnedAxisGeneric() {}

  virtual BinNumber map(Object* arg) const;
  virtual Object* getBinRange(BinNumber bin_number) const;

  std::pair<TYPE, TYPE> range_;

};


template<typename TYPE>
inline
BinnedAxisGeneric<TYPE>::BinnedAxisGeneric(int number_of_bins,
					   Object* range)
  : BinnedAxis(number_of_bins),
    range_(extractRange<TYPE>(range))
{
}


template<typename TYPE>
inline BinNumber
BinnedAxisGeneric<TYPE>::map(Object* arg)
  const
{
  TYPE lo = range_.first;
  TYPE hi = range_.second;
  TYPE coordinate = PythonType<TYPE>::fromPyObject(arg);
  if (coordinate < lo)
    return BINNUMBER_UNDERFLOW;
  else if (coordinate >= hi)
    return BINNUMBER_OVERFLOW;
  else
    return int(double(coordinate - lo) * number_of_bins_ / (hi - lo));
}


template<>
inline BinNumber
BinnedAxisGeneric<double>::map(Object* arg)
  const
{
  double coordinate = PythonType<double>::fromPyObject(arg);

  // Check for abnormal values.
  if (std::isinf(coordinate)) {
    std::cerr << "warning: infinite coordinate value " 
	      << coordinate << " in histogram\n";
    return BINNUMBER_OVERFLOW;
  }
  if (std::isnan(coordinate)) {
    std::cerr << "warning: NaN coordinate value in histogram\n";
    return BINNUMBER_UNDERFLOW;
  }

  double lo = range_.first;
  double hi = range_.second;
  if (coordinate < lo)
    return BINNUMBER_UNDERFLOW;
  else if (coordinate >= hi)
    return BINNUMBER_OVERFLOW;
  else
    return int((coordinate - lo) * number_of_bins_ / (hi - lo));
}


template<typename TYPE>
inline Object*
BinnedAxisGeneric<TYPE>::getBinRange(BinNumber bin_number)
  const
{
  TYPE lo = range_.first;
  TYPE hi = range_.second;
  Ref<Object> lo_obj;
  Ref<Object> hi_obj;
  if (bin_number == BINNUMBER_UNDERFLOW) {
    lo_obj = newRef(None);
    hi_obj = PythonType<TYPE>::asPyObject(lo);
  }
  else if (bin_number == BINNUMBER_OVERFLOW) {
    lo_obj = PythonType<TYPE>::asPyObject(hi);
    hi_obj = newRef(None);
  }
  else if (bin_number >= 0 && bin_number < number_of_bins_) {
    lo_obj = PythonType<TYPE>::asPyObject
      (lo + bin_number * (hi - lo) / number_of_bins_);
    hi_obj = PythonType<TYPE>::asPyObject
      (lo + (bin_number + 1) * (hi - lo) / number_of_bins_);
  }
  else if (bin_number == BINNUMBER_NONE) 
    throw Exception(PyExc_ValueError, "no 'None' bin");
  else
    abort();
  
  return Tuple::New(2, (Object*) lo_obj, (Object*) hi_obj);
}


//----------------------------------------------------------------------

/* 'BinnedAxis' implementation for numeric types.  */

template<typename TYPE>
class UnevenlyBinnedAxisGeneric
  : public BinnedAxis
{
public:

  /* Construct an unevenly-binned axis.

     'bin_edges' -- The positions of the bin edges.  
  */
  UnevenlyBinnedAxisGeneric(Sequence* bin_edges);

  virtual ~UnevenlyBinnedAxisGeneric() {}

  virtual BinNumber map(Object* arg) const;
  virtual Object* getBinRange(BinNumber bin_number) const;

  std::vector<TYPE> bin_edges_;

};


template<typename TYPE>
inline
UnevenlyBinnedAxisGeneric<TYPE>::UnevenlyBinnedAxisGeneric(Sequence* bin_edges)
  : BinnedAxis(bin_edges->Size() - 1)
{
  int num_edges = bin_edges->Size();
  assert(num_edges >= 2);
  for (int i = 0; i < num_edges; ++i) {
    Ref<Object> edge = bin_edges->GetItem(i);
    bin_edges_.push_back(PythonType<TYPE>::fromPyObject(edge));
  }
}


template<typename TYPE>
inline BinNumber
UnevenlyBinnedAxisGeneric<TYPE>::map(Object* arg)
  const
{
  TYPE coordinate = PythonType<TYPE>::fromPyObject(arg);

  // Is it lower than the first bin edge?
  if (coordinate < bin_edges_[0])
    return BINNUMBER_UNDERFLOW;

  // Is it higher than the last bin edge?
  else if (coordinate >= bin_edges_[number_of_bins_])
    return BINNUMBER_OVERFLOW;

  else {
    // Perform binary search to find the right bin.
    int i0 = 0;
    int i2 = number_of_bins_;
    while (i2 > i0 + 1) {
      int i1 = (i0 + i2) / 2;
      if (coordinate < bin_edges_[i1])
	i2 = i1;
      else
	i0 = i1;
    }
    return i2 - 1;
  } 
}


template<typename TYPE>
inline Object*
UnevenlyBinnedAxisGeneric<TYPE>::getBinRange(BinNumber bin_number)
  const
{
  Ref<Object> lo_obj;
  Ref<Object> hi_obj;
  if (bin_number == BINNUMBER_UNDERFLOW) {
    lo_obj = newRef(None);
    hi_obj = PythonType<TYPE>::asPyObject(bin_edges_[0]);
  }
  else if (bin_number == BINNUMBER_OVERFLOW) {
    lo_obj = PythonType<TYPE>::asPyObject(bin_edges_[number_of_bins_ + 1]);
    hi_obj = newRef(None);
  }
  else if (bin_number >= 0 && bin_number < number_of_bins_) {
    lo_obj = PythonType<TYPE>::asPyObject(bin_edges_[bin_number]);
    hi_obj = PythonType<TYPE>::asPyObject(bin_edges_[bin_number + 1]);
  }
  else if (bin_number == BINNUMBER_NONE) 
    throw Exception(PyExc_ValueError, "no 'None' bin");
  else
    abort();
  
  return Tuple::New(2, (Object*) lo_obj, (Object*) hi_obj);
}


//----------------------------------------------------------------------

/* Abstract base for container for histogram bins.

   A 'HistogramBins' object stores bin contents and bin errors for a
   histogram.  The histogram may be of any shape; the bins are assumed
   to be independent, so only the number of bins is relevant.  Bins are
   specified by an 'unsigned' bin index.

   The contents of and errors on bins are specified and returned only as
   Python objects, so the user of this class needn't know the type of
   the bin contents.  Conversion to/from Python objects is handled by
   this class.
*/

class HistogramBins
{
public:

  HistogramBins(unsigned number_of_bins, ErrorModel error_model) 
    : num_bins_(number_of_bins), error_model_(error_model) {}
  virtual ~HistogramBins() {}

  ErrorModel getErrorModel() const { return error_model_; }

  /* Accumulate 'weight' to bin 'bin_index'.

     Add 'weight' to the bin, and update the bin error accordingly.  If
     'weight' is NULL, it is taken to be unity.
  */
  virtual void accumulate(unsigned bin_index, Object* weight) = 0;

  virtual Object* getBinContent(unsigned bin_index) = 0;
  virtual void setBinContent(unsigned bin_index, Object* value) = 0;
  virtual Object* getBinError(unsigned bin_index) = 0;
  virtual void setBinError(unsigned bin_index, Object* value) = 0;

protected:

  const unsigned num_bins_;
  const ErrorModel error_model_;

};


//----------------------------------------------------------------------

/* 'HistogramBins' implementation for numeric types. 

   Bin errors are computed as square root of sum-of-squares of
   accumulated bin contents.  
*/

template<typename TYPE>
class HistogramBinsGeneric
  : public HistogramBins
{
public:

  HistogramBinsGeneric(int number_of_bins_, ErrorModel error_model);
  virtual ~HistogramBinsGeneric();

  virtual void accumulate(unsigned bin_index, Object* weight_arg);
  virtual Object* getBinContent(unsigned bin_index);
  virtual void setBinContent(unsigned bin_index, Object* value_arg);
  virtual Object* getBinError(unsigned bin_index);
  virtual void setBinError(unsigned bin_index, Object* value);

protected:

  TYPE* bins_;
  double* lo_errors_;
  double* hi_errors_;

};


template<typename TYPE>
HistogramBinsGeneric<TYPE>::HistogramBinsGeneric(int number_of_bins,
						 ErrorModel error_model)
  : HistogramBins(number_of_bins, error_model)
{
  // Allocate the bin arrays.
  bins_ = new TYPE[number_of_bins];
  // Zero them.
  for (int i = 0; i < number_of_bins; ++i) 
    bins_[i] = TYPE(0);

  // Allocate arrays for errors, if they are not computed.
  if (error_model == ERROR_MODEL_ASYMMETRIC) {
    lo_errors_ = new double[number_of_bins];
    hi_errors_ = new double[number_of_bins];
    for (int i = 0; i < number_of_bins; ++i)
      lo_errors_[i] = hi_errors_[i] = 0.0;
  }
  else if (error_model == ERROR_MODEL_SYMMETRIC) {
    lo_errors_ = new double[number_of_bins];
    for (int i = 0; i < number_of_bins; ++i) 
      lo_errors_[i] = 0.0;
  }
}


template<typename TYPE>
HistogramBinsGeneric<TYPE>::~HistogramBinsGeneric()
{
  delete[] bins_;

  switch (error_model_) {
  case ERROR_MODEL_ASYMMETRIC:
    delete[] lo_errors_;
    delete[] hi_errors_;
    break;

  case ERROR_MODEL_SYMMETRIC:
    delete[] lo_errors_;
    break;

  default:
    break;
  }
}


template<typename TYPE>
void
HistogramBinsGeneric<TYPE>::accumulate(unsigned bin_index,
				       Object* weight_arg)
{
  assert(bin_index < num_bins_);
  // Extract the weight.  Assume unit weight if none was specified.
  TYPE weight = 
    (weight_arg == NULL) 
    ? TYPE(1) 
    : PythonType<TYPE>::fromPyObject(weight_arg);
  // Update bin contents.
  bins_[bin_index] += weight;
  // Update the errors, if necessary.
  switch (error_model_) {
  case ERROR_MODEL_SYMMETRIC:
    lo_errors_[bin_index] += weight * weight;
    break;
  case ERROR_MODEL_ASYMMETRIC:
    lo_errors_[bin_index] += weight * weight;
    hi_errors_[bin_index] += weight * weight;
    break;
  default:
    break;
  }
}


template<typename TYPE>
Object* 
HistogramBinsGeneric<TYPE>::getBinContent(unsigned bin_index)
{
  assert(bin_index < num_bins_);
  return PythonType<TYPE>::asPyObject(bins_[bin_index]);
}


template<typename TYPE>
void 
HistogramBinsGeneric<TYPE>::setBinContent(unsigned bin_index, 
					  Object* value_arg)
{
  assert(bin_index < num_bins_);
  bins_[bin_index] = PythonType<TYPE>::fromPyObject(value_arg);
}


template<typename TYPE>
Object*
HistogramBinsGeneric<TYPE>::getBinError(unsigned bin_index)
{
  assert(bin_index < num_bins_);

  double lo;
  double hi;
  switch (error_model_) {
  case ERROR_MODEL_NONE:
    lo = 0.0;
    hi = 0.0;
    break;

  case ERROR_MODEL_GAUSSIAN:
    lo = sqrt(fabs((double) bins_[bin_index]));
    hi = lo;
    break;

  case ERROR_MODEL_POISSON: {
    std::pair<double, double> errors = 
      getPoissonErrors(int(std::abs(bins_[bin_index])));
    lo = errors.first;
    hi = errors.second;
    break;
  }

  case ERROR_MODEL_ASYMMETRIC:
    lo = sqrt(lo_errors_[bin_index]);
    hi = sqrt(hi_errors_[bin_index]);
    break;

  case ERROR_MODEL_SYMMETRIC:
    lo = sqrt(lo_errors_[bin_index]);
    hi = lo;
    break;

  default:
    abort();
  }

  return buildValue("(dd)", lo, hi);
}

      
template<typename TYPE>
void 
HistogramBinsGeneric<TYPE>::setBinError(unsigned bin_index, 
					Object* value_arg)
{
  assert(bin_index < num_bins_);

  switch (error_model_) {
  case ERROR_MODEL_NONE:
  case ERROR_MODEL_GAUSSIAN:
  case ERROR_MODEL_POISSON:
    throw Exception(PyExc_RuntimeError, 
		    "cannot set error with error model '%s'",
		    errorModelAsString(error_model_));

  case ERROR_MODEL_SYMMETRIC:
  case ERROR_MODEL_ASYMMETRIC:
    {
      double lo;
      double hi;

      if (Sequence::Check(value_arg)) {
	// Extract the '(lo, hi)' pair of error values.
	Sequence* pair = cast<Sequence>(value_arg);
	if (pair->Size() != 2)
	  throw Exception
	    (PyExc_TypeError, "error must be a '(lo, hi)' pair");
	Ref<Object> first = pair->GetItem(0);
	lo = fabs(first->FloatAsDouble());
	Ref<Object> second = pair->GetItem(1);
	hi = fabs(second->FloatAsDouble());
      }
      else {
	// Treat the argument as a number and use it for both errors.
	lo = fabs(value_arg->FloatAsDouble());
	hi = lo;
      }

      // Set them.
      if (error_model_ == ERROR_MODEL_ASYMMETRIC) {
	lo_errors_[bin_index] = lo * lo;
	hi_errors_[bin_index] = hi * hi;
      }
      else {
	double error = std::max(lo, hi);
	lo_errors_[bin_index] = error * error;
      }
    }
    break;

  default:
    abort();
  }
}


//----------------------------------------------------------------------
// inline functions
//----------------------------------------------------------------------

template<typename TYPE>
std::pair<TYPE, TYPE>
extractRange(Object* range_obj) 
{
  Ref<Object> lo;
  Ref<Object> hi;
  Sequence* range = cast<Sequence>(range_obj);
  range->split(lo, hi);
  return std::pair<TYPE, TYPE>(PythonType<TYPE>::fromPyObject(lo),
			       PythonType<TYPE>::fromPyObject(hi));
}


inline Object*
makeBinNumberObject(BinNumber bin_number)
{
  if (bin_number == BINNUMBER_UNDERFLOW)
    return String::FromString("underflow");
  else if (bin_number == BINNUMBER_OVERFLOW)
    return String::FromString("overflow");
  else if (bin_number >= 0)
    return Int::FromLong(bin_number);
  else
    abort();
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYHIST_HH__
