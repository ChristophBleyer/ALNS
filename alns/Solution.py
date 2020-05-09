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
    
    def calculateRequestCoverageScore(self):
        requestCoverageScore = 0

        for route in self.routes:
            for servedCustomer in route.stops:
                requestCoverageScore+= servedCustomer.priority
        
        return requestCoverageScore

    
    def calculateTotalDistanceTraveled(self):
        totalDistanceTraveled = 0

        for route in self.routes:
            totalDistanceTraveled+= route.calculateDistanceTraveled()

        return totalDistanceTraveled
    
    def calculateDeployedFleetCost(self):
        deployedFleetCost = 0
        
        # if a there is no ServiceStop in the route the vehicle is not deployed
        for route in self.routes:
            if(len(route.stops) > 0):
                deployedFleetCost+=1
        
        return deployedFleetCost
    
    def calculateTotalOvertime(self):
        totalOvertime = 0

        for route in self.routes:
            totalOvertime+= route.calculateOvertime()
        
        return totalOvertime
    
    def objective(self):
        return [self.calculateRequestCoverageScore(), self.calculateTotalDistanceTraveled(), self.calculateTotalOvertime(), self.calculateDeployedFleetCost()]
    
    def toGraph(self):
        G = self.problem.plot()

        for route in self.routes:
            waypoints = route.stops

            G.add_edge(route.depot.index, route.waypoints[0].index, weight=self.problem.distanceMatrix[route.depot.index, route.waypoints[0].index])
            G.add_edge(route.waypoints[len(waypoints) - 1].index, route.depot.index, weight=self.problem.distanceMatrix[route.waypoints[len(waypoints) - 1].index, route.depot.index])

            i = 0
            while (i < len(waypoints) - 1):
                G.add_edge(waypoints[i].index, waypoints[i + 1].index, weight=self.problem.distanceMatrix[waypoints[i].index, waypoints[i + 1].index])
                i+=1
        

        nx.draw_networkx_edges(G, nx.get_node_attributes(G, 'pos'), G.edges())
        nx.draw_networkx_edge_labels(G, nx.get_node_attributes(G, 'pos'), nx.get_edge_attributes(G,'weight'), font_size=6)
        
        return G
            


    


        





