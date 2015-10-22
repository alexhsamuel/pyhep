#-----------------------------------------------------------------------
#
# module hep.evtgen
#
# Copyright 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""PyHEP interface to the EvtGen decay generation package."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   ext import Generator, Particle
import hep.config
import os.path

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

default_pdt_path = os.path.join(hep.config.data_dir, "pdt.dat")
default_decay_file_path = os.path.join(hep.config.data_dir, "decay.dat")

