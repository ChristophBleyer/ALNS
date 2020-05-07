import numpy as np
import csv
import networkx as nx

class Problem:

    def __init__(self, instanceFilePath):

        depots, demand, timeMatrix, distanceMatrix, lunchBreak, lunchDuration = self.readInstance(self, instanceFilePath)

        self._depots = depots
        self._demand = demand
        self._timeMatrix = timeMatrix
        self._distanceMatrix = distanceMatrix
        self._lunchBreak = lunchBreak
        self._lunchDuration = lunchDuration

        self._servcieMap = self.buildServiceMap()
        self._maxServiceStartDistance = self.calculateMaxServiceStartDistance()
        self._maxTravelTimeOccurences = self.calculcateMaxTravelTimeOccurences()

    
    @property
    def depots(self):
        return self._depots
    
    @property
    def demand(self):
        return self._demand
    
    @property
    def timeMatrix(self):
        return self._timeMatrix

    @property
    def distanceMatrix(self):
        return self._distanceMatrix

    @property
    def lunchBreak(self):
        return self._lunchBreak
    
    @property
    def lunchDuration(self):
        return self._lunchDuration
    
    @property
    def servcieMap(self):
        return self._servcieMap
    
    @property
    def maxServiceStartDistance(self):
        return self._maxServiceStartDistance
    
    @property
    def maxTravelTimeOccurences(self):
        return self._maxTravelTimeOccurences


    def readInstance(self, instanceFilepath):
        pass

    def buildServiceMap(self):
        pass

    def calculcateMaxTravelTimeOccurences(self):
        pass

    def calculateMaxServiceStartDistance(self):
        pass

    def plot(self):
        pass