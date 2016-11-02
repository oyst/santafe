from sim import Simulator
from render import CursesRenderer

import random
import numpy
from functools import partial

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

def compound(func1, func2):
    def progn(*args):
        for arg in args:
            arg()
    return partial(progn, func1, func2)

def condition(cond):
    def _cond(out1, out2):
        return lambda: out1() if cond() else out2()
    return _cond

def evaluate(individual):
    routine = gp.compile(individual, pset)
    sim.run(routine)
    penalty = 1.01**len(individual)
    return sim.reward, penalty

sim = Simulator(600)
with  open("santafe_trail.txt") as trail_file:
  sim.parse_trail(trail_file)

pset = gp.PrimitiveSet("main", 0)
pset.addPrimitive(condition(sim.food_ahead), 2, name="ahead")
pset.addPrimitive(condition(sim.food_around), 2, name="around")
pset.addPrimitive(compound, 2, name="compose")
pset.addTerminal(sim.move_forward, name="fwd")
pset.addTerminal(sim.turn_left, name="left")
pset.addTerminal(sim.turn_right, name="right")

creator.create("FitnessMax", base.Fitness, weights=(5.0, -1.0))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("expr_init", gp.genFull, pset=pset, min_=1, max_=2)

# Structure initializers
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr_init)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

stats = tools.Statistics(key=lambda ind: ind.fitness.values)
stats.register("avg", numpy.mean)
stats.register("std", numpy.std)
stats.register("min", numpy.min)
stats.register("max", numpy.max)

NPOP = 50
NGEN = 10
CXPB = 0.5
MUTPB = 0.1

def main(toolbox, hof):
    log = tools.Logbook()

    pop = toolbox.population(NPOP)

    # Evaluate the initial population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    for gen in range(0, NGEN):
        # Select the offspring
        selected = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, selected))

        # Apply crossover to the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                # Only remove the fitness if crossover is applied
                del child1.fitness.values
                del child2.fitness.values

        # Apply mutation to the offspring
        for child in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(child)
                # Only remove the fitness if mutation is applied
                del child.fitness.values

        # Evaluate the individuals with invalid fitness
        for child in [ind for ind in offspring if not ind.fitness.valid]:
            child.fitness.values = toolbox.evaluate(child)

        # Replace the population
        pop[:] = offspring

        # Record the generation
        record = stats.compile(pop)
        log.record(gen=gen, **record)
        if hof is not None:
            hof.update(pop)
    return pop, log

if __name__ == "__main__":
    hof = tools.HallOfFame(1)
    pop, log = main(toolbox, hof)

    print toolbox.evaluate(hof[0])
    print hof[0]
    
    best = tools.selBest(pop, 1)[0]

    renderer = CursesRenderer()
    routine = gp.compile(best, pset)
    try:
        renderer.render(sim)
        sim.run(routine)
    finally:
        renderer.close()
