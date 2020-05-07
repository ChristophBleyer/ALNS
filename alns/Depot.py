from .Node import Node

class Depot(Node):
  def __init__(self, index, lat, lng, serviceDuration, schedule, serviceTime, vehicles):
        super.__init__(index, lat ,lng, serviceDuration, schedule, serviceTime)
        self._vehicles = vehicles
    

  @property
  def vehicles(self):
      return self._vehicles