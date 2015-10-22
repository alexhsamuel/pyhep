#----------------------------------------------------------*- python -*-
#
# module hep.config
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

import os

version = "0.8.1"

# Determine the path to the PyHEP installation we're running.
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
data_dir = os.path.join(base_dir, "hep", "data")

