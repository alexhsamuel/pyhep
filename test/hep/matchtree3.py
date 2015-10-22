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

# Test checking of subdecays.

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,K'*+,gamma],B-]")
assert_(hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,K'*+,gamma,gamma],B-]")
assert_(not hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,K'*+],B-]")
assert_(not hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,K'*+,gamma],pi0,B-]")
assert_(not hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+,K'*+,gamma]]")
assert_(not hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),[B+],B-]")
assert_(not hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S),B+,[B-,D*0,a_20,pi-]]")
assert_(hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("[Upsilon(4S)]")
assert_(not hep.mctruth.matchTree(pattern, particle))

pattern = hep.mctruth.parseDecay("Upsilon(4S)")
assert_(hep.mctruth.matchTree(pattern, particle))

