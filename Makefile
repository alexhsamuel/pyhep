SUBDIRS		= packages ext

include config.mk

# Build documentation if enabled.
ifeq ($(ENABLEDOCS),yes)
  SUBDIRS	+= doc
endif

# Build the CERNLIB extension module only if we're configured for 
# CERNLIB support.
ifneq ($(CERN),no)
  SUBDIRS	+= ext/cernlib
endif

# Build the ROOT extension module only if we're configured for 
# ROOT support.
ifneq ($(ROOTSYS),no)
  SUBDIRS	+= ext/root
endif

# Build the EvtGen extension module only if we have all the stuff we
# need.
ifneq ($(EVTGEN),no)
ifneq ($(CERN),no)
  SUBDIRS	+= ext/evtgen
endif
endif

include standard.mk

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

TARBALL		= pyhep-$(VERSION).tgz

SPEC		= pyhep.spec

PYSOURCES	= py/hep/config.py.in \
		  $(filter-out \
		    py/hep/config.py, \
		    $(shell find py/hep -name \*.py))

SOURCES		= configure.in configure install-sh config.mk.in \
                  Makefile standard.mk clean pyhep.spec pyhep.spec.in \
		  py/hep/ext.so \
		  py/hep/cernlib/ext.so \
		  py/hep/root/{ext.so,rootc.so} \
		  py/hep/evtgen/ext.so \
		  $(PYSOURCES) ext doc

#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:			$(DATADIR)/pdt.pickle

default:		all

dist:			$(TARBALL)

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

.PHONY:			pyinstall


install:		py/hep/config.py-install \
			scripts/pyhep-install \
			scripts/pyhep-pythonpath-install
	for src in $(shell cd py; find hep -name \*.py); do \
	  echo installing $$src; \
	  dst=$(INSTALLLIBDIR)/$$src; \
	  $(COMPILEPYTHON) py/$$src; \
	  $(INSTALLDATA) -D py/$$src $$dst; \
	  $(INSTALLDATA) -D py/$${src}c $${dst}c; \
	done
	$(INSTALLDATA) py/hep/config.py-install \
	  $(INSTALLLIBDIR)/hep/config.py
	$(INSTALLPROGRAM) -d $(INSTALLDOCDIR)
	$(INSTALLDATA) -D COPYRIGHT README $(INSTALLDOCDIR)
	$(INSTALLPROGRAM) -d $(INSTALLDATADIR)
	$(INSTALLDATA) -D py/hep/data/*.{pickle,dat} $(INSTALLDATADIR)
	$(INSTALLPROGRAM) -d $(INSTALLDATADIR)/fonts
	$(INSTALLDATA) -D py/hep/data/fonts/*.{pfb,afm} \
	  $(INSTALLDATADIR)/fonts
	$(INSTALLPROGRAM) -D scripts/pyhep-install $(INSTALLBINDIR)/pyhep
	$(INSTALLPROGRAM) -D scripts/pyhep-pythonpath-install \
	  $(INSTALLBINDIR)/pyhep-pythonpath


clean:
	rm -f $(TARBALL) $(SPEC)


distclean:		clean
	@ ./clean --do


scripts/pyhep-install: 	scripts/pyhep-install.in
	cat $^ \
	  | sed -e "s!@PYTHON@!$(PYTHON)!" \
	  | sed -e "s!@PYTHONVERSION@!$(PYTHONVERSION)!" \
	> $@


scripts/pyhep-pythonpath-install: \
			scripts/pyhep-pythonpath-install.in
	cat $^ \
	  | sed -e "s!@PYTHON@!$(PYTHON)!" \
	  | sed -e "s!@PYTHONVERSION@!$(PYTHONVERSION)!" \
	> $@


py/hep/config.py-install: \
			py/hep/config.py.in
	cat $^ | sed -e "s!@VERSION@!$(VERSION)!" > $@


$(DATADIR)/pdt.pickle:	$(DATADIR)/pdt.dat
	PYTHONPATH=$(PYTHONPATH) \
          $(PYTHON) scripts/make_particle_data.py $^ $@


#-----------------------------------------------------------------------
# Local variables:
# mode: Makefile
# fill-column: 72
# End:
