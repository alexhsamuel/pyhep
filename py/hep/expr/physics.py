#-----------------------------------------------------------------------
#
# module hep.expr.physics
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Expressions specific to physics."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.expr import *
import hep.lorentz
import hep.vec

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class ThreeVectorExpr(ObjectExpr):

    def __init__(self, x, y, z):
        x, y, z = map(asExpression, (x, y, z))
        ObjectExpr.__init__(self, hep.vec.ThreeVector, x, y, z)
        


class LabFourVectorExpr(ObjectExpr):

    def __init__(self, t, x, y, z):
        t, x, y, z = map(asExpression, (t, x, y, z))
        ObjectExpr.__init__(self, hep.lorentz.Vector, t, x, y, z)



class LabFourMomentumExpr(ObjectExpr):

    def __init__(self, t, x, y, z):
        t, x, y, z = map(asExpression, (t, x, y, z))
        ObjectExpr.__init__(self, hep.lorentz.Momentum, t, x, y, z)



