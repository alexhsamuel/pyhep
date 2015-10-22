#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

CC		= gcc
CFLAGS		= -g -O2 -Wall
CXX		= g++
CXXFLAGS	= -g -O2 -Wall
FC		= f95

LIBX11		= @LIBX11@

PYHEPDIR	= /home/samuel/dev/pyhep
BASEDIR		= $(PYHEPDIR)/py
DATADIR		= $(BASEDIR)/hep/data

PYTHON		= /usr/bin/python2
PYTHONPREFIX	= /usr
PYTHONVERSION	= 2.4
PYTHONINCDIR	= $(PYTHONPREFIX)/include/python$(PYTHONVERSION)/
PYTHONLIBDIR	= $(PYTHONPREFIX)/lib/python$(PYTHONVERSION)/

ENABLEDOCS	= no
PYDOC		= $(PYTHONPREFIX)/lib/python$(PYTHONVERSION)/pydoc.py

X_CFLAGS	= 
X_LIBS		=  -L/usr/lib64  -lX11
XFT_CFLAGS	= -I/usr/include/freetype2  
XFT_LIBS	= -lXft -lXrender -lfontconfig -lfreetype -lX11  
IMLIB_CFLAGS	= 
IMLIB_LIBS	= -L/usr/lib64 -lImlib -ljpeg -ltiff -lungif -lpng -lz -lm -lXext -L/usr/lib64 -lXext -lX11

ROOTSYS		= no
CERN		= no
EVTGEN		= no

SWIG		= /usr/bin/swig
SWIGVERSION	= 1.3.31

AGG		= $(PYHEPDIR)/packages/agg
AGGINCDIR	= $(AGG)/include
AGG_LIBS	= $(AGG)/src/libagg.a

INSTALL		= /usr/bin/install -c
INSTALLPROGRAM	= $(INSTALL) -m 755
INSTALLDATA	= $(INSTALL) -m 644

INSTALLDIR	= /home/samuel/sw/pyhep
INSTALLLIBDIR	= $(INSTALLDIR)/lib/python$(PYTHONVERSION)
INSTALLBINDIR	= $(INSTALLDIR)/bin
INSTALLDOCDIR	= $(INSTALLDIR)/share/doc/pyhep-$(VERSION)
INSTALLDATADIR  = $(INSTALLLIBDIR)/hep/data

#-----------------------------------------------------------------------
# the version number
#-----------------------------------------------------------------------

VERSION		= $(shell cat $(PYHEPDIR)/version)

#-----------------------------------------------------------------------
# Local variables:
# mode: Makefile
# fill-column: 72
# End:
