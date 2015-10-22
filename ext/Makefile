include ../config.mk
include ../standard.mk

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

# Link statically against the C++ standard library.
# LDLIBS	+= $(shell $(CXX) -print-file-name=libstdc++.a)

CPPFLAGS	+= -I$(AGGINCDIR)
CXXFLAGS	+= $(IMLIB_CFLAGS) $(XFT_CFLAGS) $(X_CFLAGS)
LDLIBS		+= $(AGG_LIBS) $(IMLIB_LIBS) $(XFT_LIBS) $(X_LIBS)

CXXFILES	= \
		PyBoolArray.cc \
		PyContour.cc \
		PyExpr.cc \
		PyFourVector.cc \
		PyHist.cc \
		PyHistogram1D.cc \
		PyHistogram2D.cc \
		PyImageFile.cc \
		PyIterator.cc \
		PyRandom.cc \
		PyRow.cc \
		PyRowDict.cc \
		PyRowObject.cc \
		PyScatter.cc \
		PyTable.cc \
		PyTimer.cc \
		PyX11Window.cc \
		aggrender.cc \
		contour.cc \
		ext.cc \
		python.cc \
		random.cc \
		table.cc

OBJFILES	= $(CXXFILES:.cc=.o)

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

clean:
	rm -f *.o ext.so


install:		ext.so
	$(INSTALLPROGRAM) -D ext.so $(INSTALLLIBDIR)/hep/ext.so


ext.so:			$(OBJFILES)
	$(CXX) -shared $(LDFLAGS) $^ -o $@ $(LDLIBS)


setup:
	@ if [ ! -L ../py/hep/ext.so ]; then \
	  ln -s ../../ext/ext.so ../py/hep/ext.so; \
	fi


ext.o: 
CXXFLAGS	:= $(CXXFLAGS) \
		   -DCXXFLAGS="\"$(CXXFLAGS)\"" 


# To configure Freetype, an include file name stored in a preprocessor
# macro is used.  This causes problems with the autodependency
# processor.  Define the macro here as something innocuous.
depend.mk: \
CPPFLAGS	+= -DFT_FREETYPE_H="<ft2build.h>"


#-----------------------------------------------------------------------
# dependecies
#-----------------------------------------------------------------------

all:			ext.so setup

ext.o:			python.hh \
			PyBoolArray.hh \
			PyContour.hh \
			PyFourVector.hh \
			PyHistogram1D.hh \
			PyHistogram2D.hh \
			PyRandom.hh \
			PyRow.hh \
			PyRowDict.hh \
			PyRowObject.hh \
			PyScatter.hh \
			PyTable.hh \
			PyX11Window.hh \
			random.hh 

-include depend.mk

#-----------------------------------------------------------------------
# Local variables:
# mode: Makefile
# fill-column: 72
# End:
