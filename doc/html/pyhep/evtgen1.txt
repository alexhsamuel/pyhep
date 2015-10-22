import hep.evtgen
from   hep.lorentz import lab

def printParticleTree(particle, depth=0):
    indentation = depth * " "
    name = "%-12s" % particle.species
    pad = (8 - depth) * " "
    momentum = "%5.2f %5.2f %5.2f %5.2f" % lab.coordinatesOf(particle.momentum)
    print indentation + name + pad + momentum
    for child in particle.decay_products:
        printParticleTree(child, depth + 1)
    

generator = hep.evtgen.Generator("evt.pdl", "DECAY.DEC")
upsilon4s = hep.evtgen.Particle("Upsilon(4S)")
generator.decay(upsilon4s)
printParticleTree(upsilon4s)
