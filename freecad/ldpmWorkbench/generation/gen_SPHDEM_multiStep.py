## ===========================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be
## found in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ===========================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ===========================================================================
##
## Description coming soon...
## 
## ===========================================================================



import numpy as np
import math
import time
import multiprocessing
import functools
from pathlib import Path


import sys
import FreeCAD as App


from calc_sieveCurve                                        import calc_sieveCurve
from calc_parVolume                                         import calc_parVolume
from gen_particleList                                       import gen_particleList
from gen_particleMPI                                        import gen_particleMPI
from check_particleOverlapMPI                               import check_particleOverlapMPI
from gen_particle                                           import gen_particle



def gen_SPHDEM_multiStep(tempPath, numCPU, numIncrements, maxIter, parOffset, maxEdgeLength, max_dist, minPar, maxPar, sieveCurveDiameter, sieveCurvePassing, wcRatio, cementC, airFrac, fullerCoef, flyashC, silicaC, scmC, fillerC, flyashDensity, silicaDensity, scmDensity, fillerDensity, cementDensity, densityWater, tetVolume, minC, maxC, verbose):

    # Load back in these seven matrices from their temporary files:
    # coord1, coord2, coord3, coord4, meshVertices, meshTets, surfaceNodes

    maxC = np.array(maxC)
    minC = np.array(minC)

    # Read in the seven matrices from their temporary files
    coord1 = np.load(tempPath + 'coord1.npy')
    coord2 = np.load(tempPath + 'coord2.npy')
    coord3 = np.load(tempPath + 'coord3.npy')
    coord4 = np.load(tempPath + 'coord4.npy')
    meshVertices = np.load(tempPath + 'meshVertices.npy')
    meshTets = np.load(tempPath + 'meshTets.npy')
    surfaceNodes = np.load(tempPath + 'surfaceNodes.npy')


    # Shift sieve curve if needed
    if sieveCurveDiameter != (0 or None or [] or ""):
        # Shifts sieve curve to appropriate range
        [newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max] = calc_sieveCurve(minPar, maxPar, sieveCurveDiameter, sieveCurvePassing)
    else:
        newSieveCurveD, newSieveCurveP, w_min, w_max, NewSet = 0, 0, 0, 0, 0

    # Calculates volume of particles needed
    [volFracPar, parVolTotal, cdf, cdf1, kappa_i] = calc_parVolume(tetVolume, wcRatio, cementC,
                                                airFrac, fullerCoef, 
                                                flyashC, silicaC, scmC, fillerC,
                                                flyashDensity, silicaDensity, 
                                                scmDensity, fillerDensity, cementDensity,
                                                densityWater, minPar, maxPar,
                                                newSieveCurveD, newSieveCurveP, 
                                                NewSet, w_min, w_max)



    # Calculate list of particle diameters for placement
    [maxParNum,parDiameterList] = gen_particleList(parVolTotal,minPar,maxPar,newSieveCurveD,\
        cdf,kappa_i,NewSet,fullerCoef)

    # Initialize empty particle nodes list outside geometry
    internalNodes = (np.zeros((len(parDiameterList),3))+2)*maxC





    ########################## Begin Placing Particles ##############################

    


    
    # Initialize values
    newMaxIter = 6
    particlesPlaced = 0


    # Initialize particleID list of length of internalNodes
    particleID = np.zeros(len(internalNodes))

    if numCPU > 1:
    
        
        for increment in range(numIncrements-1):

            process_pool = multiprocessing.Pool(numCPU)

            outputMPI = process_pool.map(functools.partial(gen_particleMPI, surfaceNodes,maxParNum, minC, maxC, meshVertices, \
                meshTets, coord1,coord2,coord3,coord4,newMaxIter,maxIter,minPar,\
                maxPar,parOffset,verbose,parDiameterList,maxEdgeLength,max_dist,internalNodes), parDiameterList[particlesPlaced:particlesPlaced+math.floor(len(parDiameterList)/numIncrements)])

            nodeMPI = np.array(outputMPI)[:,0:3]
            diameter = np.array(outputMPI)[:,3]
            newMaxIter = int(max(np.array(outputMPI)[:,4]))
            maxAttempts = int(max(np.array(outputMPI)[:,5]))

            particlesPlaced = particlesPlaced+len(np.array(outputMPI)[:,0:3])        

            for x in range(len(nodeMPI)):

                # Store placed particles from this increment
                internalNodes[particlesPlaced+x,:] = nodeMPI[x,:]

                # Obtain extents for floating bin for node to test
                binMin = np.array(([nodeMPI[x,0]-diameter[x]/2-maxPar/2-parOffset,\
                    nodeMPI[x,1]-diameter[x]/2-maxPar/2-parOffset,nodeMPI[x,2]-\
                    diameter[x]/2-maxPar/2-parOffset]))
                binMax = np.array(([nodeMPI[x,0]+diameter[x]/2+maxPar/2+parOffset,\
                    nodeMPI[x,1]+diameter[x]/2+maxPar/2+parOffset,nodeMPI[x,2]+\
                    diameter[x]/2+maxPar/2+parOffset]))

                # Check if particle overlapping any just added particles (ignore first one placed)
                if x > 0:

                    overlap = check_particleOverlapMPI(nodeMPI[x,:],diameter[x],binMin,\
                        binMax,minPar,parOffset,nodeMPI[0:x],diameter[0:x])

                    if overlap == True:

                        [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,\
                            parDiameterList[particlesPlaced+x], meshVertices, \
                            meshTets,newMaxIter,maxIter,minPar,\
                            maxPar,parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes)
                        
                        internalNodes[particlesPlaced+x,:] = node[0,:]



    # Generate particles for length of needed aggregate (not placed via MPI)
    for x in range(particlesPlaced,len(parDiameterList)):

        # Generate particle
        [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,parDiameterList[x],meshVertices,meshTets,newMaxIter,maxIter,minPar,maxPar,\
            parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes)
 

        internalNodes[x,:] = node




    materialList = np.ones(len(parDiameterList))


    # Save the internalNodes list to a temporary file
    np.save(tempPath + 'internalNodes.npy', internalNodes)

    # Save the materialList to a temporary file
    np.save(tempPath + 'materialList.npy', materialList)

    # Save the parDiameterList to a temporary file
    np.save(tempPath + 'parDiameterList.npy', parDiameterList)

    # Save the particleIDs to a temporary file
    np.save(tempPath + 'particleID.npy', particleID)

    # Save the volFracPar to a temporary file
    np.save(tempPath + 'volFracPar.npy', volFracPar)


    #placementTime = round(time.time() - start_time,2)   
    nParticles = len(parDiameterList)