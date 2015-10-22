//----------------------------------------------------------------------
//
// util.hh
//
// Copyright (C) 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Utility functions, classes, and wrappers involving CERNLIB calls.  */

#ifndef __UTIL_HH__
#define __UTIL_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <vector>

#include "python.hh"

//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

/* Range of integration over one variable.  */

struct IntegrationRange
{
  IntegrationRange(Py::String* variable_name, double lo, double hi)
    : variable_name_(variable_name), lo_(lo), hi_(hi) {}

  /* The name of the variable to integrate over.  */
  Py::String* variable_name_;

  /* Low and high limits of the integration range.  */
  double lo_;
  double hi_;
};


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern double dgauss(Py::Callable* function, Py::String* variable_name,
		     double lo, double hi, double accuracy);

/* Perform integration over a rectangular region.

   Integrates 'fn' over a rectangular 'region', using the appropriate
   CERNLIB call.  This function can integrate over at most 15
   dimensions. 

   'fn' -- A callable or expression object.
*/
extern double integrate(Py::Callable* fn, 
			const std::vector<IntegrationRange>& region,
			double accuracy=1e-8);


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

template<typename TYPE>
inline TYPE
sqr(TYPE value)
{
  return value * value;
}

//----------------------------------------------------------------------

#endif  // #ifndef __UTIL_HH__
