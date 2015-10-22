default:		all

#-----------------------------------------------------------------------
# variables
#-----------------------------------------------------------------------

PYTHONPATH	= $(PYHEPDIR)/py

SUBDIRSALL	= $(SUBDIRS:=-all)
SUBDIRSCLEAN	= $(SUBDIRS:=-clean)
SUBDIRSTEST	= $(SUBDIRS:=-test)
SUBDIRSINSTALL	= $(SUBDIRS:=-install)

CPPFLAGS	+= -I$(PYTHONINCDIR) -I$(PYHEPDIR)/ext 
CFLAGS		+= -fpic -fno-strict-aliasing
CXXFLAGS	+= -fpic -fno-strict-aliasing
FFLAGS		+= -g -O2 -fpic

COMPILEPYTHON	= $(PYTHON) -c \
	"import py_compile; import sys; py_compile.compile(sys.argv[1]);"

#-----------------------------------------------------------------------
# rules
#-----------------------------------------------------------------------

.PHONY:			all clean install setup test distclean version \
			$(SUBDIRSALL) $(SUBDIRSCLEAN) $(SUBDIRSTEST) \
			$(SUBDIRSINSTALL)


version:
	@ echo $(VERSION)


test:
	@ for test in $(wildcard *.py); do $(TESTDRIVER) "$$test"; done


%.so:
	$(CXX) -shared $(LDFLAGS) $^ -o $@ $(LDLIBS)


$(SUBDIRSALL): \
%-all:			
	$(MAKE) -C $* all


$(SUBDIRSCLEAN): \
%-clean:		
	$(MAKE) -C $* clean


$(SUBDIRSTEST): \
%-test:		
	$(MAKE) -C $* test


$(SUBDIRSINSTALL): \
%-install:
	$(MAKE) -C $* install


depend.mk:	$(wildcard *.cc) $(wildcard *.hh)
	rm -f depend.mk
	( for f in *.cc; do \
	  $(CXX) $(CPPFLAGS) -MM $$f >> $@ || exit 1; \
	  done ) || rm -f $@


#-----------------------------------------------------------------------
# dependencies
#-----------------------------------------------------------------------

all:			$(SUBDIRSALL)

clean:			$(SUBDIRSCLEAN)

test:			$(SUBDIRSTEST)

install:		$(SUBDIRSINSTALL)

#-----------------------------------------------------------------------
# Local variables:
# mode: Makefile
# fill-column: 72
# End:
