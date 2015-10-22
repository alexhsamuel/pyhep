#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

import fn
import num
from   math import exp
import random

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def normalizeParameters(parameters):
    parameters = list(parameters)
    if len(parameters) < 1:
        raise TypeError, "at least one parameter must be specified"

    # Fix up the parameters list.
    for i in xrange(len(parameters)):
        parameter = parameters[i]
        
        if isinstance(parameter, str):
            parameter = (parameter, )

        # First, the parameter name.
        name = str(parameter[0])
        if len(parameter) >= 2:
            initial_value = float(parameter[1])
        else:
            initial_value = 0.0
        # Next, the step size.  If omitted or 'None', the parameter is
        # fixed. 
        if len(parameter) >= 3 and parameter[2] is not None:
            step_size = float(parameter[2])
        else:
            step_size = None
        # Next the bounds.
        if len(parameter) >= 4:
            bound_lo, bound_hi = map(float, parameter[3])
        else:
            bound_lo = 0.0
            bound_hi = 0.0

        parameters[i] = \
            (name, initial_value, step_size, (bound_lo, bound_hi))

    return parameters


def gridMinimize(function, *variables, **constants):
    parameters = dict(constants)
    best_function_value = None
    grid = [ (samples, lo, hi) for name, samples, lo, hi in variables ]
    for point in num.multigrid(*grid):
        for variable, value in zip(variables, point):
            parameters[variable[0]] = value
        function_value = function(**parameters)
        if best_function_value is None \
           or function_value < best_function_value:
            best_function_value = function_value
            best_parameters = dict(parameters)

    return best_parameters, best_function_value


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class SimulatedAnnealingMinimizer:

    initial_temperature_scale = 0.1
    initial_temperature_samples = 10
    temperature_scale_factor = 0.999
    iterations_until_rescale = 20
    step_rescale_factor = 0.5


    def __init__(self, function, parameters):
        self.function = function
        self.parameters = normalizeParameters(parameters)


    def getRandomStep(self, parameters, step_scale=1.0):
        new_parameters = dict(parameters)
        for name, initial_value, step_size, (lo, hi) in self.parameters:
            if step_size is None:
                continue
            delta = random.normalvariate(0, step_size * step_scale)
            new_parameters[name] = \
                max(lo, min(hi, new_parameters[name] + delta))
        new_value = self.function(**new_parameters)
        return new_parameters, new_value
        

    def minimize(self, temperature=None, target_scale=1.0e-4,
                 max_iterations=1000000, verbose=False):
        parameters = dict([ (n, v) for (n, v, s, (l, h)) in self.parameters ])
        value = self.function(**parameters)

        if temperature is None:
            temperature = self.initial_temperature_scale * max([
                abs(self.getRandomStep(parameters)[1] - value)
                for i in xrange(self.initial_temperature_samples) ])

        step_scale = 1.0
        iterations = 0
        iterations_since_improvement = 0

        best_parameters = None
        best_value = None
        iterations_since_best_improvement = 0

        while step_scale > target_scale \
              and iterations < max_iterations:

            if iterations_since_best_improvement > 1000:
                parameters = best_parameters
                value = best_value
                iterations_since_best_improvement = 0

            new_parameters, new_value = \
                self.getRandomStep(parameters, step_scale)

            if new_value < value:
                accept = True
            else:
                probability = exp((value - new_value) / temperature)
                if random.random() < probability:
                    accept = True
                else:
                    accept = False
            
            if accept:
                if verbose:
                    print "%6d: T=%7.1e s=%7.1e " \
                          % (iterations, temperature, step_scale),
                    ns = new_parameters.keys()
                    ns.sort()
                    for n in ns:
                        print "%7.4f" % new_parameters[n],
                    print ": %9.4f" % new_value

                value = new_value
                parameters = new_parameters
                iterations_since_improvement = 0

                if best_value is None \
                   or value < best_value:
                    best_parameters = parameters
                    best_value = value
                    iterations_since_best_improvement = 0
            else:
                iterations_since_improvement += 1
                if iterations_since_improvement \
                   > self.iterations_until_rescale:
                    step_scale *= self.step_rescale_factor
                    iterations_since_improvement = 0

            temperature *= self.temperature_scale_factor
            iterations += 1
            iterations_since_best_improvement += 1

        return best_parameters, best_value



