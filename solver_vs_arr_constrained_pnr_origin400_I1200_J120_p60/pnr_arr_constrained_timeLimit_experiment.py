import pandas as pd
import random 
from gurobipy import *
import math
import copy
import time
import datetime
import socket

machineName = socket.gethostname()
print(machineName)
print(datetime.datetime.now())

#trialLimit = 20000
timeLimit = 60
repLimit = 1


# =============================================================================
# (numHubs,numAlternatives,numOrigins,numInstances) = (15,30,100,10)
# instance = 0
# 
# grandAlternatives = pd.read_csv('pnr_list_csv.csv')
# grandIndividuals = pd.read_csv('pnr_utility.csv')
# numDestins = 3 # fixed
# tolError = 7 # limit of error of odds
# 
# subAlternatives = pd.read_csv('pnr_list_csv.csv')
# subIndividuals = pd.read_csv('pnr_utility.csv')
# 
# numHubs = int(len(subAlternatives['id']) / 2)
# numAlternatives = len(subAlternatives['id'])
# numOrigins = len(subIndividuals['TAZ'])
# =============================================================================


(numHubs,numAlternatives,numOrigins,numInstances) = (6,30,100,10)
instance = 0

grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')
numDestins = 3 # fixed
tolError = 7 # limit of error of odds


#for (numAlternatives,numOrigins,timeLimit) in [(60,200,600),(90,300,3000),(120,400,15000)]:#[(30,100,60),(60,200,300),(90,300,1500),(120,400,7500)]:
# =============================================================================
# for (numAlternatives,numOrigins) in [(120,400)]:#[(30,100),(60,200),(90,300),(120,400)]:
#     numHubs = int(numAlternatives / 2 + 0.0001)
# =============================================================================



print(numAlternatives,numHubs)
trialLimit = 100 * numOrigins

for instance in [0]:#range(numInstances):
    for rep in range(repLimit):
        print(datetime.datetime.now())
        print('instance=',instance)
        
        subAlternatives = pd.read_csv('../data/pnr_J%s_inst%s.csv'%(numAlternatives,instance))
        subIndividuals = pd.read_csv('../data/origin%s_I%s_inst%s.csv'%(numOrigins, numOrigins * numDestins, instance))
        
        
        pw = {} # preference weight
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                j = 0 # j = 0 : car
                [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_car_CBD%s'%(destin)]
                pw[taz,destin,j] = math.exp(utility)
        
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                for j in subAlternatives['id']:
                    [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_pnr_corr_%s_CBD_%s'%(j,destin)]
                    pw[taz,destin,j] = math.exp(utility)
        
        totalPW = {}            
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                totalPW[taz,destin] = pw[taz,destin,0]
                for j in subAlternatives['id']:
                    totalPW[taz,destin] += pw[taz,destin,j]
        
        odds = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                for j in subAlternatives['id']:
                    odds[taz,destin,j] = pw[taz,destin,j] / pw[taz,destin,0]
                    
        Flow = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                [flow_i] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'car_to_CBD%s'%(destin)]
                Flow[taz,destin] = flow_i
        
        halfY = {}
        for j in subAlternatives['id']:
            halfY[j] = 0.5
            
        tic = time.time()
        # seed -> perturb     
        seedY = copy.deepcopy(halfY)
        ptbY = {}
        for j in subAlternatives['id']:
            ptbY[j] = seedY[j] * random.random()
        
        
        # theSelected = ROUND(ptb)
        theSelected = []
        jToProcess = copy.deepcopy(list(subAlternatives['id']))
        while len(theSelected) < numHubs:
            largest = 0.0    
            largestJ = -1
            for j in jToProcess:
                if largest < ptbY[j]:
                    largest = ptbY[j]
                    largestJ = j
            jToProcess.remove(largestJ)
            theSelected += [largestJ]
        
        
        # demand(theSelected)
        totalPW = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                totalPW[taz,destin] = pw[taz,destin,0]
                for j in theSelected:
                    totalPW[taz,destin] += pw[taz,destin,j]
        
        totalDemand = 0.0
        for j in theSelected:
            demand_j = 0.0
            for taz in subIndividuals['TAZ']:
                for destin in range(numDestins):
                    demand_j += Flow[taz,destin] * pw[taz,destin,j] / totalPW[taz,destin]
            [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
            totalDemand += min(demand_j,capacity_j)
            #totalDemand += demand_j # unconstrained
        
        
        # record trial = 0
        bestDemand = totalDemand
        bestSelected = copy.deepcopy(sorted(theSelected))
        trial = 0
        nLocal = 0
        reset = False
        print()
        print('trial=',trial)
        toc = time.time()
        print('elapse time=',toc-tic)
        print('bestDemand=',bestDemand)
        
        machineArray = [machineName]
        repArray = [rep]
        trialArray = [trial]
        timeArray = [toc-tic]
        demandArray = [bestDemand]
        
        selectedArray = {}
        for num in range(numHubs):
            selectedArray[num] = [bestSelected[num]]
        
        bestSolution = pd.DataFrame(list(zip(machineArray,repArray,trialArray,timeArray,demandArray)),columns =['Machine','Rep','Trial','Time','Demand'])
        for num in range(numHubs):
            bestSolution['selectedHub%s'%num] = selectedArray[num] 
        
        #bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_trial%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,trialLimit), index = False)#Check
        bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_rep%s_time%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,rep,timeLimit), index = False)#Check
        
        toc = time.time()
        elapseTime = toc - tic
        while elapseTime < timeLimit:
        #while trial < trialLimit:
            
            trial += 1
        
            # compute RMSD
            RMSD = 0.0
            for j in subAlternatives['id']:
                RMSD += (seedY[j] - 0.5) ** 2
            RMSD = math.sqrt(RMSD / len(subAlternatives['id']))
        
            # seed -> perturb     
            ptbY = {}
            for j in subAlternatives['id']:
                ptbY[j] = seedY[j] * random.random()
            
            # theSelected = ROUND(ptb)
            theSelected = []
            jToProcess = copy.deepcopy(list(subAlternatives['id']))
            while len(theSelected) < numHubs:
                largest = 0.0    
                largestJ = -1
                for j in jToProcess:
                    if largest < ptbY[j]:
                        largest = ptbY[j]
                        largestJ = j
                jToProcess.remove(largestJ)
                theSelected += [largestJ]
                
                
            # check theSelected = bestSelected
            same = True
            for j in bestSelected:
                if j not in theSelected:
                    same = False
                    break
                
            if same == True:
                nLocal += 1
                
                # compute reset probability
                ## pR = probability of reset
                pR = min(1,nLocal/20) * RMSD
                if pR > random.random():
                    reset = True
                    seedY = copy.deepcopy(halfY)
                    nLocal = 0
                    
            else:
                nLocal = 0
                reset = False
                
                # demand(theSelected)
                totalPW = {}
                for taz in subIndividuals['TAZ']:
                    for destin in range(numDestins):
                        totalPW[taz,destin] = pw[taz,destin,0]
                        for j in theSelected:
                            totalPW[taz,destin] += pw[taz,destin,j]
                
                totalDemand = 0.0
                for j in theSelected:
                    demand_j = 0.0
                    for taz in subIndividuals['TAZ']:
                        for destin in range(numDestins):
                            demand_j += Flow[taz,destin] * pw[taz,destin,j] / totalPW[taz,destin]
                    [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
                    totalDemand += min(demand_j,capacity_j)
                    #totalDemand += demand_j # unconstrained
                    
                    
                if bestDemand < totalDemand:
                    bestDemand = totalDemand
                    bestSelected = copy.deepcopy(sorted(theSelected))            
                    print()
                    print('trial=',trial)
                    toc=time.time()
                    print('elapse time=',toc-tic)
                    print('bestDemand=',bestDemand)
        
                    machineArray += [machineName]
                    repArray += [rep]
                    trialArray += [trial]
                    timeArray += [toc-tic]
                    demandArray += [bestDemand]
                    
                    for num in range(numHubs):
                        selectedArray[num] += [bestSelected[num]]
                    
                    #bestSolution = pd.DataFrame(list(zip(machineArray,trialArray,timeArray,demandArray)),columns =['Machine','Trial','Time','Demand'])
                    bestSolution = pd.DataFrame(list(zip(machineArray,repArray,trialArray,timeArray,demandArray)),columns =['Machine','Rep','Trial','Time','Demand'])
                    for num in range(numHubs):
                        bestSolution['selectedHub%s'%num] = selectedArray[num] 

                    #bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_trial%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,trialLimit), index = False)#Check
                    #bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_time%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,timeLimit), index = False)#Check
                    bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_rep%s_time%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,rep,timeLimit), index = False)#Check

                
            if reset == False:
                alpha = 1 / (1 + math.exp(4 * RMSD))
                for j in subAlternatives['id']:
                    seedY[j] = (1 - alpha) * seedY[j]
                for j in bestSelected:
                    seedY[j] += alpha 
                
            toc = time.time()
            elapseTime = toc - tic
        
        toc = time.time()
        elapseTime = toc - tic
        print('elapseTime=',elapseTime)
        
        machineArray += ['Finish']
        repArray += [rep]
        trialArray += [trial]
        timeArray += [toc-tic]
        demandArray += [bestDemand]
        
        for num in range(numHubs):
            selectedArray[num] += [bestSelected[num]]
        
        #bestSolution = pd.DataFrame(list(zip(machineArray,trialArray,timeArray,demandArray)),columns =['Machine','Trial','Time','Demand'])
        bestSolution = pd.DataFrame(list(zip(machineArray,repArray,trialArray,timeArray,demandArray)),columns =['Machine','Rep','Trial','Time','Demand'])
        for num in range(numHubs):
            bestSolution['selectedHub%s'%num] = selectedArray[num] 
        
        #bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_trial%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,trialLimit), index = False)#Check
        #bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_time%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,timeLimit), index = False)#Check
        bestSolution.to_csv(r'arr_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_rep%s_time%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,rep,timeLimit), index = False)#Check

