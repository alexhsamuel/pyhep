#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.mctruth
from   hep.test import compare, assert_

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# The decay below corresponds to the following tree:
# 
#   Upsilon(4S)
#    B-
#     D*0
#      D0
#       pi0
#        gamma
#        gamma
#       pi0
#        gamma
#        gamma
#       pi+
#        mu+
#        nu_mu
#       K-
#        n0
#      gamma
#     a_20
#      rho+
#       pi0
#        gamma
#        gamma
#       pi+
#      pi-
#     pi-
#      n0
#    B+
#     K'*+
#      K*0
#       pi-
#       K+
#        mu+
#        nu_mu
#      pi+
#     gamma

particle = hep.mctruth.parseDecay("[Upsilon(4S),[B-,[D*0,[D0,[pi0,[gamma],[gamma]],[pi0,[gamma],[gamma]],[pi+,[mu+],[nu_mu]],[K-,[n0]]],[gamma]],[a_20,[rho+,[pi0,[gamma],[gamma]],[pi+]],[pi-]],[pi-,[n0]]],[B+,[K'*+,[K*0,[pi-],[K+,[mu+],[nu_mu]]],[pi+]],[gamma]]]")

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

# Test order-independence of particles in the pattern.

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,gamma,K'*+],B-]")
assert_(hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),B-,[B+,gamma,K'*+]]")
assert_(hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),B-,[B+,K'*+,gamma]]")
assert_(hep.mctruth.matchTree(pattern, particle))

