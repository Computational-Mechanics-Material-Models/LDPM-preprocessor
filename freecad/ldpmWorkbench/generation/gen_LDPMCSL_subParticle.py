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
## This file contains the function to generate a subparticle and outputs the
## location of the particle as well as the maximum number of iterations
## allowed and the number of iterations required to place the particle.
##
## ===========================================================================

import numpy as np
import time

from freecad.ldpmWorkbench.generation.check_LDPMCSL_particleOverlap    import check_LDPMCSL_particleOverlap
from freecad.ldpmWorkbench.generation.check_LDPMCSL_particleInside     import check_LDPMCSL_particleInside


def gen_LDPMCSL_subParticle(facePoints,parDiameter,\
    vertices,tets,newMaxIter,maxIter,minPar,maxPar,\
    parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,nodes,\
    multiMatX,multiMatY,multiMatZ,multiMatRes,multiMatVoxels,voxelIDs,minC,maxC, quiet=False):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - facePoints:       List of points on the surface of the mesh
    - parDiameter:      Diameter of the particle
    - vertices:         List of vertices of the mesh
    - tets:             List of tetrahedrons of the mesh
    - newMaxIter:       Maximum number of iterations to try to place a particle
    - maxIter:          Maximum number of iterations to try to place a particle
    - minPar:           Minimum particle diameter
    - maxPar:           Maximum particle diameter
    - parOffset:        Offset coefficient for particle placement
    - parDiameterList:  List of all particle diameters
    - coord1:           Coordinate 1 of the tets
    - coord2:           Coordinate 2 of the tets
    - coord3:           Coordinate 3 of the tets
    - coord4:           Coordinate 4 of the tets
    - maxEdgeLength:    Maximum edge length of the mesh
    - max_dist:         Maximum distance from the surface
    - nodes:            List of nodes
    --------------------------------------------------------------------------
    ### Outputs ###
    - node:             Node location of the particle
    - newMaxIter:       Maximum number of iterations to try to place a particle
    - iterReq:          Number of iterations required to place a particle
    --------------------------------------------------------------------------
    """  


    # Generate random numbers to use in generation
    randomN = np.random.rand(newMaxIter*3)    
    nVoxels = len(multiMatVoxels)

    # Generate random nodal location
    iterReq = 0
    attempts = 0
    max_attempts_critical = 2500
    max_time_seconds = 60

    start_time = time.time()

    while True:
        iterReq = iterReq + 3
        attempts += 1

        elapsed_time = time.time() - start_time
        if elapsed_time > max_time_seconds:
            raise RuntimeError()

        if attempts >= max_attempts_critical:
            raise RuntimeError()

        if iterReq/3 >= newMaxIter:
            iterReq = 0
            newMaxIter = min(newMaxIter * 2, maxIter)
            randomN = np.random.rand(newMaxIter*3)

        if newMaxIter >= maxIter:
            raise RuntimeError()

        # Selection of random voxel
        randVoxel = round(randomN[iterReq]*nVoxels)

        # Find voxel coordinates of random voxel
        xVoxel = np.floor(multiMatVoxels[randVoxel-1]/(multiMatZ*multiMatY))+1
        yVoxel = np.floor((multiMatVoxels[randVoxel-1]-(xVoxel-1)*(multiMatZ*multiMatY))/multiMatZ)+1
        zVoxel = multiMatVoxels[randVoxel-1]-(xVoxel-1)*(multiMatZ*multiMatY)-(yVoxel-1)*multiMatZ

        # Min and max coordinates of voxel (offset to align with geometry)
        voxMin = np.array(((xVoxel-1)*multiMatRes-multiMatRes/2,(yVoxel-1)*\
            multiMatRes-multiMatRes/2,(zVoxel-1)*multiMatRes-multiMatRes/2))+minC
        voxMax = np.array(((xVoxel-1)*multiMatRes+multiMatRes/2,(yVoxel-1)*\
            multiMatRes+multiMatRes/2,(zVoxel-1)*multiMatRes+multiMatRes/2))+minC

        # Check voxel max is within max of geometry
        if (voxMax[0]<maxC[0] and voxMax[1]<maxC[1] and voxMax[2]<maxC[2]).all(): 

            # Select random point in voxel
            node = np.array([randomN[iterReq]*(voxMax[0]-voxMin[0])+voxMin[0],\
                randomN[iterReq+1]*(voxMax[1]-voxMin[1])+voxMin[1],randomN[iterReq+2]\
                *(voxMax[2]-voxMin[2])+voxMin[2]]).T
            node = node[np.newaxis,:]           

            # Obtain extents for floating bin
            binMin = node[0,:] - parDiameter/2 - maxPar/2 - parOffset
            binMax = node[0,:] + parDiameter/2 + maxPar/2 + parOffset

            # Check if particle overlapping any existing particles or bad nodes
            overlap = check_LDPMCSL_particleOverlap(nodes,node,parDiameter,facePoints,binMin,\
                binMax,minPar,maxEdgeLength,parOffset,parDiameterList)

            # If does not overlap an existing particle set overlap[0] = False
            if overlap[0] == False:
                
                # If critically close to the surface set overlap[1] = True
                if overlap[1] == True:

                    # Check if particle is inside the mesh if critically close          
                    inside = check_LDPMCSL_particleInside(vertices,tets,node,parDiameter,binMin,binMax,coord1,\
                                        coord2,coord3,coord4)

                else:
                    inside = True

                # Indicate placed particle and break While Loop
                if inside == True and overlap[0] == False:
                    if (type(voxelIDs) == np.ndarray):
                        return newMaxIter,node,iterReq,voxelIDs[randVoxel-1]
                    else:
                        return newMaxIter,node,iterReq,0
