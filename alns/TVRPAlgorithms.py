import numpy as np
import networkx as nx
import copy
import matplotlib.pyplot as plt
from alns.Solution import Solution
from alns.Route import Route

def _closeness(customer, depot, problem):
    distance = problem.distanceMatrix[customer.index, depot.index] + problem.distanceMatrix[depot.index, customer.index]
    affinity = _aysmmetricTansiniAffinity(customer,depot, problem)
    return distance/affinity

def _aysmmetricTansiniAffinity(serviceStop, depot, problem):
    nodesInCluster = list(depot.clusterCache)
    nodesInCluster.append(depot)
    longestTwoTravelTimes = problem.maxTravelTimeOccurences
    
    sum = 0
    for clusterNode in nodesInCluster:
        timeMsr = tansiniDTW(serviceStop, clusterNode) + problem.timeMatrix[serviceStop.index, clusterNode.index] + problem.timeMatrix[clusterNode.index, serviceStop.index]
        normalizedTimeMsr = timeMsr/(longestTwoTravelTimes[0] + longestTwoTravelTimes[1] + problem.maxTimeWindowDistance)
        sum+= np.exp(-normalizedTimeMsr)

    return (sum/len(problem.demand))


def tansiniDTW(nodei, nodej):

    if(nodei.serviceTime.latest < nodej.serviceTime.earliest):
        return nodej.serviceTime.earliest - nodei.serviceTime.latest
    elif(nodej.serviceTime.latest < nodei.serviceTime.earliest):
        return nodei.serviceTime.earliest - nodej.serviceTime.latest
    else:
        return 0



def _urgency(customer, firstDep, secDep, problem):

    if(secDep is not None):
        urgency = _closeness(customer, secDep, problem) - _closeness(customer, firstDep, problem)
    else:
        urgency = np.Infinity
    
    return urgency


def _getClosestAndSecondClosestDepot(customer, depotsWithUnsatisfiedDemand, problem):
    i = 0
    asymmetricTravelTimes = []
    while(i < len(depotsWithUnsatisfiedDemand)):
        if(_isAssignable(customer, depotsWithUnsatisfiedDemand[i], problem)):
            asymmetricTravelTimes.append(problem.distanceMatrix[customer.index, depotsWithUnsatisfiedDemand[i].index] + problem.distanceMatrix[depotsWithUnsatisfiedDemand[i].index, customer.index])
        else:
            asymmetricTravelTimes.append(np.Infinity)
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

    return temporalClusterWorkDemand, avgTravelTime


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

    nonAssignedCustomers = list(problem.demand)
    holdingVector = []
    
    assignmentStillPossible = True
    # we try to assign customers to depots as long as there is a depot with unsatisfied demand left
    while (assignmentStillPossible):

        # calculate urgencies for all customers store their clostest depot
        urgencies = []
        stops = []
        bestDepotForStops = []
        for stop in nonAssignedCustomers:

            firstDep, secDep = _getClosestAndSecondClosestDepot(stop, depotsWithUnsatisfiedDemand, problem)
            
            # At least one depot (always the first one) has to be compatible with the customer otherwise we can not assign him anymore and we drive him into the holding vector.
            if(firstDep is not None):
                bestDepotForStops.append(firstDep)
                urgencies.append(_urgency(stop, firstDep, secDep, problem))
                stops.append(stop)
            else:
                holdingVector.append(stop)

        limitForDepotReached = False
        
        # if there is no unanssigned customer left or no depot left that we can add a customer to we stop the algorithm
        if(not urgencies):
            assignmentStillPossible = False

        # These customers can not be taken care of right now. This is the job of the optimization algorithm.
        for unassignableCustomer in holdingVector:
            if(unassignableCustomer in nonAssignedCustomers):
                nonAssignedCustomers.remove(unassignableCustomer)

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
        
    routes = []
    for depot in problem.depots:
        for vehicle in depot.vehicles:
            route = Route(problem, depot, vehicle)
            routes.append(route)
    
    clusteredSolution = Solution(routes, holdingVector, problem)


    if (plotClusters):
        G = nx.Graph()

        colors = []
        edgeColors = []
        labels = {}
        for depot in problem.depots:
            G.add_node(depot.index, pos=(depot.lng, depot.lat))
            colors.append('blue')
            edgeColors.append('blue')
        
        for stop in problem.demand:
            edgeColors.append('blue')
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

        nx.draw_networkx_edges(G, nx.get_node_attributes(G, 'pos'), G.edges(), edge_color=edgeColors)
        
        return G, clusteredSolution
    
    return clusteredSolution


def buildSolutionParallelStyle(solution):
    
    problem = solution.problem

    # we run the algorithm on all the depots. This should be done in parallel (in a computational sense) in future iterations
    for depot in problem.depots:
        
        # create a list for all routes of the depot
        routesForDepot = []
        for route in solution.routes:
            if(route.depot is depot):
                routesForDepot.append(route)
        
        unroutedCustomers = depot.clusterCache
        
        cheapestCostsPerCust= {}
        changedRoute = None
        while(unroutedCustomers):

            # for all unrouted customers...
            for unroutedCust in unroutedCustomers:
                
                cheapestCostPerRoute = {}
                # ...search for the cheapest insertion spot in all the routes
                for route in routesForDepot:
                    
                    # if a route has not changed we do not need to update the costs for all unrouted customers for that route since the insertion costs stay the same.
                    if(changedRoute is None or route is changedRoute):

                        insertAt = 0
                        insertionCostForRoute = []

                        # try to insert the customer in all places of the current coute and store the costs
                        while(insertAt <= len(route.stops)):

                            if(route.isAssignable(unroutedCust, insertAt)):
                                cost = 0.75 * route.getTimeBasedInsertionCost(insertAt - 1, insertAt, unroutedCust) + 0.25 * route.getIntroducedDelay(insertAt - 1, insertAt, unroutedCust)
                            else:
                                cost = np.Infinity
                            
                            insertionCostForRoute.append(cost)
                            insertAt+=1
                        
                        # store the cheapest place of the current route
                        cheapestPlaceCost = min(insertionCostForRoute)
                        
                        if(cheapestPlaceCost == np.Infinity):
                            cheapestPlace = -100
                        else:
                            cheapestPlace = insertionCostForRoute.index(cheapestPlaceCost)
                    
                        cheapestCostPerRoute[route] = [cheapestPlace, cheapestPlaceCost]
            
                # after determining the cheapest insertion place for all routes for the current customer we store the cheapest costs with a reference to that customer
                if(changedRoute is None):
                    cheapestCostsPerCust[unroutedCust] = cheapestCostPerRoute
                else:
                    cheapestCostsPerCust[unroutedCust][changedRoute] = cheapestCostPerRoute[changedRoute]
            
            
            # determine the optimal route for all customers, that is the route with the minimal cost for insertion at the cheapest place in that route
            bestFitPerCust = {}
            toDelete = []
            for unroutedCust in cheapestCostsPerCust:
                
                allOvercheapestPlaceCost = [-100, np.Infinity, None]
                
                cheapestCostForRoute = cheapestCostsPerCust[unroutedCust]

                for route in cheapestCostForRoute:
                    
                    if(cheapestCostForRoute[route][1] < allOvercheapestPlaceCost[1]):
                        allOvercheapestPlaceCost = cheapestCostForRoute[route]
                        allOvercheapestPlaceCost.append(route)
                
                # the customers that cannot be inserted anywhere they are removed from the depots cluster cache and driven into the solutions holding list.
                if (allOvercheapestPlaceCost[1] == np.Infinity):
                    del unroutedCustomers[unroutedCustomers.index(unroutedCust)]
                    toDelete.append(unroutedCust)
                    solution.unassignedRequests.append(unroutedCust)
                else:
                    bestFitPerCust[unroutedCust] = allOvercheapestPlaceCost
            
            for el in toDelete:
                del cheapestCostsPerCust[el]
            
            if(not cheapestCostsPerCust):
                return

            # the customer that maximizes the generalized regret will be inserted at the cheapest position across all routes
            regret = {}
            insertLoss = {}
            for unroutedCust in bestFitPerCust:
                
                insertLoss[unroutedCust] = 0.0
                regret[unroutedCust] = 0.0
                cheapestCostRouteList = cheapestCostsPerCust[unroutedCust]
                
                # we do not exclude the bestFitPerCust in the calculation since it will normalize to zero anyways
                for route in cheapestCostRouteList:
                    
                    costsForRoute = cheapestCostRouteList[route]
                    
                    # if we can not include a customer in a route we increment his loss. If we can include him in a route we add to the regret.
                    if(costsForRoute[1] == np.Infinity):
                        insertLoss[unroutedCust]+=1
                    else:
                        regret[unroutedCust]+= costsForRoute[1] - bestFitPerCust[unroutedCust][1]
                
                if(regret[unroutedCust] < 0):
                    raise Exception("impossible system state")
                
                # Increase the regret by the customers priority
                regret[unroutedCust]*=unroutedCust.priority

            
            
            # the customer that is inserted is one with the biggest loss. For all customers that have the same loss we insert the one with the biggest regret.
            maxLossCustomer = max(insertLoss, key=insertLoss.get)
            maxLossCustomers =  []

            for cust in insertLoss:
                if(insertLoss[cust] == insertLoss[maxLossCustomer]):
                    maxLossCustomers.append(cust)
            
            regretOnSameLossLevel = {}
            for cust in maxLossCustomers:
                regretForCust = regret[cust]
                regretOnSameLossLevel[cust] = regretForCust
            
            # if the route length is 1 meaning there is only one route for that depot or only one route left we insert the customer that has the cheapest insertion cost for that route
            if(len(routesForDepot) == 1 or max(regretOnSameLossLevel, key=regretOnSameLossLevel.get) == 0.0):

                minCosts = {}

                for cust in maxLossCustomers:
                    minCosts[cust] = bestFitPerCust[cust][1]
                
                customerToInsert = min(minCosts, key=minCosts.get)

            else:
                customerToInsert = max(regretOnSameLossLevel, key=regretOnSameLossLevel.get)

            
            del unroutedCustomers[unroutedCustomers.index(customerToInsert)]
            del cheapestCostsPerCust[customerToInsert]
            
            
            targetRoute = bestFitPerCust[customerToInsert][2]
            success = targetRoute.tryInsertServiceStop(customerToInsert, bestFitPerCust[customerToInsert][0])
            changedRoute = targetRoute

            if(not success):
                raise Exception("impossible system state")




def determineDegreeOfDestruction(problem):
    # As mentioned by Ropke and Pisinger the degree of destruction is choosen at random depending on the instance size. In this case between 10 and 50 percent.
   return round(np.random.uniform(0.1, 0.50) * len(problem.demand))

def determineDegreeOfDiversification():
    return 0.95

def randomRemoval(current, random_state):
    destroyed = copy.deepcopy(current)
    
    solutionSpace = []
    nodeToRoute = {}
    targetsPerRoute = {}
    for route in destroyed.routes:
        targetsPerRoute[route] = []
        for stop in route.stops:
            solutionSpace.append(stop)
            nodeToRoute[stop] = route

    # elements are also removed from the holding vector to drive them back into the solution space
    combinedSearchSpace = destroyed.unassignedRequests + solutionSpace

    if(len(combinedSearchSpace) != len(current.problem.demand) or len(combinedSearchSpace) != len(destroyed.problem.demand)):
        raise Exception("impossible system state")

    random_state.shuffle(combinedSearchSpace)

    destructionDegree = determineDegreeOfDestruction(destroyed.problem)
    targetsToRemove = random_state.choice(combinedSearchSpace, destructionDegree, replace=False)

    for target in targetsToRemove:
        if(target in solutionSpace):
            targetRoute = nodeToRoute[target]
            idx = targetRoute.stops.index(target)
            targetsPerRoute[targetRoute].append(idx)
        elif(target in destroyed.unassignedRequests):
            el = destroyed.unassignedRequests.pop(destroyed.unassignedRequests.index(target))
            destroyed.removalCache.append(el)
        else:
            raise Exception("impossible system state")
    

    for targetRoute in targetsPerRoute:
        if(targetsPerRoute[targetRoute]):
            removed = targetRoute.removeServiceStops(targetsPerRoute[targetRoute])
            for el in removed:
                destroyed.removalCache.append(el)

    
    if(len(destroyed.removalCache) != destructionDegree):
        raise Exception("impossible system state")

    return destroyed


def distancedBasedWorstRemoval(current, random_State):
    pass











        

        


        

        
        


            
            





        

            

        



        




        




            
            


    