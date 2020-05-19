class Vehicle:
    def __init__(self, skillSet, overtimeThreshold, maxOvertime, overTimeCost):
        self._skillSet = skillSet
        self._overtimeThreshold = overtimeThreshold
        self._maxOvertime = maxOvertime
        self._overTimeCost = overTimeCost
    
    @property
    def skillSet(self):
        return self._skillSet
    
    @property
    def overtimeThreshold(self):
        return self._overtimeThreshold
    
    @property
    def maxOvertime(self):
        return self._maxOvertime
    
    @property
    def overTimeCost(self):
        return self._overTimeCost

    def canServe(self, stop):
        return stop.requirements.issubset(self.skillSet)