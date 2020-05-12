from alns.Solution import Solution
from alns.Problem import Problem
from alns.Depot import Depot
from alns.Vehicle import Vehicle

def closeness(customer, depot):
    pass

def tansiniAffinity():
    pass

def urgency(customer):
    pass

def getClostestAndSecondClostestDepot(customer):
    pass


def parallelUrgencyAssignment(problem, plotClusters = False):
    depotsWithUnsatisfiedDemand = problem.depots
    nonAssignedCustomers = problem.demand
    
    # we try to assign customers to depots as long as there is a depot with unsatisfied demand left
    while (depotsWithUnsatisfiedDemand):
        
        # calculate urgencies for all customers
        urgencies = []
        stops = []
        for stop in nonAssignedCustomers:
            urgencies.append(urgency(stop))
            stops.append(stop)

        limitForDepotReached = False
        # until we have customers and no free depot reached it's limit we assign customers according to the urgencies.
        # if a depot has reached the capacity limit we stop because the urgencies need to be recalculated because the clustering environment has changed.
        while (depotsWithUnsatisfiedDemand and not limitForDepotReached):
            maxUrgencyIndex = urgencies.index(max(urgencies))

    