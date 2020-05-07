class Node:
    def __init__(self, index, lat ,lng, serviceDuration, schedule, serviceTime):
        self._index = index
        self._lat = lat
        self._lng = lng
        self._serviceDuration = serviceDuration
        self._schedule= schedule
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
    
    def tryUpdateHorizon(self, pred, travelTime):
        newArrival = pred.departureTime + travelTime

        if newArrival >= self.serviceTime.latest:
            return False
        
        self.schedule.arrivalTime = newArrival
        
        pause = 0

        if self.schedule.arrivalTime < self.serviceTime.earliest:
            pause = self.serviceTime.earliest - self.schedule.arrivalTime
        
        self.schedule.waitingTime = pause
        self.schedule.departureTime = self.schedule.arrivalTime + self.schedule.waitingTime + self.serviceDuration

        self.schedule.departureIncludesBreak = False
        return True
    
    def injectLunchBreak(self, lunchDuration):
        
        # If the lunch time is bigger then the time paused by the driver, the lunch is taken immediately on arrival. Because ... why wait?
        if lunchDuration > self.schedule.waitingTime:
            timeOnSite = lunchDuration + self.serviceDuration

            # ... well waiting is neccessary if our break would cause us to be late. We assume that we pause - say hello -  then take our break on site.
            if self.schedule.arrivalTime + lunchDuration > self.serviceTime.latest:
                timeOnSite = lunchDuration + self.serviceDuration + self.schedule.waitingTime
            else:
                self.schedule.waitingTime = 0

            self.schedule.departureTime =  self.schedule.arrivalTime + timeOnSite
        
        self.schedule.departureIncludesBreak = True




        





