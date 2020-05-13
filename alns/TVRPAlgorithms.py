import numpy as np
from alns.Solution import Solution
from alns.Problem import Problem
from alns.Depot import Depot
from alns.Vehicle import Vehicle
import networkx as nx
import matplotlib.pyplot as plt

def _closeness(customer, depot, problem):
    distance = problem.distanceMatrix[customer.index, depot.index] + problem.distanceMatrix[depot.index, customer.index]
    affinity = _aysmmetricTansiniAffinity(customer,depot, problem)
    return distance/affinity

def _aysmmetricTansiniAffinity(serviceStop, depot, problem):
    nodesInCluster = list(depot.clusterCache)
    nodesInCluster.append(depot)

    sum = 0
    for clusterNode in nodesInCluster:
        timeMsr = _tansiniDTW(serviceStop, clusterNode) + problem.timeMatrix[serviceStop.index, clusterNode.index] + problem.timeMatrix[clusterNode.index + serviceStop.index]
        sum+= np.exp(-timeMsr)

    return (sum/len(problem.demand))


def _tansiniDTW(nodei, nodej):

    if(nodei.serviceTime.latest < nodej.serviceTime.earliest):
        return nodej.serviceTime.earliest - nodei.serviceTime.latest
    elif(nodej.serviceTime.latest < nodei.serviceTime.earliest):
        return nodei.serviceTime.earliest - nodej.serviceTime.latest
    else:
        return 0



def _urgency(customer, firstDep, secDep):

    if(secDep is not None):
        urgency = _closeness(customer, secDep) - _closeness(customer, firstDep)
    else:
        urgency = np.Infinity
    
    if(urgency < 0):
        raise Exception("impossible system state")
    
    return urgency * customer.priority

def _getClosestAndSecondClosestDepot(customer, depotsWithUnsatisfiedDemand, problem):
    i = 0
    asymmetricTravelTimes = []
    while(i < len(depotsWithUnsatisfiedDemand)):
        if(_isAssignable(customer, depotsWithUnsatisfiedDemand[i], problem)):
            asymmetricTravelTimes[i] = problem.distanceMatrix[customer.index, depotsWithUnsatisfiedDemand[i].index] + problem.distanceMatrix[depotsWithUnsatisfiedDemand[i].index, customer.index]
        else:
            asymmetricTravelTimes[i] = np.Infinity
        i+=1
    
    sorted = np.sort(asymmetricTravelTimes)
    smallestTwo = sorted[0:2]

    if(smallestTwo[0] == np.Infinity):
        return None, None
    else:
        closest = smallestTwo[0]
        indexSmallest = asymmetricTravelTimes.index(closest)
        closestDepot = depotsWithUnsatisfiedDemand[indexSmallest]

        secondClosest = smallestTwo[1]
        
        if(secondClosest == np.Infinity):
            return closestDepot, None
        elif(secondClosest == closest):
            firstOccurence = False
            i = 0
            for score in asymmetricTravelTimes:
                if (score == closest and not firstOccurence):
                    firstOccurence = True
                elif(score == closest and firstOccurence):
                    return closestDepot, depotsWithUnsatisfiedDemand[i]
                i+=1
        else:
            indexSecSmallest = asymmetricTravelTimes.index(secondClosest)
            secClosestDepot = depotsWithUnsatisfiedDemand[indexSecSmallest]
            return closestDepot, secClosestDepot
        
    

def _isAssignable(customer, depot, problem):

    # if the vehicles at the depot do not have the skills for that customer the customer is not assignable to the depot
    abilityToServe = False
    for vehicle in depot.vehicles:
        if(vehicle.canServe(customer)):
            abilityToServe = True
            break

    if (not abilityToServe):
        return False

    temporalClusterWorkDemand, avgTravelTime = _calculateTemporalClusterWorkDemand(depot, problem, customer)
    return depot.temporalWorkforce >= temporalClusterWorkDemand + customer.serviceDuration + avgTravelTime



def _calculateTemporalClusterWorkDemand(depot, problem, customer):

    avgTravelTime = _calculateAvgTravelTime(depot, customer, problem)
    temporalClusterWorkDemand = 0

    # estimation of time effort to serve every customer
    for customer in depot.clusterCache:
        temporalClusterWorkDemand+= customer.serviceDuration + avgTravelTime
    
    # we need to go back to the depot n-times where n is the number of vehicles at the depot
    temporalClusterWorkDemand+= len(depot.vehicles) * avgTravelTime

    return temporalClusterWorkDemand


def _calculateAvgTravelTime(depot, customer, problem):
    clusterNodes = list(depot.clusterCache)
    clusterNodes.append(customer)
    clusterNodes.append(depot)
    
    travelSum = 0
    i = 0
    while (i < len(clusterNodes)):
        j = 0
        while(j < len(clusterNodes)):
            if(i != j):
                travelSum+= problem.timeMatrix[clusterNodes[i].index, clusterNodes[j].index]
            j+=1
        i+=1
    
    return (travelSum/len(clusterNodes))


def parallelUrgencyAssignment(problem, plotClusters = False):

    depotsWithUnsatisfiedDemand = list(problem.depots)
    depotsWithSatisfiedDemand = []

    nonAssignedCustomers = list(problem.demand)
    
    assignmentStillPossible = True
    # we try to assign customers to depots as long as there is a depot with unsatisfied demand left
    while (assignmentStillPossible):

        # calculate urgencies for all customers store their clostest depot
        urgencies = []
        stops = []
        bestDepotForStops = []
        for stop in nonAssignedCustomers:

            firstDep, secDep = _getClosestAndSecondClosestDepot(stop, depotsWithUnsatisfiedDemand, problem)
            
            # At least one depot (always the first one) has to be compatible with the customer otherweise we can not assign him 
            if(firstDep is not None):
                bestDepotForStops.append(firstDep)
                urgencies.append(_urgency(stop, firstDep, secDep))
                stops.append(stop)

        limitForDepotReached = False
        
        # if there is no unanssigned customer left or no depot left that we can add a customer to we stop the algorithm
        if(not urgencies):
            assignmentStillPossible = False

        # until we have customers and no free depot reached it's limit we assign customers according to the urgencies.
        # if a depot has reached the capacity limit for a dedicated customer we stop because the urgencies need to be recalculated because the clustering environment has changed.
        while (assignmentStillPossible and nonAssignedCustomers and not limitForDepotReached):
            
            maxUrgencyIndex = urgencies.index(max(urgencies))
            customerWithMaxUrgency = stops[maxUrgencyIndex]
            closestDepot = bestDepotForStops[maxUrgencyIndex]

            # If custer can be assigned we assign him and remove him from the non assignment set. If he can not be assigned we have to recalculate the urgencies and start over
            if(_isAssignable(customerWithMaxUrgency, closestDepot, problem)):

                closestDepot.clusterCache.append(customerWithMaxUrgency)
                nonAssignedCustomers.remove(customerWithMaxUrgency)

                # To keep track of the indices we delete that customers represantation also from all the caching done in the loop above
                del urgencies[maxUrgencyIndex]
                del stops[maxUrgencyIndex]
                del bestDepotForStops[maxUrgencyIndex]


            else:
                limitForDepotReached = True
        

    
    if (plotClusters):
        G = nx.Graph()

        colors = []
        labels = {}
        for depot in problem.depots:
            G.add_node(depot.index, pos=(depot.lng, depot.lat))
            colors.append('green')
        
        for stop in problem.demand:
            G.add_node(stop.index, pos=(stop.lng, stop.lat))
            if(stop.priority == 1.0):
                 colors.append('yellow')
            elif (stop.priority == 2.0):
                colors.append('orange')
            else:
                colors.append('red')
        
        nx.draw(G, nx.get_node_attributes(G, 'pos'), node_color=colors, with_labels=True)

        for cluster in problem.depots:

            for el in cluster.clusterCache:

                G.add_edge(cluster.index, el.index)

        nx.draw_networkx_edges(G, nx.get_node_attributes(G, 'pos'), G.edges())
        
        return G
        



        




            
            


    