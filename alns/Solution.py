import networkx as nx
import matplotlib.pyplot as plt

class Solution:

    def __init__(self, routes, unassignedRequests, problem):
        self._routes = routes
        self._unassignedRequests = unassignedRequests
        self._removalCache = []
        self._problem = problem
    
    @property
    def routes(self):
        return self._routes
    
    @property
    def unassignedRequests(self):
        return self._unassignedRequests
    
    @property
    def removalCache(self):
        return self._removalCache
    
    @property
    def problem(self):
        return self._problem
    
    def calculateRequestCoverageCost(self):
        requestCoverageCost = 0

        for cust in self.unassignedRequests:
                requestCoverageCost+= self.problem.costPerPriority[cust.priority]
        
        return requestCoverageCost

    
    def calculateTotalDistanceTraveledCost(self):
        totalDistanceTraveledCost = 0

        for route in self.routes:
            totalDistanceTraveledCost+= route.calculateDistanceTraveledCost()

        return totalDistanceTraveledCost
    
    def calculateDeployedFleetCost(self):
        deployedFleetCost = 0
        
        # if a there is no ServiceStop in the route the vehicle is not deployed
        for route in self.routes:
            if(len(route.stops) > 0):
                deployedFleetCost+=1
        
        return deployedFleetCost
    
    def calculateTotalOvertimeCost(self):
        totalOvertimeCost = 0

        for route in self.routes:
            totalOvertimeCost+= route.calculateOvertime() * route.vehicle.overTimeCost
        
        return totalOvertimeCost
    
    def objective(self):
        return self.calculateRequestCoverageCost() + self.calculateTotalDistanceTraveledCost() + self.calculateTotalOvertimeCost()
    
    def toGraph(self):
        G = self.problem.plot()

        for route in self.routes:
            waypoints = route.stops

            if(waypoints):
                G.add_edge(route.depot.index, waypoints[0].index)
                G.add_edge(waypoints[len(waypoints) - 1].index, route.depot.index)

            i = 0
            while (i < len(waypoints) - 1):
                G.add_edge(waypoints[i].index, waypoints[i + 1].index)
                i+=1
        

        nx.draw_networkx_edges(G, nx.get_node_attributes(G, 'pos'), G.edges(), arrows=True)
        
        return G
            


    


        





