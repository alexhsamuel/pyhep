include ../standard.mk
include ../config.mk

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

PAPER		= letter
MKHOWTO		= $(PYTHON) tools/mkhowto
ADDRESS		= "<tt>alex@alexsamuel.net</tt>"

TEXFILES	= $(wildcard *.tex)

.PHONY: apidocs

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

clean:
	rm -f pyhep.pdf
	rm -rf html/pyhep


install:		pyhep.pdf html/pyhep/index.html
	$(INSTALL) -d $(INSTALLDOCDIR)
	$(INSTALLDATA) pyhep.pdf $(INSTALLDOCDIR)/pyhep-$(VERSION).pdf
	$(INSTALL) -d $(INSTALLDOCDIR)/html
	$(INSTALLDATA) html/pyhep/*.{html,txt,gif,css} \
	  $(INSTALLDOCDIR)/html
	$(INSTALL) -d $(INSTALLDOCDIR)/html/icons
	$(INSTALLDATA) html/icons/*.{png,gif} \
	  $(INSTALLDOCDIR)/html/icons


%.dvi:			%.tex $(TEXFILES)
	$(MKHOWTO) --paper=$(PAPER) --dvi


%.ps:			%.tex $(TEXFILES)
	$(MKHOWTO) --paper=$(PAPER) --ps $<


%.pdf:			%.tex $(TEXFILES)
	$(MKHOWTO) --paper=$(PAPER) --pdf $<


html/%/index.html:	%.tex $(TEXFILES)
	mkdir -p html/$*
	$(MKHOWTO) --html \
	  --address $(ADDRESS) \
          --dvips-safe \
	  --dir html/$* \
	  --iconserver icons/ \
          $<

          # --about html/stdabout.dat \
	  # --up-title "Python Documentation Index" \
          # --up-link ../index.html \
	  # --global-module-index "../modindex.html" \


apidocs:
	rm -rf apidocs 
	mkdir -p apidocs
	cd apidocs && \
	  PYTHONPATH=$(PYTHONPATH) $(PYTHON) $(PYDOC) -w hep $(PYHEPDIR)/py 


#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:		html/pyhep/index.html pyhep.pdf

