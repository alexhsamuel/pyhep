include ../../standard.mk
include ../../config.mk

ifeq ($(EVTGEN),no)
  $(error EvtGen not configured)
endif

ifeq ($(CERN),no)
  $(error CERNLIB not configured)
endif

.SECONDARY:

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

EVTGENINCDIR	= $(EVTGEN)
EVTGENLIBDIR	= $(EVTGEN)

CERNLIBDIR	= $(CERN)/lib
CERNLDFLAGS	= -L$(CERNLIBDIR)

CPPFLAGS	+= -I$(EVTGENINCDIR)
LDFLAGS		+= -L$(CERNLIBDIR)
LDLIBS		+= $(EVTGENLIBDIR)/libEvtGen.a 
LDLIBS		+= $(EVTGENLIBDIR)/libEvtGenModels.a 
LDLIBS		+= $(EVTGENLIBDIR)/libEvtGenBase.a
LDLIBS		+= $(EVTGENLIBDIR)/libCLHEP.a
LDLIBS		+= $(CERNLIBDIR)/libpythia6205.a $(CERNLIBDIR)/libpythiad.a
LDLIBS		+= -ljetset74 -lphotos202 -lpacklib -lmathlib -lg2c 

OBJFILES	= ext.o PyGenerator.o PyParticle.o

# Resolve the parent 'ext.so'.
INSTALLRPATH	= -Wl,-rpath=\$$ORIGIN/.. 

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

clean:
	rm -f $(OBJFILES) ext.so 


install:		ext-install.so
	$(INSTALLPROGRAM) -D ext-install.so \
		$(INSTALLLIBDIR)/hep/evtgen/ext.so


setup:
	@ if [ ! -L ../../py/hep/evtgen/ext.so ]; then \
	  ln -s ../../../ext/evtgen/ext.so ../../py/hep/evtgen/ext.so; \
	fi


#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:			setup ext.so

PyGenerator.o:		../python.hh PyParticle.hh PyGenerator.hh

PyParticle.o:		../python.hh PyParticle.hh

ext.o:			../python.hh PyParticle.hh PyGenerator.hh

ext.so: LDLIBS += $(PYHEPDIR)/py/hep/ext.so 
ext.so:			$(OBJFILES)

ext-install.so:	LDFLAGS += $(INSTALLRPATH)
ext-install.so: LDLIBS += ext.so
ext-install.so:		$(OBJFILES)

