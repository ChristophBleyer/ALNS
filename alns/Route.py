import copy
class Route:
    def __init__(self, problem, depot, vehicle):
        self._problem = problem
        self._depot = depot
        self._vehicle = vehicle
        self._stops = []
    
    @property
    def problem(self):
        return self._problem
    
    @property
    def depot(self):
        return self._depot
    
    @property
    def vehicle(self):
        return self._vehicle
    
    @property
    def stops(self):
        return self._stops
    
    def calculateOvertime(self):

        workTime = self.calculateWorktime()

        if (workTime > self.vehicle.overtimeThreshold):
            overTime = workTime - self.vehicle.overtimeThreshold
        else:
            overTime = 0

        return overTime
    
    def calculateWorktime(self, onInstance = None):
         
        if (onInstance is None):
            onInstance = self._stops

        workTime = 0
        i = 0
        # working time: every nodes service time on site and the time it is waiting in addition to the travel time to the next customer
        while(i < len(onInstance) - 1):
            workTime+= onInstance[i].serviceDuration + onInstance[i].schedule.waitingTime + self.problem.timeMatrix[onInstance[i].index, onInstance[i + 1].index]
            i+=1
        
        # the travel time from the departure from the depot to the first node is working time as well
        workTime+= self.problem.timeMatrix[self.depot.index, onInstance[0].index]
        
        # working time from the last node including its traveltime back to the depot
        workTime+= onInstance[len(onInstance) - 1].serviceDuration + onInstance[len(onInstance) - 1].schedule.waitingTime + self.problem.timeMatrix[onInstance[len(onInstance) - 1].index, self.depot.index]

        return workTime
    
    def calculateDistanceTraveled(self):

        distanceTraveled = 0
        i = 0
        # distance from each customer to his sucessive customer. 
        while(i < len(self._stops) - 1):
            distanceTraveled+= self.problem.distanceMatrix[self._stops[i].index, self._stops[i + 1].index]
            i+=1
        
        # distance from the depot to the first customer
        distanceTraveled+= self.problem.distanceMatrix[self.depot.index, self._stops[0].index]

        # distance from the last customer back to the depot
        distanceTraveled+= self.problem.distanceMatrix[self._stops[len(self._stops) - 1].index, self.depot.index]

        return distanceTraveled
    

    def isAssignable(self, newStop, index):
        
        # Constraint: Does this routes vehicle actually has what it takes ... ?
        if (not self.vehicle.canServe(newStop)):
            return False

        # ... if so, lets try to build the route
        seemsPossible, prototype, lunchRescedulingNeeded = self.tryGetNoLunchInsertionPrototype(index, newStop)

        if (not seemsPossible):
           # print("BUMP Because of scheduling problem")
            return False
        
        depotBreakDepartureBefore = self.depot.schedule.departureIncludesBreak
        depotBreakTravelBefore = self.depot.schedule.travelIncludesBreak

        # If there is only one node inside the Route, meaning we inserted the first one whe have to inject the pause. After that the serach takes care of it self.
        # Also if the depot is the lunch target we will do a lookup
        pauseAtDepotCanBeTakenAtTheEnd = prototype[len(prototype) - 1].schedule.departureTime + self.problem.timeMatrix[prototype[len(prototype) - 1].index, self.depot.index] <= self.problem.lunchBreak.latest
        
        if ((len(prototype) == 1) or (self.depot.schedule.departureIncludesBreak and not pauseAtDepotCanBeTakenAtTheEnd) or self.depot.schedule.travelIncludesBreak):
            lunchRescedulingNeeded = True
            self.depot.schedule.departureIncludesBreak = False
            self.depot.schedule.travelIncludesBreak = False
            
            
        # if the lunch was found somewhere across the planning horizon updates beginning at the new node, it has to be rescheduled
        if(lunchRescedulingNeeded):
            isPossible, pauseInjectedPrototype = self.tryInjectLunchBreak(prototype)
        else:
            isPossible = True
            # we already have what we need
            pauseInjectedPrototype = prototype
        
        if(not isPossible):
            # print("BUMP Because of lunch insersion problem")
            self.depot.schedule.departureIncludesBreak = depotBreakDepartureBefore
            self.depot.schedule.travelIncludesBreak = depotBreakTravelBefore
            return False
        
        workTime = self.calculateWorktime(pauseInjectedPrototype)

        if (workTime > self.vehicle.maxOvertime):
            # print("BUMP Because of overtime problem")
            self.depot.schedule.departureIncludesBreak = depotBreakDepartureBefore
            self.depot.schedule.travelIncludesBreak = depotBreakTravelBefore
            return False
        
        return True




    
    def tryInsertServiceStop(self, newStop, index):
        
        # Constraint: Does this routes vehicle actually has what it takes ... ?
        if (not self.vehicle.canServe(newStop)):
            return False

        # ... if so, lets try to build the route
        seemsPossible, prototype, lunchRescedulingNeeded = self.tryGetNoLunchInsertionPrototype(index, newStop)

        if (not seemsPossible):
            print("BUMP Because of scheduling problem")
            return False
        
        depotBreakDepartureBefore = self.depot.schedule.departureIncludesBreak
        depotBreakTravelBefore = self.depot.schedule.travelIncludesBreak

        # If there is only one node inside the Route, meaning we inserted the first one whe have to inject the pause. After that the serach takes care of it self.
        # Also if the depot is the lunch target we will do a lookup
        pauseAtDepotCanBeTakenAtTheEnd = prototype[len(prototype) - 1].schedule.departureTime + self.problem.timeMatrix[prototype[len(prototype) - 1].index, self.depot.index] <= self.problem.lunchBreak.latest
        
        if ((len(prototype) == 1) or (self.depot.schedule.departureIncludesBreak and not pauseAtDepotCanBeTakenAtTheEnd) or self.depot.schedule.travelIncludesBreak):
            lunchRescedulingNeeded = True
            self.depot.schedule.departureIncludesBreak = False
            self.depot.schedule.travelIncludesBreak = False
            
            
        # if the lunch was found somewhere across the planning horizon updates beginning at the new node, it has to be rescheduled
        if(lunchRescedulingNeeded):
            isPossible, pauseInjectedPrototype = self.tryInjectLunchBreak(prototype)
        else:
            isPossible = True
            # we already have what we need
            pauseInjectedPrototype = prototype
        
        if(not isPossible):
            print("BUMP Because of lunch insersion problem")
            self.depot.schedule.departureIncludesBreak = depotBreakDepartureBefore
            self.depot.schedule.travelIncludesBreak = depotBreakTravelBefore
            return False
        
        workTime = self.calculateWorktime(pauseInjectedPrototype)

        if (workTime > self.vehicle.maxOvertime):
            print("BUMP Because of overtime problem")
            self.depot.schedule.departureIncludesBreak = depotBreakDepartureBefore
            self.depot.schedule.travelIncludesBreak = depotBreakTravelBefore
            return False
        
        self._stops = pauseInjectedPrototype
        
        # update the depot schedule
        self.updateDepotScheduleOnChange()

        return True
            
    
    def tryGetNoLunchInsertionPrototype(self, index, newStop):
        trialPlan = copy.deepcopy(self._stops)
        trialPlan.insert(index, newStop)
        lunchDetected = False

        i = index
        while(i < len(trialPlan)):

            current = trialPlan[i]

            # An insert at the beginning is an edge case. The predecessor is a the depot. Its departure time is set exactly to meet the earliest arrival treshhold of the new node.
            if (i == 0):
                predeccesor = copy.deepcopy(self.depot)
                predeccesor.schedule.departureTime = current.serviceTime.earliest - self.problem.timeMatrix[predeccesor.index, current.index]
            else:
                predeccesor = trialPlan[i - 1]

            current.schedule.arrivalTime = predeccesor.schedule.departureTime + self.problem.timeMatrix[predeccesor.index, current.index]
            
            # if we are to late this does not work
            if (current.schedule.arrivalTime > current.serviceTime.latest):
                return False, [], False

            # ... but if it does, do we have to wait here?
            if (current.schedule.arrivalTime < current.serviceTime.earliest):
                current.schedule.waitingTime = current.serviceTime.earliest - current.schedule.arrivalTime
            else:
                current.schedule.waitingTime = 0
            
            current.schedule.departureTime = current.schedule.arrivalTime + current.schedule.waitingTime + current.serviceDuration

            if (current.schedule.departureIncludesBreak or current.schedule.travelIncludesBreak):
                lunchDetected = True
                current.schedule.departureIncludesBreak = False
                current.schedule.travelIncludesBreak = False
            
            # if we have to wait waiting has also been needed before the insert. That means all the updcoming planning stays the same. We can stop here.
            if(current.schedule.waitingTime > 0):
                return True, trialPlan, lunchDetected
            
            i+=1

        # There is no loop iteration that targets the depot arrival. This is because the arrival at the depot is always O.K. as long as we do not cross the maxOvertime treshhold.
        # This is taken care of by the tryInsertServiceStop method.
        
        return True, trialPlan, lunchDetected
    
    def tryInjectLunchBreak(self, prototype):

        earliestLunchStart = self.problem.lunchBreak.earliest
        latestLunchStart = self.problem.lunchBreak.latest
        depotArrival = prototype[len(prototype) - 1].schedule.departureTime + self.problem.timeMatrix[prototype[len(prototype) - 1].index, self.depot.index]
        additionalStay = -1
        additionalDrive = -1

        i = 0
        while(i < len(prototype)):
            stop = prototype[i]
            # If the pause is only possible at this node we have only that one shot
            if (stop.schedule.arrivalTime <= earliestLunchStart and stop.schedule.departureTime >= latestLunchStart):
                # If the lunch is longer than our waiting time we include that waiting time in the lunch break
                if (self.problem.lunchDuration > stop.schedule.waitingTime):
                    # If the lunch would exceed the latest service beginning we take the pause after saying hello to the customer. So no matter how long we wait before,
                    # we have to wait - say hello - and than take the pause.
                    if(stop.schedule.arrivalTime + self.problem.lunchDuration > stop.serviceTime.latest):
                        additionalStay = self.problem.lunchDuration
                        return self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
                    else:
                        additionalStay = self.problem.lunchDuration - stop.schedule.waitingTime
                        return self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
                # If the waiting time is longer or equal to the lunch break we take the lunch at this stage. But we need to wait for that amount of time anyways
                else:
                    additionalStay = 0
                    return self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
            # The pause is only possible in between these two customers or between the last customer and the depot
            elif((stop.schedule.departureTime <= earliestLunchStart and (i + 1) != len(prototype) and prototype[i+1].schedule.arrivalTime >= latestLunchStart) or ((i + 1) == len(prototype) and stop.schedule.departureTime <= earliestLunchStart and depotArrival >= latestLunchStart)):
                additionalDrive = self.problem.lunchDuration
                return self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
            # We can take the pause here and also on another node so let's try it here and if it fails we continue searching
            elif(stop.schedule.arrivalTime >= earliestLunchStart and stop.schedule.arrivalTime < latestLunchStart):
                # If the lunch is longer than our waiting time we include that waiting time in the lunch break
                if (self.problem.lunchDuration > stop.schedule.waitingTime):
                    # If the lunch would exceed the latest service beginning we take the pause after saying hello to the customer. So no matter how long we wait before,
                    # we have to wait - say hello - and than take the pause.
                    if(stop.schedule.arrivalTime + self.problem.lunchDuration > stop.serviceTime.latest):
                        additionalStay = self.problem.lunchDuration
                        success, pauseInjectedPrototype = self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
                        if (success):
                            return success, pauseInjectedPrototype
                    else:
                        additionalStay = self.problem.lunchDuration - stop.schedule.waitingTime
                        success, pauseInjectedPrototype = self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
                        if(success):
                            return success, pauseInjectedPrototype
                # If the waiting time is longer or equal to the lunch break we take the lunch at this stage. But we need to wait for that amount of time anyways
                else:
                    additionalStay = 0
                    success, pauseInjectedPrototype = self.tryUpdateOnLunchInsertion(prototype, additionalStay, additionalDrive, i)
                    if(success):
                         return success, pauseInjectedPrototype
            i+=1
        
        # Before we declare this as impossible we try to insert the pause at the depot itself or on the departure to the first customer
        return self.tryUpdateOnLunchInsertion(prototype, -1, -1, -1)
        
    
    def tryUpdateOnLunchInsertion(self, prototype, additionalStay, additionalDrive, injectAt):
        if(additionalStay != -1 and additionalDrive != -1):
            raise Exception("Impossible system state")

        trialPlan = copy.deepcopy(prototype)

        earliestLunchStart = self.problem.lunchBreak.earliest
        latestLunchStart = self.problem.lunchBreak.latest

        # depot Edge Cases
        if(additionalStay == -1 and additionalDrive == -1):

            depotDeparture = trialPlan[0].serviceTime.earliest - self.problem.timeMatrix[self.depot.index, trialPlan[0].index]
            depotArrival = trialPlan[len(trialPlan) - 1].schedule.departureTime + self.problem.timeMatrix[trialPlan[len(trialPlan) - 1].index, self.depot.index]

            # lunch can be inserted only between the depot and the first customer
            if(depotDeparture <= earliestLunchStart and trialPlan[0].schedule.arrivalTime >= latestLunchStart):
                self.depot.schedule.travelIncludesBreak = True
                injectAt = 0
            
            # we can take the lunch after work on the field
            elif (depotArrival <= latestLunchStart):
                self.depot.schedule.departureIncludesBreak = True
                return True, trialPlan
            
            # we take the pause before work in the field starts. 
            elif(depotDeparture >= latestLunchStart):
                self.depot.schedule.departureIncludesBreak = True
                # if we take the pause as soon as possible and we exceed the departure we have to recalculate the route. The arrival on the first node will shift because we will depart later.
                if(earliestLunchStart + self.problem.lunchDuration > depotDeparture):
                    injectAt = 0
                # we can take the pause and than start work in the field and still are on time like planned so far.
                else:
                    return True, trialPlan
            else:
                return False,  []



        if (additionalStay != -1):
            trialPlan[injectAt].schedule.departureIncludesBreak = True
        else:
            trialPlan[injectAt].schedule.travelIncludesBreak = True
        
        if(additionalStay == 0):
            return True, trialPlan

        i = injectAt
        while(i < len(trialPlan)):

            current = trialPlan[i]

            # the beginning is an edge case. The predecessor is a the depot. Its departure time is set exactly to meet the earliest arrival treshhold of the new node.
            if (i == 0):
                predeccesor = copy.deepcopy(self.depot)
                # the travel from the depot incldues a break
                if(predeccesor.schedule.travelIncludesBreak):
                    predeccesor.schedule.departureTime = current.serviceTime.earliest - self.problem.timeMatrix[predeccesor.index, current.index]
                    predeccesor.schedule.departureTime+= self.problem.lunchDuration

                # we take the lunch at the depot as early as possible to leave when ever needed
                elif(predeccesor.schedule.departureIncludesBreak):
                      predeccesor.schedule.departureTime = earliestLunchStart + self.problem.lunchDuration
            else:
                predeccesor = trialPlan[i - 1]

            current.schedule.arrivalTime = predeccesor.schedule.departureTime + self.problem.timeMatrix[predeccesor.index, current.index]

            if (i - 1  == injectAt and additionalDrive != -1):
                 current.schedule.arrivalTime+= additionalDrive
            
            # if we are to late this does not work
            if (current.schedule.arrivalTime > current.serviceTime.latest):
                return False, []

            # ... but if it does, do we have to wait here?
            if (current.schedule.arrivalTime < current.serviceTime.earliest):
                current.schedule.waitingTime = current.serviceTime.earliest - current.schedule.arrivalTime
            else:
                current.schedule.waitingTime = 0
            
            current.schedule.departureTime = current.schedule.arrivalTime + current.schedule.waitingTime + current.serviceDuration
             
            if(i == injectAt and additionalStay != -1):
                current.schedule.departureTime+= additionalStay
            
            # if we have to wait waiting has also been needed before the insert. That means all the updcoming planning stays the same. We can stop here.
            if(current.schedule.waitingTime > 0):
                return True, trialPlan
            
            i+=1

        # There is no loop iteration that targets the depot arrival. This is because the arrival at the depot is always O.K. as long as we do not cross the maxOvertime treshhold.
        # This is taken care of by the tryInsertServiceStop method.
        
        return True, trialPlan


    
    def updateDepotScheduleOnChange(self):

        # the departure is taken so that the we arrive at the first customer as soon as we can start our work. This has been scheduled to the first stop already.
        self.depot.schedule.departureTime = self._stops[0].serviceTime.earliest - self.problem.timeMatrix[self.depot.index, self._stops[0].index]

        # lunch is taken on the road
        if(self.depot.schedule.travelIncludesBreak):
            self.depot.schedule.departureTime-=self.problem.lunchDuration

        # if we take the lunch at the depot we take it as early as possible. If that break causes us the depart later we have to update the departure time. This has been scheduled to the first stop already.
        if ((self.depot.schedule.departureTime >= self.problem.lunchBreak.latest) and (self.problem.lunchBreak.earliest + self.problem.lunchDuration  > self.depot.schedule.departureTime)):
            self.depot.schedule.departureTime = self.problem.lunchBreak.earliest + self.problem.lunchDuration

        self.depot.schedule.arrivalTime = self._stops[len(self._stops) - 1].schedule.departureTime + self.problem.timeMatrix[self._stops[len(self._stops) - 1].index, self.depot.index]

        # if we could only take the lunch break on the way back to the depot we will arrive later
        if(self._stops[len(self._stops) - 1].schedule.travelIncludesBreak):
            self.depot.schedule.arrivalTime+= self.problem.lunchDuration
    
    
    def removeServiceStop(self, index, cluster = False, lunchDetected = False):
        if(not cluster):
            elToRemove = self._stops[index]
            del self._stops[index]

        i = index
        while(i < len(self._stops)):

            current = self._stops[i]

            # An insert at the beginning is an edge case. The predecessor is a the depot. Its departure time is set exactly to meet the earliest arrival treshhold of the new node.
            if (i == 0):
                predeccesor = copy.deepcopy(self.depot)
                predeccesor.schedule.departureTime = current.serviceTime.earliest - self.problem.timeMatrix[predeccesor.index, current.index]
            else:
                predeccesor = self._stops[i - 1]

            current.schedule.arrivalTime = predeccesor.schedule.departureTime + self.problem.timeMatrix[predeccesor.index, current.index]
            
            # we can never be too late asssuming triangle inequality across the problem space.
            if (current.schedule.arrivalTime > current.serviceTime.latest):
                raise Exception("impossible system state")

            # ... but if it does, do we have to wait here?
            if (current.schedule.arrivalTime < current.serviceTime.earliest):
                current.schedule.waitingTime = current.serviceTime.earliest - current.schedule.arrivalTime
            else:
                current.schedule.waitingTime = 0
            
            current.schedule.departureTime = current.schedule.arrivalTime + current.schedule.waitingTime + current.serviceDuration

            if (current.schedule.departureIncludesBreak or current.schedule.travelIncludesBreak):
                lunchDetected = True
                current.schedule.departureIncludesBreak = False
                current.schedule.travelIncludesBreak = False
            
            i+=1
        
        if(lunchDetected):
            isPossible, pauseInjectedPrototype = self.tryInjectLunchBreak(self._stops)
        else:
            isPossible = True
            pauseInjectedPrototype = self._stops

        # with less time on the field a pause is insertable no matter what
        if(not isPossible):
            raise Exception("impossible system state")

        self._stops = pauseInjectedPrototype

        self.updateDepotScheduleOnChange()

        if(not cluster):
            return elToRemove
    

    def removeServiceStops(self, cluster):
        firstToDelete = min(cluster)
        elementsToRemove = []
        lunchDetected = False
        for removeAt in sorted(cluster, reverse=True):

            if(self._stops[removeAt].schedule.departureIncludesBreak or self._stops[removeAt].schedule.travelIncludesBreak):
                lunchDetected = True

            elementsToRemove.append(self._stops[removeAt])
            del self._stops[removeAt]
        
        self.removeServiceStop(firstToDelete, True, lunchDetected)
        
        return elementsToRemove
    
    def getDistanceBasedInsertionCost(self, pred, succ, newStop):

        if(succ != len(self.stops)):
            succ = self.stops[succ]
        else:
            succ = self.depot

        if(pred != -1):
            pred = self.stops[pred]
        else:
            pred = self.depot

        predToNew = self.problem.distanceMatrix[pred.index, newStop.index]
        newToSucc = self.problem.distanceMatrix[newStop.index, succ.index]
        predToSucc = self.problem.distanceMatrix[pred.index, succ.index]

        cost = predToNew + newToSucc - predToSucc

        if(cost < 0):
            raise Exception("impossible system state")

        return cost
    
    def getTimeBasedInsertionCost(self, pred, succ, newStop):

        if(succ != len(self.stops)):
            succ = self.stops[succ]
        else:
            succ = self.depot

        if(pred != -1):
            pred = self.stops[pred]
        else:
            pred = self.depot

        predToNew = self.problem.timeMatrix[pred.index, newStop.index]
        newToSucc = self.problem.timeMatrix[newStop.index, succ.index]
        predToSucc = self.problem.timeMatrix[pred.index, succ.index]

        cost = predToNew + newToSucc - predToSucc

        if(cost < 0):
            raise Exception("impossible system state")

        return cost
    
    def getIntroducedDelay(self, pred, succ, newStop):

        # if we insert the last node in the route we do not have any delay. Because the depot is not a customer. 
        if(succ == len(self.stops)):
            return 0
        
        succ = self.stops[succ]

        if(pred != -1):
            pred = self.stops[pred]

        currentServiceAtSucc = succ.schedule.arrivalTime
        
        if(pred != -1):
            arrivalAtNewStop = pred.schedule.departureTime + self.problem.timeMatrix[pred.index, newStop.index]
        # the arrival at the first stop, if the predecessor is a depot, is always the ealiest service time
        else:
            arrivalAtNewStop = newStop.serviceTime.earliest

        # do we wait at newStop?
        if (arrivalAtNewStop < newStop.serviceTime.earliest):
            waitAtNewStop = newStop.serviceTime.earliest - arrivalAtNewStop
        else:
            waitAtNewStop = 0
        
        
        departureAtNewStop = arrivalAtNewStop + waitAtNewStop + newStop.serviceDuration
        
        shiftedSuccArrival = departureAtNewStop + self.problem.timeMatrix[newStop.index, succ.index]


        # do we wait with the shifted succ arrival or are we perfectly on time? Then there is no delay.
        if (shiftedSuccArrival <= succ.serviceTime.earliest):
           introducedDelay = 0
        # if he had to wait before we see only the difference with the earliest start as the delay
        elif (currentServiceAtSucc < succ.serviceTime.earliest):
            introducedDelay = shiftedSuccArrival - succ.serviceTime.earliest
        else:
            introducedDelay = shiftedSuccArrival - currentServiceAtSucc

        if(introducedDelay < 0 ):
            raise Exception("impossible system state")

        return introducedDelay

    
    def stateLog(self):
        print("DEPOPT DEPARTURE: " + str(self.depot.schedule.departureTime) + "\nDEPOPT ARRIVAL: " + str(self.depot.schedule.arrivalTime))
        print("DEPOT BREAK ON DEPARTURE: ", str(self.depot.schedule.departureIncludesBreak))
        print("DEPOT BREAK ON TRAVEL: ", str(self.depot.schedule.travelIncludesBreak))
        print("\nSTOPS: ")
        for stop in self._stops:
            print("\n Index: " + str(stop.index) +  " Earliest : " + str(stop.serviceTime.earliest) + " Latest: " + str(stop.serviceTime.latest) + " Arrival: " + str(stop.schedule.arrivalTime) + " Departure: " + str(stop.schedule.departureTime) + " Pause: " + str(stop.schedule.waitingTime) + " Work for: " + str(stop.serviceDuration) +  " Departure Beak: " + str(stop.schedule.departureIncludesBreak) + " Travel Beak: " + str(stop.schedule.travelIncludesBreak))

    

    





