"""Construct a particle data pickle from a text PDT file."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import cPickle
from   hep.config import data_dir
import hep.pdt
from   os.path import join
import sys

#-----------------------------------------------------------------------
# script
#-----------------------------------------------------------------------

assert len(sys.argv) == 3
table = hep.pdt.loadPdtFile(join(data_dir, sys.argv[1]))
cPickle.dump(table, open(join(data_dir, sys.argv[2]), "w"), 1)
