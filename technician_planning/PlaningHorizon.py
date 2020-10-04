class PlanningHorizon:
    def __init__(self, arrivalTime, departureTime, waitingTime):
        self._arrivalTime = arrivalTime
        self._departureTime = departureTime
        self._waitingTime = waitingTime
        # A lunchbreak was taken before departure
        self._departureIncludesBreak = False
        # A lunchbreak was taken during travel to the next Node
        self._travelIncludesBreak = False

    
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
    def travelIncludesBreak(self):
        return self._travelIncludesBreak
    
    @arrivalTime.setter
    def arrivalTime(self, value):
        self._arrivalTime = value
    
    @departureTime.setter
    def departureTime(self, value):
        self._departureTime = value
    
    @waitingTime.setter
    def waitingTime(self, value):
        self._waitingTime = value
    
    @departureIncludesBreak.setter
    def departureIncludesBreak (self, value):
        self._departureIncludesBreak = value
    
    @travelIncludesBreak.setter
    def travelIncludesBreak(self, value):
        self._travelIncludesBreak = value