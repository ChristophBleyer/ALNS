from .Node import Node

class Depot(Node):
  def __init__(self, index, lat, lng, serviceDuration, schedule, serviceTime, vehicles):
        super().__init__(index, lat ,lng, serviceDuration, schedule, serviceTime)
        self._vehicles = vehicles
        self._temporalWorkforce = self.calculateTemporalWorkforce()
        self._clusterCache = []

    
  @property
  def vehicles(self):
      return self._vehicles

  @property
  def temporalWorkforce(self):
      return self._temporalWorkforce

  @property 
  def clusterCache(self):
      return self._clusterCache


  def calculateTemporalWorkforce(self):
      temporalWorkForce = 0
      for vehicle in self._vehicles:
            temporalWorkForce+= vehicle.maxOvertime
      return temporalWorkForce
