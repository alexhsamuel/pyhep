//----------------------------------------------------------------------
// 
// contour.cc
//
// Adapted from newcntr.c by Michael Aramini,
// http://members.bellatlantic.net/~vze2vrva/
//
// Ref: http://members.bellatlantic.net/~vze2vrva/thesis.html
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cmath>
#include <cstdlib>
#include <cstdio>

#include "contour.hh"

//----------------------------------------------------------------------
// methods
//----------------------------------------------------------------------

Contour::Contour(double x0, 
		 double x1,
		 int x_spacing,
		 double y0,
		 double y1,
		 int y_spacing,
		 const std::vector<double>& levels,
		 Function function,
		 Callback callback,
		 void* cookie)
  : x0_(x0),
    x1_(x1),
    x_spacing_(x_spacing),
    y0_(y0),
    y1_(y1),
    y_spacing_(y_spacing),
    levels_(levels),
    function_(function),
    callback_(callback),
    cookie_(cookie),
    x_scale_((x1_ - x0_) / X_RESOLUTION),
    x_offset_(x0_),
    y_scale_((y1_ - y0_) / Y_RESOLUTION),
    y_offset_(y0_)
{
}


double 
Contour::function(int x,   
		  int y)
{
  // Is it already in the array?
  if (grid(x, y).top_len_ == -1) {  
    // Not in the array; create new array element.
    grid(x, y).top_len_ = 0;
    grid(x, y).bot_len_ = 0;
    grid(x, y).right_len_ = 0;
    grid(x, y).left_len_ = 0;
    double x1 = x_offset_ + x_scale_ * x;
    double y1 = y_offset_ + y_scale_ * y;
    grid(x, y).value_ = function_(cookie_, x1, y1);
  }

  return grid(x, y).value_;
}


void
Contour::compute()
{
  int xlow = 0;
  int oldx3 = 0;
  int x3 = Y_RESOLUTION / x_spacing_;
  int x4 = (2 * Y_RESOLUTION) / x_spacing_;
  for (int x = oldx3; x <= x4; x++) {
    // Allocate new columns needed.
    if (x >= Y_RESOLUTION + 1)
      break;
    grid_[x] = (Cell*) calloc(X_RESOLUTION + 1, sizeof(Cell));
    for (int y = 0; y <= X_RESOLUTION; y++)
      grid(x, y).top_len_ = -1;
  }
  int y3;
  int y4 = 0;
  for (int j = 0; j < y_spacing_; j++) {
    y3 = y4;
    y4 = ((j + 1) * X_RESOLUTION) / y_spacing_;
    cntr1(oldx3, x3, y3, y4);
  }
  for (int i = 1; i < x_spacing_; i++) {
    y4 = 0;
    for (int j = 0; j < y_spacing_; j++) {
      y3 = y4;
      y4 = ((j + 1) * X_RESOLUTION) / y_spacing_;
      cntr1(x3, x4, y3, y4);
    }
    y4 = 0;
    for (int j = 0; j < y_spacing_; j++) {
      y3 = y4;
      y4 = ((j + 1) * X_RESOLUTION) / y_spacing_;
      pass2(oldx3, x3, y3, y4);
    }
    if (i < x_spacing_ - 1) {    
      // Re-use columns no longer needed.
      oldx3 = x3;
      x3 = x4;
      x4 = ((i + 2) * Y_RESOLUTION) / x_spacing_;
      for (int x = x3 + 1; x <= x4; x++) {
        if (xlow < oldx3) {
          grid_[x] = grid_[xlow];
          grid_[xlow++] = NULL;
        }
        else {
          grid_[x] = (Cell*) calloc(X_RESOLUTION + 1, sizeof(Cell));
        }
        for (int y = 0; y <= X_RESOLUTION; y++)
          grid(x, y).top_len_ = -1;
      }
    }
  }
  y4 = 0;
  for (int j = 0; j < y_spacing_; j++) {
    y3 = y4;
    y4 = ((j + 1) * X_RESOLUTION) / y_spacing_;
    pass2(x3, x4, y3, y4);
  }
  // Clean up rest of dynamically allocated memory.
  for (int x = xlow; x <= Y_RESOLUTION; x++)
    free(grid_[x]);
}


void 
Contour::cntr1(int x1,
	       int x2,
	       int y1,
	       int y2)
{
  // If not a real cell, punt.
  if ((x1 == x2) || (y1 == y2))   
    return;

  double f11 = function(x1, y1);
  double f12 = function(x1, y2);
  double f21 = function(x2, y1);
  double f22 = function(x2, y2);
  // Is the cell divisible?
  if ((x2 > x1 + 1) || (y2 > y1 + 1)) {   
    int x3 = (x1 + x2) / 2;
    int y3 = (y1 + y2) / 2;
    double f33 = function(x3, y3);
    unsigned i = 0;
    unsigned j = 0;
    if (f33 < f11)
      i++;
    else if (f33 > f11)
      j++;
    if (f33 < f12)
      i++;
    else if (f33 > f12)
      j++;
    if (f33 < f21)
      i++;
    else if (f33 > f21)
      j++;
    if (f33 < f22)
      i++;
    else if (f33 > f22)
      j++;
    // Should we divide the cell?
    if ((i > 2) || (j > 2)) {   
      // Yes.
      cntr1(x1, x3, y1, y3);
      cntr1(x3, x2, y1, y3);
      cntr1(x1, x3, y3, y2);
      cntr1(x3, x2, y3, y2);
      return;
    }
  }

  // Install the cell in the array.
  grid(x1, y2).bot_len_ = x2 - x1;
  grid(x1, y1).top_len_ = x2 - x1;
  grid(x2, y1).left_len_ = y2 - y1;
  grid(x1, y1).right_len_ = y2 - y1;
}


void 
Contour::pass2(int x1,
	       int x2,
	       int y1,
	       int y2)
{
  int left = 0;
  int right = 0;
  int top = 0;
  int bot = 0;
  double yy0 = 0;
  double yy1 = 0;
  double xx0 = 0;
  double xx1 = 0;
  int old, neu;
  double fold, fnew;

  // If not a real cell, punt.
  if ((x1 == x2) || (y1 == y2))   
    return;

  double f11 = grid(x1, y1).value_;
  double f12 = grid(x1, y2).value_;
  double f21 = grid(x2, y1).value_;
  double f22 = grid(x2, y2).value_;

  // Is cell divisible? 
  if ((x2 > x1 + 1) || (y2 > y1 + 1)) {
    int x3 = (x1 + x2) / 2;
    int y3 = (y1 + y2) / 2;
    double f33 = grid(x3, y3).value_;
    unsigned i = 0;
    unsigned j = 0;
    if (f33 < f11)
      i++;
    else if (f33 > f11)
      j++;
    if (f33 < f12)
      i++;
    else if (f33 > f12)
      j++;
    if (f33 < f21)
      i++;
    else if (f33 > f21)
      j++;
    if (f33 < f22)
      i++;
    else if (f33 > f22)
      j++;
    // Should we divide the cell?
    if ((i > 2) || (j > 2)) {
      // Yes.
      pass2(x1, x3, y1, y3);
      pass2(x3, x2, y1, y3);
      pass2(x1, x3, y3, y2);
      pass2(x3, x2, y3, y2);
      return;
    }
  }
  for (unsigned i = 0; i < levels_.size(); i++) {
    double v = levels_[i];
    unsigned j = 0;
    if (f21 > v)
      j++;
    if (f11 > v)
      j |= 2;
    if (f22 > v)
      j |= 4;
    if (f12 > v)
      j |= 010;
    if ((f11 > v) ^ (f12 > v)) {
      if ((grid(x1, y1).left_len_ != 0) &&
          (grid(x1, y1).left_len_ < grid(x1, y1).right_len_)) {
        old = y1;
        fold = f11;
        while (1) {
          neu = old + grid(x1, old).left_len_;
          fnew = grid(x1, neu).value_;
          if ((fnew > v) ^ (fold > v))
            break;
          old = neu;
          fold = fnew;
        }
        yy0 = ((old - y1) + (neu - old) * (v - fold) / (fnew - fold)) 
	      / (y2 - y1);
      }
      else
        yy0 = (v - f11) / (f12 - f11);
      left = (int)(y1 + (y2 - y1) * yy0 + 0.5);
    }
    if ((f21 > v) ^ (f22 > v)) {
      if ((grid(x2, y1).right_len_ != 0) &&
          (grid(x2, y1).right_len_ < grid(x2, y1).left_len_)) {
        old = y1;
        fold = f21;
        while (1) {
          neu = old + grid(x2, old).right_len_;
          fnew = grid(x2, neu).value_;
          if ((fnew > v) ^ (fold > v))
            break;
          old = neu;
          fold = fnew;
        }
        yy1 = ((old - y1) + (neu - old) * (v - fold) / (fnew - fold)) /
              (y2 - y1);
      }
      else
        yy1 = (v - f21) / (f22 - f21);
      right = (int)(y1 + (y2 - y1) * yy1 + 0.5);
    }
    if ((f21 > v) ^ (f11 > v)) {
      if ((grid(x1, y1).bot_len_ != 0) &&
          (grid(x1, y1).bot_len_ < grid(x1, y1).top_len_)) {
        old = x1;
        fold = f11;
        while (1) {
          neu = old + grid(old, y1).bot_len_;
          fnew = grid(neu, y1).value_;
          if ((fnew > v) ^ (fold > v))
            break;
          old = neu;
          fold = fnew;
        }
        xx0 = ((old - x1) + (neu - old) * (v - fold) / (fnew - fold)) /
              (x2 - x1);
      }
      else
        xx0 = (v - f11) / (f21 - f11);
      bot = (int)(x1 + (x2 - x1) * xx0 + 0.5);
    }
    if ((f22 > v) ^ (f12 > v)) {
      if ((grid(x1, y2).top_len_ != 0) &&
          (grid(x1, y2).top_len_ < grid(x1, y2).bot_len_)) {
        old = x1;
        fold = f12;
        while (1) {
          neu = old + grid(old, y2).top_len_;
          fnew = grid(neu, y2).value_;
          if ((fnew > v) ^ (fold > v))
            break;
          old = neu;
          fold = fnew;
        }
        xx1 = ((old - x1) + (neu - old) * (v - fold) / (fnew - fold)) /
              (x2 - x1);
      }
      else
        xx1 = (v - f12) / (f22 - f12);
      top = (int)(x1 + (x2 - x1) * xx1 + 0.5);
    }
    switch (j) {
    case 7:
    case 010:
      line(x1, left, top, y2);
      break;

    case 5:
    case 012:
      line(bot, y1, top, y2);
      break;

    case 2:
    case 015:
      line(x1, left, bot, y1);
      break;

    case 4:
    case 013:
      line(top, y2, x2, right);
      break;

    case 3:
    case 014:
      line(x1, left, x2, right);
      break;

    case 1:
    case 016:
      line(bot, y1, x2, right);
      break;

    case 0:
    case 017:
      break;

    case 6:
    case 011: {
      double yy3 = (xx0 * (yy1 - yy0) + yy0) 
	           / (1.0 - (xx1 - xx0) * (yy1 - yy0));
      double xx3 = yy3 * (xx1 - xx0) + xx0;
      xx3 = x1 + xx3 * (x2 - x1);
      yy3 = y1 + yy3 * (y2 - y1);
      xx3 = x_offset_ + xx3 * x_scale_;
      yy3 = y_offset_ + yy3 * y_scale_;
      // double f = function_(cookie_, xx3, yy3);
      double f = function_(cookie_, isnan(xx3) ? x1_ : xx3, 
			   isnan(yy3) ? y1_ : yy3);
      if (f == v) {
        line(bot, y1, top, y2);
        line(x1, left, x2, right);
      }
      else {
        if (((f > v) && (f22 > v)) || ((f < v) && (f22 < v))) {
          line(x1, left, top, y2);
          line(bot, y1, x2, right);
        }
        else {
          line(x1, left, bot, y1);
          line(top, y2, x2, right);
        }
      }
      break; }
    }
  }
}


