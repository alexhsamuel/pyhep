include ../../standard.mk
include ../../config.mk

ifeq ($(ROOTSYS),no)
  $(error Root not configured)
endif

.SECONDARY:

.PHONY: rootsys

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

ROOT		= $(ROOTSYS)/bin/root -l -b
ROOTINCDIR	= $(ROOTSYS)/include
ROOTLIBDIR	= $(ROOTSYS)/lib

# Command to run cint with the right environment set up.
ROOTCINT	= env LD_LIBRARY_PATH=$(LD_LIBRARY_PATH):$(ROOTSYS)/lib \
		  ROOTSYS=$(ROOTSYS) \
		  $(ROOTSYS)/bin/rootcint

# Names of Root libraries linked by our libraries.
ROOTLIBS	= Core Cint Hist Tree Matrix

# Resolve Root libraries from our copied ROOTSYS.
RPATH		= -Wl,-rpath,$(ROOTSYS)/lib

# Additional Root files needed at run time.
ROOTEXTRA	= include/RQ_OBJECT.h cint/MAKEINFO cint/include

# Stuff to copy into our 'ROOTSYS' directory.
TARGETROOTFILES = $(ROOTLIBS:%=ROOTSYS/lib/lib%.so) \
		  $(ROOTEXTRA:%=ROOTSYS/%)

# Stuff to copy into the installed 'ROOTSYS' directory.
INSTALLROOTDIR	= $(INSTALLLIBDIR)/hep/root
INSTALLROOTLIBS = $(ROOTLIBS:%=$(INSTALLROOTDIR)/ROOTSYS/lib/lib%.so)
INSTALLROOTSYS	= $(INSTALLROOTDIR)/ROOTSYS
INSTALLROOTFILES= $(ROOTEXTRA:%=$(INSTALLROOTSYS)/%)

# Resolve the parent 'ext.so', and Root libraries from the installed
# ROOTSYS.
INSTALLRPATH	= -Wl,-rpath=\$$ORIGIN/.. \
		  -Wl,-rpath=\$$ORIGIN/ROOTSYS/lib 

CPPFLAGS	+= -I$(ROOTINCDIR)
LDFLAGS		+= -L$(ROOTLIBDIR)
LDLIBS		+= $(ROOTLIBS:%=-l%) 

OBJFILES	= ext.o tree.o TBlob.o TBlobDict.o 

# We have to specify the C interface name for newer versions of SWIG to
# obtain the default name of older versions.  Unfortunately, older
# versions don't support this option.
ifeq ($(SWIGVERSION),1.1)
  SWIGFLAGS	=
else
  SWIGFLAGS	= -interface rootc
endif

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

clean:
	rm -f root_wrap.{cc,o,doc} root.py rootc.so
	rm -f *.o ext.so ext-install.so
	rm -f TBlobDict.{cc,h}


$(TARGETROOTFILES): \
ROOTSYS/%:		$(ROOTSYS)/%
	mkdir -p `dirname $@`
	cp -r $< $@


rootsys:		$(TARGETROOTFILES)


root_wrap.cc root_wrap.doc root.py: \
			root.i
	$(SWIG) $(SWIGFLAGS) -shadow -c++ -python -o $@ $<


setup:
	@ if [ ! -L ../../py/hep/root/ext.so ]; then \
	  ln -s ../../../ext/root/ext.so ../../py/hep/root/ext.so; \
	fi
	@ if [ ! -L ../../py/hep/root/rootc.so ]; then \
	  ln -s ../../../ext/root/rootc.so ../../py/hep/root/rootc.so; \
	fi
	@ if [ ! -L ../../py/hep/root/root.py ]; then \
	  ln -s ../../../ext/root/root.py ../../py/hep/root/root.py; \
	fi
	@ if [ ! -L ../../py/hep/root/ROOTSYS ]; then \
	  ln -s ../../../ext/root/ROOTSYS ../../py/hep/root/ROOTSYS; \
	fi


%Dict.h %Dict.cc:	%.hh %LinkDef.hh
	$(ROOTCINT) -f $*Dict.cc -c $^


# Installation-specific stuff.
# 
# We compile special versions of the shared libraries for installation.
# These have their rpath set to '$ORIGIN/ROOTSYS/lib'; Linux expands
# '$ORIGIN' to the directory containing the library at run-time.  
#
# We install the ROOTSYS directory, which contains the libraries in
# 'lib' plus some other stuff Root seems to need, into the installation
# directory.

$(INSTALLROOTLIBS): \
$(INSTALLROOTDIR)/ROOTSYS/lib/lib%.so: \
			$(ROOTSYS)/lib/lib%.so
	$(INSTALLPROGRAM) -D $< $@


# FIXME: There's no easy way to '$(INSTALL)' a directory and its
# contents, so use 'cp -r' for now.
$(INSTALLROOTFILES): \
$(INSTALLROOTSYS)/%:	$(ROOTSYS)/%
	mkdir -p $(dir $@)
	cp -r $< $@


install:		rootsys rootc-install.so ext-install.so \
			$(INSTALLROOTLIBS) $(INSTALLROOTFILES)
	$(INSTALLPROGRAM) -D \
	  rootc-install.so $(INSTALLLIBDIR)/hep/root/rootc.so
	$(INSTALLPROGRAM) -D \
	  ext-install.so $(INSTALLLIBDIR)/hep/root/ext.so


#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:			setup rootsys rootc.so ext.so 

-include depend.mk

rootc.so: LDFLAGS += $(RPATH)
rootc.so:		root_wrap.o

rootc-install.so: LDFLAGS += $(INSTALLRPATH)
rootc-install.so:	root_wrap.o

ext.so: LDFLAGS	+= $(RPATH)
ext.so: LDLIBS += $(PYHEPDIR)/py/hep/ext.so 
ext.so:			$(OBJFILES)

ext-install.so: LDFLAGS	+= $(INSTALLRPATH)
ext-install.so: LDLIBS += ext.so
ext-install.so:		$(OBJFILES)

