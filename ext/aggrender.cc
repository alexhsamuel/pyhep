//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>

#include "agg_basics.h"
#include "agg_conv_contour.h"
#include "agg_conv_dash.h"
#include "agg_conv_stroke.h"
#include "agg_font_freetype.h"
#include "agg_path_storage.h"
#include "agg_rasterizer_scanline_aa.h"
#include "agg_renderer_scanline.h"
#include "agg_rendering_buffer.h"
#include "agg_scanline_p.h"
#include "util/agg_color_conv_rgb8.h"

// Use RGB24 for internal rendering.
#include "agg_pixfmt_rgb.h"

#include "aggrender.hh"

//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

// Set up pixel types.
typedef agg::pixfmt_rgb24 
Pixel;

typedef agg::rgba8 
PixelColorType;

typedef agg::order_rgb
ComponentOrder;

// Use 24 bits per pixel.
const static int 
bits_per_pixel = 24;

// Set up basic rendering types.
typedef agg::renderer_base<Pixel> 
BaseRenderer;

typedef agg::renderer_scanline_aa_solid<BaseRenderer> 
SolidRenderer;

typedef agg::scanline_p8 
Scanline;

typedef agg::font_engine_freetype_int32 
FontEngine;

typedef agg::font_cache_manager<FontEngine> 
FontManager;

struct AggFont
{
  FontEngine* engine_;
  FontManager* manager_;
};


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

const static size_t 
pixel_sizes[] = { 4, 1, 2, 2, 3, 3, 4, 4, 4, 4 };


void
fillPath(const PointList& points,
	 agg::path_storage& path)
{
  bool first = true;
  for (PointList::const_iterator i = points.begin();
       i != points.end();
       ++i) 
    if (first) {
      path.move_to(i->x, i->y);
      first = false;
    }
    else
      path.line_to(i->x, i->y);
}


/* Load a font from 'path'.

   Ownership of the returned 'AggFont' object is not passed to the caller.  
*/

AggFont*
loadFont(const char* path,
	 FontCache& font_cache)
{
  // Is this font already loaded?
  FontCache::iterator match = font_cache.find(path);
  // Yes.  Return the cached copy.
  if (match != font_cache.end())
    return match->second;

  // Construct the font, engine, and manager.
  AggFont* font = new AggFont;
  font->engine_ = new FontEngine;
  font->manager_ = new FontManager(*font->engine_);
  // Configure the engine.
  font->engine_->hinting(true);
  // Load the font.
  if (! font->engine_->load_font(path, 0, agg::glyph_ren_agg_gray8))
    throw FontLoadError();
  if (font->engine_->char_map(FT_ENCODING_UNICODE) != 0)
    throw FontEncodingError();
  
  // Cache it for later.
  font_cache[path] = font;
  
  return font;
}


}  // anonymous namespace

//----------------------------------------------------------------------
// methods
//----------------------------------------------------------------------

AggImage::AggImage(int width,
		   int height)
  : width_(width),
    height_(height),
    image_buffer_(NULL),
    color_(Color(0, 0, 0)),
    thickness_(1),
    font_(NULL)
{
}


AggImage::~AggImage()
{
  // Clean up the font cache contents.
  for (FontCache::iterator i = font_cache_.begin();
       i != font_cache_.end();
       ++i) {
    AggFont* font = i->second;
    delete font->engine_;
    delete font->manager_;
    delete font;
  }

  delete [] image_buffer_;
}


void
AggImage::resize(int width,
		 int height)
{
  // Hold on to the old image buffer.
  unsigned char* old_image_buffer = image_buffer_;

  // Create the new image buffer.
  image_buffer_ = 
    new unsigned char[width * height * (bits_per_pixel / 8)];
  // Attach it to the AGG rendering buffer.
  rendering_buffer_.attach(image_buffer_, width, height, 
			   width * (bits_per_pixel / 8));

  // Clean up.
  if (old_image_buffer != NULL)
    delete [] old_image_buffer;

  width_ = width;
  height_ = height;
}


void
AggImage::setColor(Color color)
{
  color_ = color;
}


void
AggImage::setDash(const Dash& dash)
{
  dash_ = dash;
}


void
AggImage::setFont(const std::string& path,
		  double size,
		  double shear)
{
  font_ = loadFont(path.c_str(), font_cache_);
  font_->engine_->height(size);
  font_->engine_->width(size);
  agg::trans_affine transformation(1, -shear, 0, 1, 0, 0);
  font_->engine_->transform(transformation);
}

		     
void
AggImage::setThickness(double thickness)
{
  thickness_ = thickness;
}


void
AggImage::drawCircle(Point center,
		     double radius,
		     bool fill)
{
  // Construct the path.
  agg::path_storage path;
  int num_segments = std::max(12, int(M_PI * radius));
  path.move_to(center.x + radius, center.y);
  for (int i = 1; i < num_segments; ++i) {
    double angle = (2 * M_PI * i) / num_segments;
    path.line_to(center.x + radius * cos(angle), 
		 center.y + radius * sin(angle));
  }
  path.close_polygon();

  // Set up the renderer and rasterizer.
  Pixel pixel(rendering_buffer_);
  BaseRenderer base_renderer(pixel);
  SolidRenderer renderer(base_renderer);
  Scanline scanline;
  agg::rasterizer_scanline_aa<> rasterizer;

  // Set attributes.
  renderer.color(agg::rgba(color_.red, color_.green, color_.blue));

  // Draw the polygon.
  if (fill) {
    // Fill the circle.
    rasterizer.add_path(path);
    // Render the path.
    agg::render_scanlines(rasterizer, scanline, renderer);
  }
  else {
    // Draw the outline.
    agg::conv_stroke<agg::path_storage> stroke(path);
    stroke.width(thickness_);
    rasterizer.add_path(stroke);
    // Render the path.
    agg::render_scanlines(rasterizer, scanline, renderer);
  }
}


void
AggImage::drawLine(const PointList& points)
{
  // Construct the renderer and rasterizer.
  Pixel pixel(rendering_buffer_);
  BaseRenderer base_renderer(pixel);
  SolidRenderer renderer(base_renderer);
  renderer.color(agg::rgba(color_.red, color_.green, color_.blue));
  Scanline scanline;
  agg::rasterizer_scanline_aa<> rasterizer;

  // Construct the path.
  agg::path_storage path;
  fillPath(points, path);
  // Construct a converter to stroke the path.
  agg::conv_stroke<agg::path_storage> stroke(path);

  // Handle dashed lines specially.
  if (dash_.size() > 0) {
    // Yes, there are dashes.
    agg::conv_dash<agg::path_storage> dash(path);
    for (Dash::iterator i = dash_.begin();
	 i != dash_.end();
	 ++i)
      dash.add_dash(i->first, i->second);
    agg::conv_stroke<agg::conv_dash<agg::path_storage> > stroke(dash);
    stroke.width(thickness_);
    rasterizer.add_path(stroke);
    // Render the path.
    agg::render_scanlines(rasterizer, scanline, renderer);
  }
  else {
    // No dashes.  Stroke directly.
    stroke.width(thickness_);
    rasterizer.add_path(stroke);
    // Render the path.
    agg::render_scanlines(rasterizer, scanline, renderer);
  }
}


void
AggImage::drawPolygon(const PointList& points)
{
  // Construct the path.
  agg::path_storage path;
  fillPath(points, path);

  // Set up the renderer and rasterizer.
  Pixel pixel(rendering_buffer_);
  BaseRenderer base_renderer(pixel);
  SolidRenderer renderer(base_renderer);
  renderer.color(agg::rgba(color_.red, color_.green, color_.blue));
  Scanline scanline;
  agg::rasterizer_scanline_aa<> rasterizer;

  // Draw the polygon.
  rasterizer.add_path(path);
  agg::render_scanlines(rasterizer, scanline, renderer);
}


void
AggImage::drawText(Point point,
		   wchar_t* text,
		   size_t len)
{
  double x = point.x;
  double y = point.y;

  // Create a rendering buffer flipped in y.
  agg::rendering_buffer rendering_buffer;
  rendering_buffer.attach
    (image_buffer_, width_, height_, -width_ * (bits_per_pixel / 8));
  y = height_ - y;

  // Set up the renderer.
  Pixel pixel(rendering_buffer);
  BaseRenderer base_renderer(pixel);
  SolidRenderer renderer(base_renderer);
  renderer.color(agg::rgba(color_.red, color_.green, color_.blue));

  if (font_ == NULL) 
    throw NoFontError();

  for (wchar_t* c = text; c < text + len; ++c) {
    const agg::glyph_cache* glyph = font_->manager_->glyph(*c);
    if (glyph != NULL) {
      font_->manager_->init_embedded_adaptors(glyph, x, y);
      assert(glyph->data_type == agg::glyph_data_gray8);
      agg::render_scanlines(font_->manager_->gray8_adaptor(),
			    font_->manager_->gray8_scanline(),
			    renderer);

      x += glyph->advance_x;
      y += glyph->advance_y;
    }
  }
}


char* 
AggImage::getImageBuffer(PixelFormat pixel_format)
{
  size_t pixel_size = pixel_sizes[pixel_format];
  size_t row_length = width_ * pixel_size;
  char* buffer = new char[height_ * row_length * 2];
  
  // Create a new rendering buffer object using it.
  agg::rendering_buffer rendering_buffer;
  rendering_buffer.attach((agg::int8u*) buffer, width_, height_, row_length);

  // Convert pixel data to the appropriate format.
  agg::rendering_buffer* dst = &rendering_buffer;
  agg::rendering_buffer* src = &rendering_buffer_;
  switch (pixel_format) {
  case PIXELFORMAT_rgb555:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_rgb555()); 
    break;
  case PIXELFORMAT_rgb565:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_rgb565()); 
    break;
  case PIXELFORMAT_rgba32:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_rgba32()); 
    break;
  case PIXELFORMAT_abgr32:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_abgr32()); 
    break;
  case PIXELFORMAT_argb32:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_argb32()); 
    break;
  case PIXELFORMAT_bgra32:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_bgra32()); 
    break;
  case PIXELFORMAT_rgb24:
    agg::color_conv(dst, src, agg::color_conv_rgb24_to_rgb24());
    break;
  default:
    abort();
  }

  return buffer;
}


