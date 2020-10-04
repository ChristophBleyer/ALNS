from .Node import Node
import numpy as np

class ServiceStop(Node):
    def __init__(self, index, lat, lng, serviceDuration, schedule, serviceTime, priority, requirements, profitForcast):
        super().__init__(index, lat ,lng, serviceDuration, schedule, serviceTime)
        self._priority = priority
        self._requirements = requirements
        self._profitForcast = profitForcast
    
    @property
    def priority(self):
       return self._priority
    
    @property
    def requirements(self):
       return self._requirements
    
    @property
    def profitForcast(self):
       return self._profitForcast
    
    def getServiceTimeStartDistance(self, stop):
        return np.abs(self.serviceTime.earliest - stop.serviceTime.earliest)
 