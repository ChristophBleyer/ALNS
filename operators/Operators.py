import numpy as np
import networkx as nx
import copy
import random
import matplotlib.pyplot as plt
from technician_planning.Solution import Solution
from technician_planning.Route import Route


# global operator parameters
degreeOfDiversification = 10
destructionRange = [0.2, 0.4]
worstRemovalWeights = [0.75, 0.25]
holdingListRemoval = 0.5
relatednessWeights = [3,1,5]


def determineDegreeOfDestruction(problem):
    # As mentioned by Ropke and Pisinger the degree of destruction is choosen at random depending on the instance size. In this case between 10 and 50 percent.
   return round(np.random.uniform(destructionRange[0], destructionRange[1]) * len(problem.demand))

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


def greedyInsertion(current, random_state):
    
    removalCacheNotEmpty = current.removalCache
    changedRoute = None
    cheapestCostsPerCust= {}
    
    while(removalCacheNotEmpty):

         # for all unrouted customers...
            for unroutedCust in current.removalCache:
                
                cheapestCostPerRoute = {}
                # ...search for the cheapest insertion spot in all the routes
                for route in current.routes:
                    
                    # if a route has not changed we do not need to update the costs for all unrouted customers for that route since the insertion costs stay the same.
                    if(changedRoute is None or route is changedRoute):

                        insertAt = 0
                        insertionCostForRoute = []

                        # try to insert the customer in all places of the current route and store the costs
                        while(insertAt <= len(route.stops)):
                            
                            metadata = {}
                            cost = np.Infinity

                            if(route.isAssignable(unroutedCust, insertAt, metadata)):
                                cost = metadata["overtimeCost"] + metadata["distanceTraveledCost"] - unroutedCust.profitForcast

                            
                            insertionCostForRoute.append(cost)
                            insertAt+=1
                        
                        # store the cheapest place of the current route
                        s = sorted(insertionCostForRoute)
                        cheapestPlaceCost = s[0]
                        
                        if(cheapestPlaceCost == np.Infinity):
                            cheapestPlace = -100
                        else:
                            cheapestPlace = insertionCostForRoute.index(cheapestPlaceCost)
                    
                        cheapestCostPerRoute[route] = [cheapestPlace, cheapestPlaceCost, route, unroutedCust]
            
                # after determining the cheapest insertion place for all routes for the current customer we store the cheapest costs with a reference to that customer
                if(changedRoute is None):
                    cheapestCostsPerCust[unroutedCust] = cheapestCostPerRoute
                else:
                    cheapestCostsPerCust[unroutedCust][changedRoute] = cheapestCostPerRoute[changedRoute]
            

            # determine the optimal route for all customers, that is the route with the minimal cost for insertion at the cheapest place in that route
            bestFitPerCust = {}
            toDelete = []
            for unroutedCust in cheapestCostsPerCust:
                
                cheapestCostForRoute = cheapestCostsPerCust[unroutedCust]
                
                toSort = []
                for route in cheapestCostForRoute:
                    toSort.append(cheapestCostForRoute[route])
                
                sortedList = sorted(toSort, key= lambda el: el[1])

                cheapest = sortedList[0]

                # the customers that cannot be inserted anywhere are removed from the removal cache and driven into the solutions holding list.
                if (cheapest[1] == np.Infinity):
                    del current.removalCache[current.removalCache.index(unroutedCust)]
                    toDelete.append(unroutedCust)
                    current.unassignedRequests.append(unroutedCust)
                else:
                    bestFitPerCust[unroutedCust] = cheapest
            
            for el in toDelete:
                del cheapestCostsPerCust[el]
            
            if(not cheapestCostsPerCust):

                if(current.removalCache):
                    raise Exception("impossible system state")
                
                return current
            
            # greedy insert: choose the cheapest insert
            cheapestOverall = []
            for potentialInsert in bestFitPerCust:
                cheapestOverall.append(bestFitPerCust[potentialInsert])
            
            s = sorted(cheapestOverall, key= lambda el: el[1])

            targetInsert = s[0]
            del current.removalCache[current.removalCache.index(targetInsert[3])]
            del cheapestCostsPerCust[targetInsert[3]]
            
            targetRoute = targetInsert[2]
            success = targetRoute.tryInsertServiceStop(targetInsert[3], targetInsert[0])
            changedRoute = targetRoute

            if(not success):
                raise Exception("impossible system state")
    
    return current


def k_regretInsertion(current, random_state):
    removalCacheNotEmpty = current.removalCache
    changedRoute = None
    cheapestCostsPerCust= {}
    
    while(removalCacheNotEmpty):

         # for all unrouted customers...
            for unroutedCust in current.removalCache:
                
                cheapestCostPerRoute = {}
                # ... search for the cheapest insertion spot in all the routes
                for route in current.routes:
                    
                    # if a route has not changed we do not need to update the costs for all unrouted customers for that route since the insertion costs stay the same.
                    if(changedRoute is None or route is changedRoute):

                        insertAt = 0
                        insertionCostForRoute = []

                        # try to insert the customer in all places of the current route and store the costs
                        while(insertAt <= len(route.stops)):
                            
                            metadata = {}
                            cost = np.Infinity

                            if(route.isAssignable(unroutedCust, insertAt, metadata)):
                                cost = metadata["overtimeCost"] + metadata["distanceTraveledCost"]

                            
                            insertionCostForRoute.append(cost)
                            insertAt+=1
                        
                        # store the cheapest place of the current route
                        s = sorted(insertionCostForRoute)
                        cheapestPlaceCost = s[0]
                        
                        if(cheapestPlaceCost == np.Infinity):
                            cheapestPlace = -100
                        else:
                            cheapestPlace = insertionCostForRoute.index(cheapestPlaceCost)
                    
                        cheapestCostPerRoute[route] = [cheapestPlace, cheapestPlaceCost, route, unroutedCust]
            
                # after determining the cheapest insertion place for all routes for the current customer we store the cheapest costs with a reference to that customer
                if(changedRoute is None):
                    cheapestCostsPerCust[unroutedCust] = cheapestCostPerRoute
                else:
                    cheapestCostsPerCust[unroutedCust][changedRoute] = cheapestCostPerRoute[changedRoute]
            

            # determine the optimal route for all customers, that is the route with the minimal cost for insertion at the cheapest place in that route
            bestFitPerCust = {}
            toDelete = []
            for unroutedCust in cheapestCostsPerCust:
                
                cheapestCostForRoute = cheapestCostsPerCust[unroutedCust]
                
                toSort = []
                for route in cheapestCostForRoute:
                    toSort.append(cheapestCostForRoute[route])
                
                sortedList = sorted(toSort, key= lambda el: el[1])

                cheapest = sortedList[0]

                # the customers that cannot be inserted anywhere are removed from the removal cache and driven into the solutions holding list.
                if (cheapest[1] == np.Infinity):
                    del current.removalCache[current.removalCache.index(unroutedCust)]
                    toDelete.append(unroutedCust)
                    current.unassignedRequests.append(unroutedCust)
                else:
                    bestFitPerCust[unroutedCust] = cheapest
            
            for el in toDelete:
                del cheapestCostsPerCust[el]
            
            if(not cheapestCostsPerCust):

                if(current.removalCache):
                    raise Exception("impossible system state")
                
                return current
            
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

            # the customer that is inserted is one with the biggest loss. For all customers that have the same loss we insert the one with the biggest added regret that is the regret plus the cost for not inserting that customer
            maxLossCustomer = max(insertLoss, key=insertLoss.get)
            maxLossCustomers =  []

            for cust in insertLoss:
                if(insertLoss[cust] == insertLoss[maxLossCustomer]):
                    maxLossCustomers.append(cust)
            
            
            lastRoute = False
            addedRegretOnSameLossLevel = {}
            for cust in maxLossCustomers:

                if(regret[cust] == 0.0):
                    lastRoute = True
                elif(lastRoute and regret[cust] != 0.0):
                    raise Exception("impossible system state")

                addedRegretForCust = regret[cust] + cust.profitForcast
                addedRegretOnSameLossLevel[cust] = addedRegretForCust
            
            if(not lastRoute):
                customerToInsert = max(addedRegretOnSameLossLevel, key=addedRegretOnSameLossLevel.get)
            else:
                
                # if we are on the last route we insert the customer where the cost penality for not inserting him is the highest of those we insert the one with the the cheapest insert cost
                
                customerWithMaxRegret= max(addedRegretOnSameLossLevel, key=addedRegretOnSameLossLevel.get)

                customerToInsert = customerWithMaxRegret
                for cust in addedRegretOnSameLossLevel:
                    if(addedRegretOnSameLossLevel[cust] == addedRegretOnSameLossLevel[customerToInsert]):
                        if(bestFitPerCust[cust][1] < bestFitPerCust[customerToInsert][1]):
                            customerToInsert = cust

            
            del current.removalCache[current.removalCache.index(customerToInsert)]
            del cheapestCostsPerCust[customerToInsert]
            
            
            targetRoute = bestFitPerCust[customerToInsert][2]
            success = targetRoute.tryInsertServiceStop(customerToInsert, bestFitPerCust[customerToInsert][0])
            changedRoute = targetRoute

            if(not success):
                print(len(removalCacheNotEmpty))
                print(len(cheapestCostsPerCust))
                print(lastRoute)
                raise Exception("impossible system state")
    
    return current


def distancedBasedWorstRemoval(current, random_state):
    
    destroyed = copy.deepcopy(current)
    destructionDegree = determineDegreeOfDestruction(destroyed.problem)

    changedRoute = None
    removed = 0
    costsPerRoute = {}

    while(removed < destructionDegree):

        # ...search for most expensive spots in all the routes
        for route in destroyed.routes:
            
            # if a route has not changed we do not need to update the costs for all customers in that route since the costs stays the same.
            if(changedRoute is None or route is changedRoute):

                targetIdx = 0
                insertionCostForRoute = []

                # store the costs for every node 
                while(targetIdx < len(route.stops)):
                    
                    cost = route.getDistanceBasedDetour(targetIdx)
                    
                    insertionCostForRoute.append([targetIdx, cost, route])
                    targetIdx+=1
                
                # store the cheapest place of the current route
            
                costsPerRoute[route] = insertionCostForRoute
        
        # select the amount of customers from the holding list
        numCustsFromHolding = int(round(holdingListRemoval * len(destroyed.unassignedRequests)))
        targetsOnHoldToRemove = random_state.choice(destroyed.unassignedRequests, numCustsFromHolding, replace=False)

        descendendCost = []

        for route in costsPerRoute:
            descendendCost.extend(costsPerRoute[route])
        
        # sort by cost descending
        sortedCosts = sorted(descendendCost, key= lambda el: el[1], reverse=True)

        # insert customers from the holding list at random positions

        for onHoldCust in targetsOnHoldToRemove:
            sortedCosts.insert(random.randrange(0, len(sortedCosts)-1), onHoldCust)

        # choose a customer to remove
        diversificationBaseFactor = random_state.uniform(0, 1)
        targetIdx = int((diversificationBaseFactor**degreeOfDiversification)*len(sortedCosts))
        target = sortedCosts[targetIdx]
        
        # remove the target from the holding list or the solution space and put him into the removal cache
        if(target in targetsOnHoldToRemove):
            destroyed.unassignedRequests.remove(target)
            destroyed.removalCache.append(target)
            changedRoute = -1
        else:
            targetRoute = target[2]
            targetCust = targetRoute.removeServiceStop(target[0])
            destroyed.removalCache.append(targetCust)
            changedRoute = targetRoute
    
        removed+=1
    
    if(len(destroyed.removalCache) != destructionDegree):
        raise Exception("Impossible system state")

    return destroyed


def timeBasedWorstRemoval(current, random_state):
    
    destroyed = copy.deepcopy(current)
    destructionDegree = determineDegreeOfDestruction(destroyed.problem)

    changedRoute = None
    removed = 0
    costsPerRoute = {}

    while(removed < destructionDegree):

        # ...search for most expensive spots in all the routes
        for route in destroyed.routes:
            
            # if a route has not changed we do not need to update the costs for all customers in that route since the costs stays the same.
            if(changedRoute is None or route is changedRoute):

                targetIdx = 0
                insertionCostForRoute = []

                # store the costs for every node 
                while(targetIdx < len(route.stops)):
                    
                    costFactors = route.getTimeBasedDetourAndDelayCost(targetIdx)

                    cost = (worstRemovalWeights[0] * costFactors[0]) + (worstRemovalWeights[1] * costFactors[1])
                    
                    insertionCostForRoute.append([targetIdx, cost, route])
                    targetIdx+=1
                
                # store the cheapest place of the current route
            
                costsPerRoute[route] = insertionCostForRoute
        
        # select the amount of customers from the holding list
        numCustsFromHolding = int(round(holdingListRemoval * len(destroyed.unassignedRequests)))
        targetsOnHoldToRemove = random_state.choice(destroyed.unassignedRequests, numCustsFromHolding, replace=False)

        descendendCost = []

        for route in costsPerRoute:
            descendendCost.extend(costsPerRoute[route])
        
        # sort by cost descending
        sortedCosts = sorted(descendendCost, key= lambda el: el[1], reverse=True)

        # insert customers from the holding list at random positions

        for onHoldCust in targetsOnHoldToRemove:
            sortedCosts.insert(random.randrange(0, len(sortedCosts)-1), onHoldCust)

        # choose a customer to remove
        diversificationBaseFactor = random_state.uniform(0, 1)
        targetIdx = int((diversificationBaseFactor**degreeOfDiversification)*len(sortedCosts))
        target = sortedCosts[targetIdx]
        
        # remove the target from the holding list or the solution space and put him into the removal cache
        if(target in targetsOnHoldToRemove):
            destroyed.unassignedRequests.remove(target)
            destroyed.removalCache.append(target)
            changedRoute = -1
        else:
            targetRoute = target[2]
            targetCust = targetRoute.removeServiceStop(target[0])
            destroyed.removalCache.append(targetCust)
            changedRoute = targetRoute
    
        removed+=1
    
    if(len(destroyed.removalCache) != destructionDegree):
        raise Exception("Impossible system state")

    return destroyed


def relatedness(stopA, stopB, problem):

    timeWindowLengthA = (stopA.serviceTime.latest - stopA.serviceTime.earliest) / problem.maxTimeWindowLength
    timeWindowLengthB = (stopB.serviceTime.latest - stopB.serviceTime.earliest) / problem.maxTimeWindowLength

    travelTimeScore = (problem.timeMatrix[stopA.index, stopB.index] + problem.timeMatrix[stopB.index, stopA.index]) / (problem.maxTravelTimeOccurences[0] + problem.maxTravelTimeOccurences[1])
    timeWindowStartScore = np.abs(stopA.serviceTime.earliest - stopB.serviceTime.earliest) / problem.maxServiceStartDistance
    timeWindowLengthScore = np.abs(timeWindowLengthA - timeWindowLengthB)
    serviceDurationScore = np.abs((stopA.serviceDuration / problem.maxServiceTime) - (stopB.serviceDuration / problem.maxServiceTime))

    vehicleAffinityScore = 1 - ( len(list(set(problem.serviceMap[stopA.index]).intersection(problem.serviceMap[stopB.index]))) / (min([len(problem.serviceMap[stopA.index]), len(problem.serviceMap[stopB.index])])) )

    relatedness = relatednessWeights[0] * travelTimeScore + relatednessWeights[1] * (timeWindowStartScore + timeWindowLengthScore + serviceDurationScore) + relatednessWeights[2] * vehicleAffinityScore

    if(not (0 <= relatedness <= relatednessWeights[0] + 3 * relatednessWeights[1] + vehicleAffinityScore)):
        raise Exception("impossible system state")

    return relatedness


def relatedRemoval(current, random_state):

    destroyed = copy.deepcopy(current)

    destructionDegree = determineDegreeOfDestruction(destroyed.problem)

    if(destructionDegree < 1):
        return destroyed


    solutionSpace = []
    targetsPerRoute = {}
    nodeToRoute = {}
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

    relatedCustsToRemove = []

    # choose a random element from the solution space to start with
    startingTarget = random_state.choice(combinedSearchSpace, 1, replace=False)
    
    relatedCustsToRemove.append(startingTarget[0])
    combinedSearchSpace.remove(startingTarget[0])

    while(len(relatedCustsToRemove) < destructionDegree):
        
        # a random pick from the customers to remove that we will use to calculate the relatedness with every other node not removed yet
        pick = random_state.choice(relatedCustsToRemove, 1, replace=False)[0]
        relatednessToPick = []

        # calculate the relatedness
        for stop in combinedSearchSpace:
            relatednessScore = relatedness(pick, stop, destroyed.problem)
            relatednessToPick.append([relatednessScore, stop])
        
        sortedList = sorted(relatednessToPick, key= lambda el: el[0])

        # pick the most related customer controlled by a diversification factor
        diversificationBaseFactor = random_state.uniform(0, 1)
        targetIdx = int((diversificationBaseFactor**degreeOfDiversification)*len(sortedList))
        target = sortedList[targetIdx]

        relatedCustsToRemove.append(target[1])
        combinedSearchSpace.remove(target[1])
    
    # after we gathered all customers to remove we drive them into the removal cache and out of their current positions
    for target in relatedCustsToRemove:
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


            
    
    

            















        

        


        

        
        


            
            





        

            

        



        




        




            
            


    