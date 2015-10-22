//----------------------------------------------------------------------
// 
// PyHist.hh
//
// Copyright (C) 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Helper code for histogram extension class implementations.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "PyHist.hh"

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

ErrorModelName
error_model_names[] = {
  { "none",       ERROR_MODEL_NONE },
  { "gaussian",   ERROR_MODEL_GAUSSIAN },
  { "poisson",    ERROR_MODEL_POISSON },
  { "symmetric",  ERROR_MODEL_SYMMETRIC },
  { "asymmetric", ERROR_MODEL_ASYMMETRIC },
  { NULL,         ERROR_MODEL_INVALID }
};


//----------------------------------------------------------------------
// functions
//----------------------------------------------------------------------

/* Return a new binned axis object for a Python 'Axis' object.  */

BinnedAxis*
makeBinnedAxis(Object* axis)
{
  Ref<Object> type = axis->GetAttrString("type");
  
  Ref<Object> EvenlyBinnedAxis_class = 
    import("hep.hist.axis", "EvenlyBinnedAxis");
  Ref<Object> UnevenlyBinnedAxis_class = 
    import("hep.hist.axis", "UnevenlyBinnedAxis");

  // Is it an evenly-binned axis?
  if (axis->IsInstance(EvenlyBinnedAxis_class)) {
    Ref<Object> range = axis->GetAttrString("range");
    Ref<Object> num_bins_obj = axis->GetAttrString("number_of_bins");
    int num_bins = (int) num_bins_obj->IntAsLong();

    // We know how to handle floats and ints.
    if (type->Compare((PyObject*) &PyFloat_Type)) 
      return new BinnedAxisGeneric<double>(num_bins, range);
    else if (type->Compare((PyObject*) &PyInt_Type)) 
      return new BinnedAxisGeneric<long>(num_bins, range);
    else {
      // Don't know how to handle this Python type.
      Ref<String> type_str = type->Str();
      throw Exception(PyExc_NotImplementedError, 
		      "axis type %s not supported", 
		      type_str->AsString());
    }
  }

  // Is it an unevenly-binned axis?
  else if (axis->IsInstance(UnevenlyBinnedAxis_class)) {
    Ref<Object> bin_edges_obj = axis->GetAttrString("bin_edges");
    Sequence* bin_edges = cast<Sequence>(bin_edges_obj);

    // We know how to handle floats and ints.
    if (type->Compare((PyObject*) &PyFloat_Type))
      return new UnevenlyBinnedAxisGeneric<double>(bin_edges);
    else if (type->Compare((PyObject*) &PyInt_Type))
      return new UnevenlyBinnedAxisGeneric<long>(bin_edges);
    else {
      // Don't know how to handle this Python type.
      Ref<String> type_str = type->Str();
      throw Exception(PyExc_NotImplementedError,
		      "unevenly binned axis type %s not supported",
		      type_str->AsString());
    }
  }
  
  // We don't know how to handle other types of axes.
  else 
    throw Exception(PyExc_NotImplementedError, 
		    "axis class not supported");
}


HistogramBins*
makeHistogramBins(Object* type,
		  int number_of_bins,
		  ErrorModel error_model)
{
  if (type->Compare((PyObject*) &PyFloat_Type))
    return new HistogramBinsGeneric<double>(number_of_bins, error_model);
  else if (type->Compare((PyObject*) &PyInt_Type))
    return new HistogramBinsGeneric<long>(number_of_bins, error_model);
  else {
    // Don't know how to handle this Python type.
    Ref<String> type_str = type->Str();
    throw Exception(PyExc_NotImplementedError,
		    "bin type %s not supported", type_str->AsString());
  }
}


ErrorModel
errorModelFromString(const char* name)
{
  for (ErrorModelName* record = error_model_names;
       record->name_ != NULL;
       ++record)
    if (strcmp(name, record->name_) == 0)
      return record->model_;

  return ERROR_MODEL_INVALID;
}


const char*
errorModelAsString(ErrorModel model)
{
  for (ErrorModelName* record = error_model_names;
       record->name_ != NULL;
       ++record)
    if (record->model_ == model)
      return record->name_;

  return NULL;
}
