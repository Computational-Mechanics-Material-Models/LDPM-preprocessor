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
## This file contains the function to generate a particle via MPI and also 
## outputs the particle diameter and new maximum iterations.
##
## ===========================================================================



import numpy as np

from freecad.ldpmWorkbench.generation.check_LDPMCSL_particleOverlap     import check_LDPMCSL_particleOverlap
from freecad.ldpmWorkbench.generation.check_LDPMCSL_particleInside      import check_LDPMCSL_particleInside


def gen_particleMPI(facePoints,maxParNum,minC,maxC,\
    vertices,tets,coord1,coord2,coord3,coord4,newMaxIter,maxIter,minPar,maxPar,\
    parOffset,verbose,parDiameterList,maxEdgeLength,max_dist,nodes,parDiameter):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - facePoints:       List of points on the surface of the mesh
    - maxParNum:        Maximum number of particles to generate
    - minC:             Minimum coordinate of the mesh
    - maxC:             Maximum coordinate of the mesh
    - vertices:         List of vertices of the mesh
    - tets:             List of tetrahedrons of the mesh
    - coord1:           Coordinate 1 of the tets
    - coord2:           Coordinate 2 of the tets
    - coord3:           Coordinate 3 of the tets
    - coord4:           Coordinate 4 of the tets
    - newMaxIter:       Maximum number of iterations to try to place a particle
    - maxIter:          Maximum number of iterations to try to place a particle
    - minPar:           Minimum particle diameter
    - maxPar:           Maximum particle diameter
    - parOffset:        Offset coefficient for particle placement
    - verbose:          Verbose output
    - parDiameterList:  List of particle diameters
    - maxEdgeLength:    Maximum edge length of the mesh
    - max_dist:         Maximum distance between particles
    - nodes:            List of nodes
    - parDiameter:      Particle diameter
    --------------------------------------------------------------------------
    ### Outputs ###
    - node:             Node location of the particle
    - newMaxIter:       Maximum number of iterations to try to place a particle
    - iterReq:          Number of iterations required to place a particle
    --------------------------------------------------------------------------
    """  

    # Generate random numbers to use in generation
    # Pre-generate more random numbers to reduce regeneration overhead
    randomN = np.random.rand(newMaxIter*3)
    i=0
    ntet = len(tets)
    attempts = 0
    
    # Generate random nodal location
    while True:
        i=i+3
        attempts += 1

        if i/3 >= newMaxIter:
            i = 3
            # Double the buffer size, but cap growth to avoid memory issues
            newMaxIter = min(newMaxIter * 2, maxIter)
            randomN = np.random.rand(newMaxIter*3)

        if newMaxIter >= maxIter:
            error_msg = "Particle placement failed: exceeded the %r specified maximum iterations allowed." % (maxIter)
            print(error_msg)
            raise RuntimeError(error_msg)

        # Random point selection in random tet prism container
        tetVerts = np.vstack((vertices[int(tets[int(int(np.around(randomN[i]*ntet))-1),0]-1),:],\
            vertices[int(tets[int(int(np.around(randomN[i]*ntet))-1),1]-1),:],\
            vertices[int(tets[int(int(np.around(randomN[i]*ntet))-1),2]-1),:],\
            vertices[int(tets[int(int(np.around(randomN[i]*ntet))-1),3]-1),:]))

        tetMin = np.amin(tetVerts, axis=0)
        tetMax = np.amax(tetVerts, axis=0)

        node = np.array([randomN[i]*(tetMax[0]-tetMin[0])+tetMin[0],\
            randomN[i+1]*(tetMax[1]-tetMin[1])+tetMin[1],randomN[i+2]\
            *(tetMax[2]-tetMin[2])+tetMin[2]]).T
        node = node[np.newaxis,:]           


        # Obtain extents for floating bin
        binMin = np.array(([node[0,0]-parDiameter/2-maxPar/2-parOffset,\
            node[0,1]-parDiameter/2-maxPar/2-parOffset,node[0,2]-\
            parDiameter/2-maxPar/2-parOffset]))
        binMax = np.array(([node[0,0]+parDiameter/2+maxPar/2+parOffset,\
            node[0,1]+parDiameter/2+maxPar/2+parOffset,node[0,2]+\
            parDiameter/2+maxPar/2+parOffset]))


        # Check if particle overlapping any existing particles or bad nodes
        overlap = check_LDPMCSL_particleOverlap(nodes,node,parDiameter,facePoints,binMin,\
            binMax,minPar,maxEdgeLength,parOffset,parDiameterList)

        if overlap[0] == False:
            
            # If critically close to the surface:
            if overlap[1] == True:


                # Check if particle is inside the mesh if critically close          
                inside = check_LDPMCSL_particleInside(vertices,tets,node,parDiameter,binMin,binMax,coord1,\
                                    coord2,coord3,coord4)

            else:

                inside = True

            # Indicate placed particle and break While Loop
            if inside == True and overlap[0] == False:
                break


    return np.append(node[0,:],[parDiameter,newMaxIter,int(i/3)])