"""Test of basic decay-generation functionality."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.evtgen
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

num_decays = 100

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

generator = hep.evtgen.Generator()

for i in xrange(num_decays):
    # Generate a rho0 decay.
    parent = hep.evtgen.Particle("rho0")
    generator.decay(parent)
    # Make sure it's still a rho0.
    compare(parent.species, "rho0")
    # Check that it decayed to pi+ pi-.
    decay_species = [ c.species for c in parent.decay_products ]
    compare(decay_species, [ "pi+", "pi-" ])

