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

lambdaBase = 1
lambdaNL = 0.5

grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')
numDestins = 3 # fixed

subAlternatives = pd.read_csv('pnr_list_corrected.csv')
subIndividuals = pd.read_csv('pnr_utility_corrected.csv')

numAlternatives = len(subAlternatives['id'])
numOrigins = len(subIndividuals['TAZ'])

for rep in [3]:
    
    for numHubs in [20]:

        incumbent = pd.read_csv('result_arr_constrained_I3405_J170_lambda100percent_8hours/arr_constrained_pnr_origin%s_I%s_J%s_p%s_rep%s_lambda%spercent.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,rep,int(lambdaBase * 100)))
        
        util = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                j = 0 # j = 0 : car
                [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_car_CBD%s'%(destin)]
                util[taz,destin,j] = float(utility) 
        
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                for j in subAlternatives['id']:
                    [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_pnr_corr_%s_CBD_%s'%(j,destin)]
                    util[taz,destin,j] = float(utility) 
                    
        Flow = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                [flow_i] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'car_to_CBD%s'%(destin)]
                Flow[taz,destin] = flow_i
        
        
        # theSelected = ROUND(ptb)
        theSelected = []
        for j in range(numHubs):
            [selected] = incumbent.loc[incumbent['Machine']=='FINISH','selectedHub%s'%j]
            theSelected += [selected]
        
        
        # demand(theSelected)
        totalPW_PNR_NL = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                totalPW_PNR_NL[taz,destin] = 0.0
                for j in theSelected:
                    totalPW_PNR_NL[taz,destin] += math.exp(util[taz,destin,j]/lambdaNL)
        
        gamma = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                gamma[taz,destin] = 0.0 # compute gamma_i
                for j in theSelected:
                    gamma[taz,destin] += math.exp(util[taz,destin,j]/lambdaNL)
                gamma[taz,destin] = math.log(gamma[taz,destin])
                
        totalDemand = 0.0
        for j in theSelected:
            demand_j = 0.0
            for taz in subIndividuals['TAZ']:
                for destin in range(numDestins):
                    demand_j += Flow[taz,destin] * (math.exp(lambdaNL * gamma[taz,destin]) / (math.exp(util[taz,destin,0]) + math.exp(lambdaNL * gamma[taz,destin]))) * (math.exp(util[taz,destin,j]/lambdaNL) / totalPW_PNR_NL[taz,destin])
            [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
            totalDemand += min(demand_j,capacity_j)
            #totalDemand += demand_j # unconstrained

        print('totalDemand=',totalDemand)                    
        print('lambdaNL=',lambdaNL)                    
        print('lambdaBase=',lambdaBase)                    
                
        
