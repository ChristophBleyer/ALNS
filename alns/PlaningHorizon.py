class PlanningHorizon:
    def __init__(self, arrivalTime, departureTime, waitingTime):
        self._arrivalTime = arrivalTime
        self._departureTime = departureTime
        self._waitingTime = waitingTime
        self._departureIncludesBreak = False
        self._TravelIncludesBreak = False

    
    @property
    def arrivalTime(self):
        return self._arrivalTime
    
    @property
    def departureTime(self):
        return self._departureTime
    
    @property
    def waitingTime(self):
        return self._waitingTime
    
    @property
    def departureIncludesBreak(self):
        return self._departureIncludesBreak
    
    @property
    def TravelIncludesBreak(self):
        return self._TravelIncludesBreak