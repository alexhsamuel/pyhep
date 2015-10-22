//----------------------------------------------------------------------
//
// util.cc
//
// Copyright (C) 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Utility functions, classes, and wrappers involving CERNLIB calls.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <pthread.h>

#include "cernlib.hh"
#include "python.hh"
#include "util.hh"

using namespace Py;

//----------------------------------------------------------------------
// helper types
//----------------------------------------------------------------------

namespace {

struct DgaussContext 
{
  Callable* function_;
  String* var_name_;
  bool exception_raised_;
  Ref<Dict> kw_args_;
};


pthread_mutex_t 
dgauss_lock = PTHREAD_MUTEX_INITIALIZER;


DgaussContext*
dgauss_context = NULL;


//----------------------------------------------------------------------

struct DadmulContext
{
  Callable* function_;
  const std::vector<IntegrationRange>* region_;
  bool exception_raised_;
  Ref<Dict> kw_args_;
};


pthread_mutex_t
dadmul_lock = PTHREAD_MUTEX_INITIALIZER;


DadmulContext*
dadmul_context = NULL;


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

double
dgauss_callback(const double* arg)
{
  assert(dgauss_context != NULL);
  DgaussContext* context = dgauss_context;

  // If an exception was already raised during this integration, don't
  // evaluate the expression any more.
  if (context->exception_raised_)
    return 0;

  try {
    // Set up the dictionary for keyword arguments.
    Ref<Float> x = Float::FromDouble(*arg);
    context->kw_args_->SetItem(context->var_name_, x);
    // Evaluate the integrand.
    // FIXME: Optimize for PyExpr.
    Ref<Object> result = 
      context->function_->Call(NULL, context->kw_args_);
    // Return the result.
    return result->FloatAsDouble();
  }
  catch (Exception) {
    // Flag that a Python exception has been raised.  Leave the Python
    // exception state alone.
    context->exception_raised_ = true;
    return 0;
  }
}


double
dadmul_callback(const int* num_args,
		const double* args)
{
  assert(dadmul_context != NULL);
  DadmulContext* context = dadmul_context;

  // If an exception was already raised during this integration, don't
  // evaluate the expression any more.
  if (context->exception_raised_)
    return 0;

  try {
    // Add variable values to keyword arguments dictionary.
    assert(*num_args == (int) context->region_->size());
    for (int i = 0; i < *num_args; ++i) {
      Ref<Float> value = Float::FromDouble(args[i]);
      String* var_name = (*context->region_)[i].variable_name_;
      context->kw_args_->SetItem(var_name, value);
    }
    // Evaluate the integrand.
    // FIXME: Optimize for PyExpr.
    Ref<Object> result = context->function_->Call(NULL, context->kw_args_);
    // Return the result.
    return result->FloatAsDouble();
  }
  catch (Exception) {
    // Flag that a Python exception has been raised.  Leave the Python
    // exception state alone.
    context->exception_raised_ = true;
    return 0;
  }
}


}  // anonymous namespace


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

double
dgauss(Callable* function,
       String* variable_name,
       double lo,
       double hi,
       double accuracy)
{
  DgaussContext context;
  context.function_ = function;
  context.var_name_ = variable_name;
  context.exception_raised_ = false;
  context.kw_args_ = Dict::New();

  // Serialize use of the 'dgauss' routine.  We don't know that it's
  // thread-safe.
  pthread_mutex_lock(&dgauss_lock);
  assert(dgauss_context == NULL);
  // This variable is used to communicate with the integrand callback
  // function.
  dgauss_context = &context;
  double result = dgauss_(dgauss_callback, &lo, &hi, &accuracy);
  dgauss_context = NULL;
  // Done with 'dgauss'.
  pthread_mutex_unlock(&dgauss_lock);

  // Was a Python exception raised during integration?
  if (context.exception_raised_)
    // Yes.  The exception state should be set.  Go with it.
    throw Exception();

  return result;
}


namespace {

double
dadmul(Callable* function,
       const std::vector<IntegrationRange>& region,
       double accuracy=1e-6)
{
  // The 'DADMUL' call works for integration between 2 and 15
  // dimensions. 
  int num_vars = region.size();
  if (num_vars < 2 || num_vars > 15)
    throw Exception(PyExc_ValueError, 
		    "only integration in 2 to 15 dimensions supported");

  // Construct a context structure for communicating with the callback
  // function. 
  DadmulContext context;
  context.function_ = function;
  context.region_ = &region;
  context.exception_raised_ = false;
  context.kw_args_ = Dict::New();
  // Build arrays of lower and upper bounds of the integration ranges.
  double lo[num_vars];
  double hi[num_vars];
  for (int i = 0; i < num_vars; ++i) {
    lo[i] = region[i].lo_;
    hi[i] = region[i].hi_;
  }
  // Set up a working buffer for 'DADMUL' and limit the number of
  // integrations of the integrand.
  int problem_size = (1 << num_vars) + 2 * num_vars * (num_vars + 1) + 1;
  int min_evaluations = 0;
  int max_evaluations = 5000000;
  int work_buffer_size = 
    (2 * num_vars + 3) * (1 + max_evaluations / problem_size) / 2;
  double work_buffer[work_buffer_size];

  // Serialize use of the 'dadmul' routine.  We don't know that it's
  // thread-safe.
  pthread_mutex_lock(&dadmul_lock);
  assert(dadmul_context == NULL);
  // This variable is used to communicate with the integrand callback
  // function.
  dadmul_context = &context;
  double result;
  double relative_error;
  int num_evaluations;
  int result_code;
  dadmul_(dadmul_callback, &num_vars, lo, hi, &min_evaluations, 
	  &max_evaluations, &accuracy, work_buffer, &work_buffer_size, 
	  &result, &relative_error, &num_evaluations, &result_code);
  dadmul_context = NULL;
  // Done with 'dadmul'.
  pthread_mutex_unlock(&dadmul_lock);

  // Was a Python exception raised during integration?
  if (context.exception_raised_)
    // Yes.  The exception state should be set.  Go with it.
    throw Exception();

  // Interpret the result code.
  switch (result_code) {
  case 0:
    // Succeeded
    break;
  case 1:
    // The specified value of 'max_evaluations' was too small to achieve
    // the target 'relative_error'.
    Warn(PyExc_RuntimeWarning,
	 "multiple integraton with DADMUL only achieved error %e",
	 relative_error);
    break;
  case 2:
    // The work buffer was too small.  This shouldn't happen.
    abort();
  case 3:
    // Parameter error.  
    abort();
  default:
    // Unknown result code.
    abort();
  }

  return result;
}


}  // anonymous namespace


double
integrate(Callable* function,
	  const std::vector<IntegrationRange>& region,
	  double accuracy)
{
  if (region.size() == 0)
    throw Exception(PyExc_ValueError, "empty integration range");

  else if (region.size() == 1) {
    const IntegrationRange& range = region[0];
    return dgauss(function, range.variable_name_, range.lo_, range.hi_, 
		  accuracy);
  }

  else if (region.size() <= 15) 
    return dadmul(function, region, accuracy);

  else 
    throw Exception(PyExc_NotImplementedError, 
		    "integrals with more than 15 dimensions");
}
	  

