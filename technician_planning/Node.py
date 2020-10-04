class Node:
    def __init__(self, index, lat ,lng, serviceDuration, schedule, serviceTime):
        self._index = index
        self._lat = lat
        self._lng = lng
        self._serviceDuration = serviceDuration
        # The current schedule in the routing plan
        self._schedule= schedule
        # The time window
        self._serviceTime = serviceTime
    

    @property
    def index(self):
        return self._index
    
    @property
    def lat(self):
        return self._lat
    
    @property
    def lng(self):
        return self._lng

    @property
    def serviceDuration(self):
        return self._serviceDuration

    @property
    def schedule(self):
        return self._schedule
    
    @property
    def serviceTime(self):
        return self._serviceTime
 






        





