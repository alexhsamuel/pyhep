include ../../../config.mk
include ../../../standard.mk

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

CPPFLAGS	+= -I../include
CXXFLAGS	+= $(XFT_CFLAGS)

CXXFILES	= \
		agg_arc.cpp \
		agg_arrowhead.cpp \
		agg_bezier_arc.cpp \
		agg_bspline.cpp \
		agg_curves.cpp \
		agg_embedded_raster_fonts.cpp \
		agg_font_freetype.cpp \
		agg_gsv_text.cpp \
		agg_image_filters.cpp \
		agg_line_aa_basics.cpp \
		agg_line_profile_aa.cpp \
		agg_rounded_rect.cpp \
		agg_sqrt_tables.cpp \
		agg_trans_affine.cpp \
		agg_trans_double_path.cpp \
		agg_trans_single_path.cpp \
		agg_trans_warp_magnifier.cpp \
		agg_vcgen_bspline.cpp \
		agg_vcgen_contour.cpp \
		agg_vcgen_dash.cpp \
		agg_vcgen_markers_term.cpp \
		agg_vcgen_smooth_poly1.cpp \
		agg_vcgen_stroke.cpp \
		agg_vpgen_clip_polygon.cpp \
		agg_vpgen_clip_polyline.cpp \
		agg_vpgen_segmentator.cpp

# CFILES	= ../gpc/gpc.c

OBJFILES	= $(CXXFILES:.cpp=.o)

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

clean:
	rm -f *.o libagg.a


libagg.a:	$(OBJFILES)
	rm -f $@
	$(AR) cq $@ $^


#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:		libagg.a
