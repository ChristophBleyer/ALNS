import numpy as np
from technician_planning import Problem
from construction import Construction
from operators import Operators
from alns.ALNS import ALNS
from alns.criteria import HillClimbing, SimulatedAnnealing, RecordToRecordTravel, ThresholdAcceptance

# the parameter sets to tune
DEGREE_OF_DESTRUCTION = [[0.2, 0.4], [0.3, 0.5], [0.4, 0.6]]
DEGREE_OF_DIVERSIFICATION = [6,3,12]
TIME_BASED_WORST_REMOVAL = [[0.75, 0.25], [0.5, 0.5], [1.0, 0.0]]
CUSTS_FROM_HOLDING_TO_REMOVE = [0.5, 0.25, 0.75]
RELATED_REMOVAL = [[3, 1, 5], [1,2,1], [5, 1, 3]]
ALNS_DECAY = [0.8, 0.9, 0.6]
ALNS_WEIGHTS = [[3, 2, 1, 0.5], [5, 4.5, 1, 0.5], [5, 2 , 1, 0.5]]
FIXED_END_LINEAR_RRT = [0.2, 0.05, 0.1, 0.15, 0.25, 0.3, 0.35, 0.4]
FIXED_END_LINEAR_TA = [0.25, 0.05, 0.1, 0.15, 0.2, 0.3, 0.35, 0.4]
EXPONENTIAL_FIXED_END_SIMULATED_ANNEALING = [[1000, 0.0001, 0.95], [1000, 0.0001, 0.9], [1000, 0.0001, 0.99]]

optimizationSpace = [DEGREE_OF_DESTRUCTION, DEGREE_OF_DIVERSIFICATION, TIME_BASED_WORST_REMOVAL, CUSTS_FROM_HOLDING_TO_REMOVE, RELATED_REMOVAL, ALNS_DECAY, ALNS_WEIGHTS, FIXED_END_LINEAR_RRT]

def calibrate(numIterations):

    its = 0

    p1 = Problem.Problem("examples/Datasets/Data_1.csv", "examples/Datasets/Matrix_1.json")
    p2 = Problem.Problem("examples/Datasets/Data_2.csv", "examples/Datasets/Matrix_2.json")
    p3 = Problem.Problem("examples/Datasets/Data_3.csv", "examples/Datasets/Matrix_3.json")
    p4 = Problem.Problem("examples/Datasets/Data_4.csv", "examples/Datasets/Matrix_4.json")

    clustered1 = Construction.parallelUrgencyAssignment(p1)
    clustered2 = Construction.parallelUrgencyAssignment(p2)
    clustered3 = Construction.parallelUrgencyAssignment(p3)
    clustered4 = Construction.parallelUrgencyAssignment(p4)

    Construction.buildSolutionParallelStyle(clustered1)
    Construction.buildSolutionParallelStyle(clustered2)
    Construction.buildSolutionParallelStyle(clustered3)
    Construction.buildSolutionParallelStyle(clustered4)

    # the instances we use as a starting point for paramter tuning
    instances = [clustered1, clustered2, clustered3, clustered4]
    globalAvgs = []
    
    # we start with the initial guess
    pointersToOptimalParameterSet = [0, 0, 0, 0, 0, 0, 0, 0]

    # we repeat the tuning numIteration times
    while(its < numIterations):

        targetIdxToOptimize = 0
        
        # for each paramter
        while (targetIdxToOptimize < len(pointersToOptimalParameterSet)):
            
            currentObjectiveScores = []

            # for each parameter set for that parameter
            for targetParamSetIdx in range(len(optimizationSpace[targetIdxToOptimize])):
                
                # change the value for the current parameter - keep all the other values fixed
                pointersToOptimalParameterSet[targetIdxToOptimize] = targetParamSetIdx

                Operators.destructionRange = optimizationSpace[0][pointersToOptimalParameterSet[0]] 
                Operators.degreeOfDiversification = optimizationSpace[1][pointersToOptimalParameterSet[1]]
                Operators.worstRemovalWeights = optimizationSpace[2][pointersToOptimalParameterSet[2]]
                Operators.holdingListRemoval = optimizationSpace[3][pointersToOptimalParameterSet[3]]
                Operators.relatednessWeights = optimizationSpace[4][pointersToOptimalParameterSet[4]]

                objectiveScoresCurrentSetting = []
                # run the configuration on all instances 3 times
                for instance in instances:
                
                    l = 0
                    while (l < 3):

                        # run the alns algorithm
                        alns = ALNS()
                        alns.add_destroy_operator(Operators.randomRemoval)
                        alns.add_destroy_operator(Operators.distancedBasedWorstRemoval)
                        alns.add_destroy_operator(Operators.timeBasedWorstRemoval)
                        alns.add_destroy_operator(Operators.relatedRemoval)
                        alns.add_repair_operator(Operators.greedyInsertion)
                        alns.add_repair_operator(Operators.k_regretInsertion)
                        criterion = RecordToRecordTravel(optimizationSpace[7][pointersToOptimalParameterSet[7]], 0.00000000000001, optimizationSpace[7][pointersToOptimalParameterSet[7]]/1000, method = "linear")

                        result = None
                        while result is None:
                            try:
                                result = alns.iterate(instance, optimizationSpace[6][pointersToOptimalParameterSet[6]], optimizationSpace[5][pointersToOptimalParameterSet[5]], criterion, iterations=1000, collect_stats=True)
                            except ...:
                                print("Something went wrong.")
                        
                        optimized = result.best_state
                        objective = optimized.objective()
                        objectiveScoresCurrentSetting.append(objective)
                    
                        l+=1
            
                # after running the configuration on all instances 3 times we compute the average performance. That performance is then saved to all the results from the other paremter settings
                avg = np.mean(objectiveScoresCurrentSetting)
                currentObjectiveScores.append(avg)
            
            # after we collected all the averages we decide which setting is best by choosing the setting with the lowest average objective cost aka the best performance
            targetSetting = currentObjectiveScores.index(min(currentObjectiveScores))
            pointersToOptimalParameterSet[targetIdxToOptimize] = targetSetting
            globalAvgs.append(currentObjectiveScores[targetSetting])
            
            # now we move on to the next paramter set to tune
            targetIdxToOptimize+=1
            
            print("Parameter set optimized: ", targetIdxToOptimize, "/", len(pointersToOptimalParameterSet), " Run: ", its, "/", numIterations)
            print("Current result: ", pointersToOptimalParameterSet)
                                                                                                                                                                           
        its+=1
    
    print()
    print()
    print("Result vector: ", pointersToOptimalParameterSet)
    print("Global Averages: ", globalAvgs)