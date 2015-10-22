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

# Test CC mode.

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,K'*+,gamma],B-]")
match = hep.mctruth.matchTree(pattern, particle, cc_mode=1)
assert_(match)
match = hep.mctruth.matchTree(pattern, particle, cc_mode=-1)
assert_(not match)
match = hep.mctruth.matchTree(pattern, particle, cc_mode=0)
assert_(match)

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B-,K'*-,gamma],B+]")
match = hep.mctruth.matchTree(pattern, particle, cc_mode=1)
assert_(not match)
match = hep.mctruth.matchTree(pattern, particle, cc_mode=-1)
assert_(match)
match = hep.mctruth.matchTree(pattern, particle, cc_mode=0)
assert_(match)

