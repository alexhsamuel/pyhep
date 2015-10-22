include ../../config.mk
include ../../standard.mk

ifeq ($(CERN),no)
  $(error CERNLIB not configured)
endif

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

CERNLIBDIR	= $(CERN)/lib
CERNLDFLAGS	= -L$(CERNLIBDIR)
CERNLDLIBS	= -lpacklib -lkernlib -lmathlib -lg2c -lcrypt -lnsl

LDFLAGS		+= $(CERNLDFLAGS)
LDLIBS		+= $(CERNLDLIBS)

CXXFILES	= \
		ext.cc \
		hbook.cc \
		minuit.cc \
		util.cc

OBJFILES	= $(CXXFILES:.cc=.o) cernlib.o

# Resolve the parent 'ext.so'.
INSTALLRPATH	= -Wl,-rpath=\$$ORIGIN/.. 

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

clean:
	rm -f $(OBJFILES) ext.so 


install:		ext-install.so
	$(INSTALLPROGRAM) -D ext-install.so \
		$(INSTALLLIBDIR)/hep/cernlib/ext.so


setup:
	@ if [ ! -L ../../py/hep/cernlib/ext.so ]; then \
	  ln -s ../../../ext/cernlib/ext.so ../../py/hep/cernlib/ext.so; \
	fi


#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:			setup ext.so

ext.so: LDFLAGS	+= $(RPATH)
ext.so: LDLIBS += $(PYHEPDIR)/py/hep/ext.so 
ext.so:			$(OBJFILES)

ext-install.so: LDFLAGS	+= $(INSTALLRPATH)
ext-install.so: LDLIBS += ext.so
ext-install.so:		$(OBJFILES)

cernlib.o:		hbook.inc

-include depend.mk

