#-----------------------------------------------------------------------
#
# module hep.lorentz
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Lorentz vectors and transformations."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.num import hypot
from   math import sqrt, sin, cos, pi, atan2
from   hep.ext import FourVector as Vector
from   vec import ThreeVector

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

# FIXME: Use some standard matrix implementation instead of this.

class Matrix:

    def __init__(self, num_cols, num_rows):
        self.__num_cols = int(num_cols)
        self.__num_rows = int(num_rows)
        self.__components = self.__num_cols * self.__num_rows * [ 0 ]


    num_columns = property(lambda self: self.__num_cols)
    num_rows = property(lambda self: self.__num_rows)


    def __getitem__(self, coordinates):
        col, row = coordinates
        return self.__components[col + row * self.__num_cols]


    def __setitem__(self, coordinates, value):
        col, row = coordinates
        self.__components[col + row * self.__num_cols] = value


    def __mul__(self, other):
        if isinstance(other, Matrix):
            # Matrix multiplication.
            if self.__num_cols != other.__num_rows:
                raise ValueError, "incompatible matrix sizes"
            result = Matrix(other.__num_cols, self.__num_rows)
            for c in xrange(0, other.__num_cols):
                for r in xrange(0, self.__num_rows):
                    entry = 0
                    for i in xrange(self.__num_cols):
                        entry += self[(i, r)] * other[(c, i)]
                    result[(c, r)] = entry
            return result
        else:
            # Multriply a matrix by a vector.
            if len(other) != self.__num_cols:
                raise ValueError, "incompatible matrix sizes"
            result = ()
            for r in xrange(0, self.__num_rows):
                entry = 0
                for i in xrange(self.__num_cols):
                    entry += self[(i, r)] * other[i]
                result += (entry, )
            return result


    def __str__(self):
        components = map(str, self.__components)
        length = max(map(len, components))
        format = "%%%ds " % length
        result = ""
        for r in xrange(0, self.__num_rows):
            result += "( "
            for c in xrange(0, self.__num_cols):
                result += format % self[(c, r)]
            result += ")\n"
        return result



def determinant(matrix):
    """Compute the determinant of 'matrix'."""

    # Make sure the matrix is square.
    if matrix.num_columns != matrix.num_rows:
        raise ValueError, "determinant of non-square matrix"
    # Handle the 1x1 and 2x2 cases specially.
    size = matrix.num_columns
    if size == 1:
        return matrix[(0, 0)]
    elif size == 2:
        return matrix[(0, 0)] * matrix[(1, 1)] \
               - matrix[(0, 1)] * matrix[(1, 0)]
    # Accumulate the derivitive by computing cofactors down column zero.
    det = 0
    for r in range(0, size):
        element = matrix[(0, r)]
        if element != 0:
            det += element * cofactor(matrix, 0, r) 
    return det


def cofactor(matrix, col, row):
    """Compute the '(col, row)' cofactor of 'matrix'."""

    # Make sure the matrix is square.
    if matrix.num_columns != matrix.num_rows:
        raise ValueError, "cofactor of non-square matrix" 
    size = matrix.num_columns
    # Construct the submatrix with the specified row and column
    # deleted. 
    submatrix = Matrix(size - 1, size - 1)
    for c in range(0, size - 1):
        if c < col:
            cc = c
        else:
            cc = c + 1
        for r in range(0, size - 1):
            if r < row:
                rr = r
            else:
                rr = r + 1
            submatrix[(c, r)] = matrix[(cc, rr)]
    # Compute the determinant of this submatrix, and multiply by the
    # appropriate sign factor.
    return (-1) ** (col + row) * determinant(submatrix) 


def inverse(matrix):
    """Compute the inverse of 'matrix'."""

    # Make sure the matrix is square.
    if matrix.num_columns != matrix.num_rows:
        raise ValueError, "inverse of non-square matrix" 
    size = matrix.num_columns
    # We'll need the matrix's determinant.
    det = determinant(matrix)
    # Compute the inverse.
    result = Matrix(size, size)
    for c in range(0, size):
        for r in range(0, size):
            # Each element of the inverse is the corresponding element
            # in the transpose of the adjoint matrix, i.e. the cofactor
            # with the column and row swapped, divided by the total
            # determinant. 
            result[(c, r)] = cofactor(matrix, r, c) / det
    return result        
            

#-----------------------------------------------------------------------

def makeRotationMatrix(phi, theta, psi):
    """Construct a rotation matrix.

    Returns a 4x4 matrix which rotates the space dimensions in the Euler
    angles 'phi', 'theta', and 'psi'."""

    sinph = sin(phi)
    cosph = cos(phi)
    sinth = sin(theta)
    costh = cos(theta)
    sinps = sin(psi)
    cosps = cos(psi)
    matrix = Matrix(4, 4)
    matrix[(0, 0)] = 1.0
    matrix[(1, 1)] =   cosph * costh * cosps - sinph * sinps
    matrix[(1, 2)] = - cosph * costh * sinps - sinph * cosps
    matrix[(1, 3)] =   cosph * sinth
    matrix[(2, 1)] =   sinph * costh * cosps + cosph * sinps
    matrix[(2, 2)] = - sinph * costh * sinps + cosph * cosps
    matrix[(2, 3)] =   sinph * sinth
    matrix[(3, 1)] = -         sinth * cosps
    matrix[(3, 2)] =           sinth * sinps
    matrix[(3, 3)] =           costh
    return matrix


def makeBoostMatrix(beta_x, beta_y, beta_z):
    """Construct a boost matrix.

    Returns a 4x4 matrix for the boost for a vector beta whose
    components are 'beta_x', 'beta_y', and 'beta_z'."""

    matrix = Matrix(4, 4)

    # Handle the zero-boost case.
    if beta_x == 0 and beta_y == 0 and beta_z == 0:
        matrix[(0, 0)] = 1
        matrix[(1, 1)] = 1
        matrix[(2, 2)] = 1
        matrix[(3, 3)] = 1
        return matrix

    # Compute beta-squared.
    betas = (beta_x, beta_y, beta_z)
    beta2 = hypot(*betas) ** 2
    if beta2 > 1:
        raise ValueError, "beta may not have magnitude greater than one"
    # Compute gamma.
    gamma = 1 / sqrt(1 - beta2)
    # Construct the boost matrix.
    matrix[(0, 0)] = gamma
    for i in (1, 2, 3):
        element = -gamma * betas[i - 1]
        matrix[(i, 0)] = element
        matrix[(0, i)] = element
    for i in (1, 2, 3):
        for j in range(i, 4):
            element = (gamma - 1) * betas[i - 1] * betas[j - 1] / beta2
            if i == j:
                element += 1
            matrix[(i, j)] = element
            matrix[(j, i)] = element
    return matrix


#-----------------------------------------------------------------------

class Transformation:
    """A Lorentz transformation."""

    def __str__(self):
        return str(self.matrix)


    def __mul__(self, other):
        """Compose two transformations."""

        return lab.Transformation(self.matrix * other.matrix)

    
    def __xor__(self, other):
        """Apply the transformation to a four-vector."""

        t, x, y, z = self.matrix * other.coordinates
        return lab.Vector(t, x, y, z, other.__class__)



class IdentityTransformation(Transformation):
    """The identity four-vector transformation."""

    def __init__(self):
        # Construct a 4x4 identity matrix.
        matrix = Matrix(4, 4)
        for i in xrange(0, 4):
            matrix[(i, i)] = 1
        self.matrix = matrix


    def __mul__(self, other):
        return other


    def __xor__(self, other):
        return other



#-----------------------------------------------------------------------

class Momentum(Vector):
    """A momentum four-vector."""


    """Return the invariant mass."""
    mass = Vector.norm


    def __get_rest_frame(self):
        en, px, py, pz = self.coordinates
        return Frame(lab.Boost(-px / en, -py / en, -pz / en))

    """Return the rest frame of a particle with this momentum."""
    rest_frame = property(__get_rest_frame)
    


class Frame:
    """A reference frame."""
    
    def __init__(self, transformation, name=None):
        """Construct a new reference frame.

        'transformation' -- The Lorentz transformation from the lab
        frame to the new frame.

        'name' -- An optional name for this frame."""

        self.transformation = transformation
        # Boosting the coordinate system is contravariant.
        self.__inverse_matrix = transformation.matrix
        self.__matrix = inverse(self.__inverse_matrix)
        self.__name = name


    def __repr__(self):
        if self.__name is None:
            name = "at 0x%x" % id(self)
        else:
            name = "" + repr(self.__name)
        return "<Frame %s>" % name


    def __str__(self):
        if self.__name is None:
            return "frame at 0x%x" % id(self)
        else:
            return "frame '%s'" % str(self.__name)


    def coordinatesOf(self, vector):
        """Return the four coordinates of 'vector' in this frame."""
        
        return self.__matrix * vector.coordinates


    def __getitem__(self, vector):
        return self.coordinatesOf(vector)


    def spacePartOf(self, vector):
        """Return the space part of 'vector' in this frame.

        returns -- A three vector of its space part."""

        t, x, y, z = self.coordinatesOf(vector)
        return ThreeVector(x, y, z)


    def partsOf(self, vector):
        """Return the time and space parts of 'vector' in this frame.

        returns -- The time component of 'vector' and a three vector of
        its space part."""

        t, x, y, z = self.coordinatesOf(vector)
        return t, ThreeVector(x, y, z)


    def energy(self, p4):
        return self.coordinatesOf(p4)[0]


    def momentum(self, p4):
        return self.spacePartOf(p4)


    def Vector(self, t, x, y, z, class_=Vector):
        """Construct a four-vector.

        't', 'x', 'y', 'z' -- The four coordinates of the vector in this
        frame.

        'class_' -- The subclass of 'Vector' to create."""

        t, x, y, z = self.__inverse_matrix * (t, x, y, z)
        return lab.Vector(t, x, y, z, class_)


    def Momentum(self, energy, p_x, p_y, p_z):
        """Construct a momentum four-vector.

        'energy' -- The energy in this frame.

        'p_x', 'p_y', 'p_z' -- The three-momentum in this frame."""

        return self.Vector(energy, p_x, p_y, p_z, class_=Momentum)


    def Transformation(self, matrix):
        """Construct a Lorentz transformation.

        returns -- The transformation whose matrix representation in
        this frame is 'matrix'."""

        return lab.Transformation(
            self.__inverse_matrix * matrix * self.__matrix)


    def Boost(self, beta_x, beta_y, beta_z):
        """Construct a Lorentz boost.

        returns -- The transformation consisting of boosting by
        '(beta_x, beta_y, beta_z)' in this frame."""

        return self.Transformation(makeBoostMatrix(beta_x, beta_y, beta_z))


    def Rotation(self, phi, theta, psi):
        """Construct a rotation.

        returns -- The transformation consisting of rotating by the
        Euler angles '(phi, theta, psi)' in this frame."""

        return self.Transformation(makeRotationMatrix(phi, theta, psi))



class LabFrame(Frame):
    """The canonical lab frame.

    This is the frame relative to which all other frames are specified.

    Always use the 'lab' singleton instance of this class."""

    # The coordinates of four-vectors and the matrix elements of
    # transformations are specified in this frame.  Redefine methods to
    # use these directly.

    def __init__(self):
        Frame.__init__(self, IdentityTransformation())


    def __repr__(self):
        return "<LabFrame>"


    def __str__(self):
        return "lab frame"


    def coordinatesOf(self, vector):
        return vector.coordinates


    def Vector(self, t, x, y, z, class_=Vector):
        result = class_(t, x, y, z)
        return result


    def Transformation(self, matrix):
        result = Transformation()
        result.matrix = matrix
        return result



"""The lab frame."""
lab = LabFrame()

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def twoBodyDecayMomentum(mass_a, mass_b, mass_c):
    """Return the decay momentum for a two-body decay.

    'mass_a' -- The mass of the decaying particle.

    'mass_b', 'mass_c' -- The masses of the decay products.

    returns -- The magnitude of the momentum of each the decay products in
    the rest frame of the decaying particle."""

    if mass_a < mass_b + mass_c:
        raise ValueError, \
              "parent's mass cannot be less than sum of children's"
    return sqrt(  (mass_a - mass_b - mass_c)
                * (mass_a + mass_b - mass_c)
                * (mass_a - mass_b + mass_c)
                * (mass_a + mass_b + mass_c)) / (2 * mass_a)


def azimuth(p4, frame=lab):
    """Returns the 3D azimuthal angle 'arctan(hypot(x, y) / z)'."""

    t, x, y, z = frame.coordinatesOf(p4)
    return atan2(sqrt(x * x + y * y), z)


def cos_azimuth(p4, frame=lab):
    """Returns the cosine of 'azimuth'."""

    t, x, y, z = frame.coordinatesOf(p4)
    return z / sqrt(x * x + y * y + z * z)


#-----------------------------------------------------------------------
# test stuff
#-----------------------------------------------------------------------

if __name__ == "__main__":
    from   random import random

    mass_Ups = 10.575
    mass_B0 = 5.2794

    cm_frame = Frame(lab.Boost(0, 0, 0.56), name="CM")
    p4_Ups = cm_frame.Momentum(mass_Ups, 0, 0, 0)

    decay_angles = random() * 2 * pi, random() * pi, random() * 2 * pi
    decay_rotation = cm_frame.Rotation(*decay_angles)

    momentum_B0 = twoBodyDecayMomentum(mass_Ups, mass_B0, mass_B0)
    energy_B0 = hypot(momentum_B0, mass_B0)
    p4_B0 = decay_rotation \
            ^ cm_frame.Momentum(energy_B0, 0, 0, momentum_B0)
    p4_B0bar = decay_rotation \
               ^ cm_frame.Momentum(energy_B0, 0, 0, -momentum_B0)

    print "B0 and B0bar coordinates in %s:" % lab
    print "(%.4f, %.4f, %.4f, %.4f)" % lab.coordinatesOf(p4_B0)
    print "(%.4f, %.4f, %.4f, %.4f)" % lab.coordinatesOf(p4_B0bar)
    print "B0 and B0bar coordinates in %s:" % cm_frame
    print "(%.4f, %.4f, %.4f, %.4f)" % cm_frame.coordinatesOf(p4_B0)
    print "(%.4f, %.4f, %.4f, %.4f)" % cm_frame.coordinatesOf(p4_B0bar)
    print "Reconstructed Upsilon(4S) mass =", (p4_B0 + p4_B0bar).mass
