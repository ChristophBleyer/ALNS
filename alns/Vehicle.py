class Vehicle:
    def __init__(self, skillSet, overtimeThreshold, maxOvertime):
        self._skillSet = skillSet
        self._overtimeThreshold = overtimeThreshold
        self._maxOvertime = maxOvertime
    
    @property
    def skillSet(self):
        return self._skillSet
    
    @property
    def overtimeThreshold(self):
        return self._overtimeThreshold
    
    @property
    def maxOvertime(self):
        return self._maxOvertime

    def canServe(self, stop):
        return stop.requirements.issubset(self.skillSet)