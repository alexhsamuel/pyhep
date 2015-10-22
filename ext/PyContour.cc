//----------------------------------------------------------------------
//
// PyContour.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension function for computing contour plots.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <vector>

#include "PyContour.hh"
#include "contour.hh"

using namespace Py;

//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

namespace {

struct Cookie
{
  Callable* function_;
  List* result_;
};


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

double
contour_fn(void* cookie_,
	   double x,
	   double y)
{
  Cookie* cookie = reinterpret_cast<Cookie*>(cookie_);
  Ref<Object> result = cookie->function_->CallFunction("dd", x, y);
  return result->FloatAsDouble();
}


void
contour_callback(void* cookie_,
		 double x0,
		 double y0,
		 double x1,
		 double y1)
{
  Cookie* cookie = reinterpret_cast<Cookie*>(cookie_);
  Ref<Object> coordinates = buildValue("dddd", x0, y0, x1, y1);
  cookie->result_->Append(coordinates);
}


}  // anonymous namespace


PyObject*
function_contours(Py::Object*, 
		  Py::Arg* args)
try {
  // Parse arguments.
  double x0, x1, y0, y1;
  long x_spacing, y_spacing;
  Object* function_arg;
  Object* levels_arg;
  args->ParseTuple("ddiddiOO", &x0, &x1, &x_spacing, &y0, &y1, 
		   &y_spacing, &function_arg, &levels_arg);
  Callable* function = cast<Callable>(function_arg);

  // Extract levels into a vector.
  Sequence* levels_seq = cast<Sequence>(levels_arg);
  std::vector<double> levels;
  for (int i = 0; i < levels_seq->Size(); ++i) {
    Ref<Object> item = levels_seq->GetItem(i);
    levels.push_back(item->FloatAsDouble());
  }

  // Construct a list to hold the results.
  Ref<List> result = List::New();
  // Build the cookie.
  Cookie cookie;
  cookie.function_ = function;
  cookie.result_ = result;
  // Find the contours.
  Contour contour(x0, x1, x_spacing, y0, y1, y_spacing, levels, 
		  contour_fn, contour_callback, &cookie);
  contour.compute();

  // All done.
  return result.release();
}
catch (Exception) {
  return NULL;
}
