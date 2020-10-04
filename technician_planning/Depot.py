from .Node import Node

class Depot(Node):
  def __init__(self, index, lat, lng, serviceDuration, schedule, serviceTime, vehicles):
        super().__init__(index, lat ,lng, serviceDuration, schedule, serviceTime)
        self._vehicles = vehicles
        self._temporalWorkforce = self.calculateTemporalWorkforce()
        # The cluster cache is used to assign customers to this Depot during the clustering phase
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

# Calculates the maximum working time of the fleet assigned to this Depot
  def calculateTemporalWorkforce(self):
      temporalWorkForce = 0
      for vehicle in self._vehicles:
            temporalWorkForce+= vehicle.maxOvertime
      return temporalWorkForce


