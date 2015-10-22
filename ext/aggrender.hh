//----------------------------------------------------------------------
//
// aggrender.hh
//
// Copyright (C) 2005 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------
//
// Portions adapted from:
// 
// Anti-Grain Geometry - Version 2.2
// Copyright (C) 2002-2004 Maxim Shemanarev (http://www.antigrain.com)
//
// Permission to copy, use, modify, sell and distribute this software 
// is granted provided this copyright notice appears in all copies. 
// This software is provided "as is" without express or implied
// warranty, and with no claim as to its suitability for any purpose.
//
//----------------------------------------------------------------------

/* Adapter class for AGG-based renderinging.  */

#ifndef __AGGRENDER_HH__
#define __AGGRENDER_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <map>
#include <string>
#include <vector>

#include "agg_basics.h"
#include "agg_rendering_buffer.h"

//----------------------------------------------------------------------
// exceptions
//----------------------------------------------------------------------

class NoFontError
{
};


class FontLoadError
{
};


class FontEncodingError
{
};


//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

enum PixelFormat {
  PIXELFORMAT_undefined = 0,  // By default. No conversions are applied.
  PIXELFORMAT_gray8,          // Simple 256 level grayscale.
  PIXELFORMAT_rgb555,         // 15 bit rgb; depends on the byte ordering.
  PIXELFORMAT_rgb565,         // 16 bit rgb; depends on the byte ordering.
  PIXELFORMAT_rgb24,          // R-G-B, one byte per color component.
  PIXELFORMAT_bgr24,          // B-G-R, native win32 BMP format.
  PIXELFORMAT_rgba32,         // R-G-B-A, one byte per color component.
  PIXELFORMAT_argb32,         // A-R-G-B, native MAC format.
  PIXELFORMAT_abgr32,         // A-B-G-R, one byte per color component.
  PIXELFORMAT_bgra32,         // B-G-R-A, native win32 BMP format.
  PIXELFORMAT_last            // Sentry.
};


//----------------------------------------------------------------------

struct Color
{
  Color(double r, double g, double b) : red(r), green(g), blue(b) {}

  double red;
  double green;
  double blue;
};


struct Point
{
  Point() {}
  Point(double xx, double yy) : x(xx), y(yy) {}

  double x;
  double y;
};


typedef std::vector<Point>
PointList;

struct AggFont;

typedef std::map<std::string, AggFont*> 
FontCache;

typedef std::vector<std::pair<double, double> > 
Dash;

//----------------------------------------------------------------------

class AggImage
{
public:

  AggImage(int width, int height);
  ~AggImage();

  int getWidth() const { return width_; }
  int getHeight() const { return height_; }

  void resize(int width, int height);
  void setColor(Color color);
  void setDash(const Dash& dash);
  void setFont(const std::string& path, double size, double shear);
  void setThickness(double thickness);

  void drawCircle(Point center, double radius, bool fill);
  void drawLine(const PointList& points);
  void drawPolygon(const PointList& points);
  void drawText(Point point, wchar_t* text, size_t len);

  /* Create a buffer of the image with pixels encoded in 'pixel_format'.
     Returns an array which should be deallocated by the caller with
     'delete[]'.  */
  char* getImageBuffer(PixelFormat pixel_format);

private:

  // The size, in pixels.
  int width_;
  int height_;

  // Raw pixel buffer and AGG rendering buffer containing the image
  // displayed in the window.  
  unsigned char* image_buffer_;
  agg::rendering_buffer rendering_buffer_;

  // The cache of loaded fonts.
  FontCache font_cache_;

  // The current graphics state.
  Color color_;
  double thickness_;
  Dash dash_;
  AggFont* font_;

};


//----------------------------------------------------------------------

#endif  // #ifndef __AGGRENDER_HH__
