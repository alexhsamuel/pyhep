#-----------------------------------------------------------------------
#
# module hep.vec
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Vector geometry."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import math

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class ThreeVector:

    def __init__(self, x, y, z):
        self.__components = [ x, y, z ]


    def __repr__(self):
        return "%s(%s)" \
               % (self.__class__.__name__, ", ".join(map(str, self)))


    def __str__(self):
        return "(" + ", ".join(map(str, self)) + ")"


    def __len__(self):
        return 3


    def __getitem__(self, index):
        return self.__components[index]


    def __setitem__(self, index, value):
        self.__components[index] = value


    def __neg__(self):
        x, y, z = self.__components
        return self.__class__(-x, -y, -z)


    def __add__(self, other):
        return apply(self.__class__,
                     map(lambda (x, y): x + y,
                         zip(self.__components, other)))


    def __sub__(self, other):
        return apply(self.__class__,
                     map(lambda (x, y): x - y,
                         zip(self.__components, other)))


    def __mul__(self, other):
        return apply(self.__class__,
                     map(lambda c: c * other, self.__components))


    def __rmul__(self, other):
        return self.__mul__(other)


    def __div__(self, other):
        return apply(self.__class__,
                     map(lambda c: c / other, self.__components))


    def __xor__(self, other):
        """Compute an inner product.

        'other' -- A 'ThreeVector' or other 3-component sequence."""

        if len(other) != 3:
            raise TypeError, "'other' must have 3 components"
        return self.__components[0] * other[0] \
               + self.__components[1] * other[1] \
               + self.__components[2] * other[2]


    x = property(lambda self: self.__components[0])
    y = property(lambda self: self.__components[1])
    z = property(lambda self: self.__components[2])
    
    norm = property(lambda self: math.sqrt(self ^ self))
    """The two-norm."""


    def __get_direction(self):
        return self / self.norm

    direction = property(__get_direction)
    


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def angles(vector):
    """Return the polar and azimuthal angles relative to the z axis."""

    x, y, z = vector
    return math.atan2(math.hypot(x, y), z), math.atan2(y, x)


def cosAngle(vector1, vector2=ThreeVector(0, 0, 1)):
    """Return the cosine of the opening angle between two vectors.

    If only one vector is given, returns the cosine of the angle between
    it and the positive z axis."""

    return (vector1 ^ vector2) / vector1.norm / vector2.norm


def openingAngle(vector1, vector2=ThreeVector(0, 0, 1)):
    """Return the opening angle between two vectors.

    If only one vector is given, returns the angle between it and the
    positive z axis."""

    return math.acos(cosAngle(vector1, vector2))


def cross(vector1, vector2):
    """Return the cross product of two vectors."""

    x0, y0, z0 = vector1
    x1, y1, z1 = vector2
    return vector1.__class__(
        y0 * z1 - y1 * z0, z0 * x1 - z1 * x0, x0 * y1 - x1 * y0)


#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

def test():
    from util.test import check

    v = ThreeVector(1, 2, 3)
    check(v[0], 1)
    check(v[1], 2)
    check(v[2], 3)
    check((v.x, v.y, v.z), v)
    check(v.norm ** 2, 14.0)
    check(v * 2, (2, 4, 6))

    w = ThreeVector(-2, 4, 0)
    check(v + w, ThreeVector(-1, 6, 3))
    check(v * w, 6)

    check(v * (3, 2, 1), 10)
