//----------------------------------------------------------------------
// 
// contour.hh
//
// Adapted from newcntr.c by Michael Aramini,
// http://members.bellatlantic.net/~vze2vrva/
//
// Ref: http://members.bellatlantic.net/~vze2vrva/thesis.html
//
//----------------------------------------------------------------------

#ifndef __CONTOUR_HH__
#define __CONTOUR_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <vector>

//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

/* Computes contour (level) lines for a function of two variables.

A 'Contour' object approximates the contours at which 'function' is
equal to the constant values in 'levels'.  The contours are computed
over the range ('x0', 'y0', 'x1', 'y1'), with a sampling spacing
'x_spacing', 'y_spacing'.  

The result of the computation is a set of contours approximated by a
sequence of short line segments.  The object calls 'callback' for each
segment, passing 'cookie' and the coordinates of the endpoints of the
segment. 
*/

class Contour {
public:

  /* Type for the two-variable function whose contours are evaluated.  */
  typedef double (*Function)(void*, double, double);

  /* Type of the callback function for a line segment.  

  The arguments are a cookie value, and the endpoint coodinates x0, y0,
  x1, and y1.  */
  typedef void (*Callback)(void*, double, double, double, double);

  /* Set up the calculation.  */
  Contour(double x0, double x1, int x_spacing, 
	  double y0, double y1, int y_spacing,
	  const std::vector<double>& levels, 
	  Function function, Callback callback, void* cookie);

  /* Compute contour lines.  */
  void compute();

private:

  // types

  struct Cell 
  {
    double value_;
    short  left_len_;
    short  right_len_;
    short  top_len_;
    short  bot_len_;
  };

  // constants

  const static int X_RESOLUTION = 480;
  const static int Y_RESOLUTION = 480;

  // helper methods

  Cell& grid(int i, int j) { return *(grid_[i] + j); }
  void cntr1(int x1, int x2, int y1, int y2);
  void pass2(int x1, int x2, int y1, int y2);
  double function(int x, int y);
  void line(int, int, int, int);

  // data

  const double x0_;
  const double x1_;
  const int x_spacing_;
  const double y0_;
  const double y1_;
  const int y_spacing_;
  const std::vector<double>& levels_;
  const Function function_;
  const Callback callback_;
  void* const cookie_;

  const double x_scale_;
  const double x_offset_;
  const double y_scale_;
  const double y_offset_;

  Cell* grid_[Y_RESOLUTION + 1];

};
  

//----------------------------------------------------------------------
// methods
//----------------------------------------------------------------------

inline void
Contour::line(int a, 
	      int b,
	      int c,
	      int d)
{
  double x0 = x_offset_ + a * x_scale_;
  double y0 = y_offset_ + b * y_scale_;
  double x1 = x_offset_ + c * x_scale_;
  double y1 = y_offset_ + d * y_scale_;
  callback_(cookie_, x0, y0, x1, y1);
}


//----------------------------------------------------------------------

#endif  // #ifndef __CONTOUR_HH__
