
class Route:
    def __init__(self, problem, depot, vehicle):
        self._problem = problem
        self._depot = depot
        self._vehicle = vehicle
        self._stops = []
    
    @property
    def problem(self):
        return self._problem
    
    @property
    def depot(self):
        return self._depot
    
    @property
    def vehicle(self):
        return self._vehicle
    
    @property
    def stops(self):
        return self._stops
    
    def calculateOvertime(self):
        # lunch breaks are injected in the following calculations already
        
        workTime = 0
        i = 0
        # working time: every nodes service time on site and the time it is waiting in addition to the travel time to the next customer
        while(i < len(self.stops) - 1):
            workTime+= stops[i].serviceDuration + stops[i].schedule.waitingTime + self.problem.timeMatrix[stops[i].index, stops[i + 1].index]
            i+=1
        
        # the travel time from the departure from the depot to the first node is working time as well
        workTime+= self.problem.timeMatrix[depot.index, stops[0].index]
        
        # working time from the last node including its traveltime back to the depot
        workTime+= stops[len(self.stops) - 1].serviceDuration + stops[len(self.stops) - 1].schedule.waitingTime + self.problem.timeMatrix[stops[len(self.stops) - 1].index, depot.index]
    
        return workTime
        
    

