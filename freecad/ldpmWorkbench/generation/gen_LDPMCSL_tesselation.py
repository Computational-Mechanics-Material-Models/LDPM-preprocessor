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
## This file contains the function to perform the tesselation of the mesh and
## generates the facet connectivity, facet centers, facet areas, facet normals,
## and other facet data for LDPM tesselations
##
## ===========================================================================

import numpy as np


def gen_LDPMCSL_tesselation(allNodes,allTets,parDiameterList,minPar,geoName):
    
    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    allNodes:        An array of coordinates for all nodes in the mesh.
    allTets:         An array of indices defining the tet connectivity 
    parDiameterList: An array of diameters for each particle.
    minPar:          The minimum particle diameter.
    geoName:         The name of the geometry.
    --------------------------------------------------------------------------
    ### Outputs ###
    tetFacets:       An array of indices defining the facet connectivity 
    facetCenters:    An array of coordinates for the center of each facet in the mesh.
    facetAreas:      An array of the area of each facet in the mesh.
    facetNormals:    An array of the normal vector of each facet in the mesh.
    tetn1:           An array of indices for the first node of each tetrahedron in the mesh.
    tetn2:           An array of indices for the second node of each tetrahedron in the mesh.
    tetPoints:       An array of coordinates for the center of each tetrahedron in the mesh.
    allDiameters:    An array of diameters for each node in the mesh.
    facetPointData:  Condensed array of facet nodes
    facetCellData:   Facet connectivity for condensed facet node list
    --------------------------------------------------------------------------
    """

    # Create diameters list (including fictitious edge particle diameters)
    allDiameters = np.concatenate((np.array([1.1*minPar,]*\
        int(len(allNodes)-len(parDiameterList))),parDiameterList))

    # Definition of Edge Points [Coordinates1,....,Coordinates6]
    # Given ambiguous indexing in Cusatis 2011a for edges, the following is used:
    # E1 = E12 or edgePoints[:,0:3]
    # E2 = E13 or edgePoints[:,3:6]
    # E3 = E14 or edgePoints[:,6:9]
    # E4 = E23 or edgePoints[:,9:12]
    # E5 = E24 or edgePoints[:,12:15]
    # E6 = E34 or edgePoints[:,15:18]
    edges1 = [allTets[:,0],allTets[:,1]]
    edges2 = [allTets[:,0],allTets[:,2]]
    edges3 = [allTets[:,0],allTets[:,3]]
    edges4 = [allTets[:,1],allTets[:,2]]
    edges5 = [allTets[:,1],allTets[:,3]]
    edges6 = [allTets[:,2],allTets[:,3]]

    edges = np.concatenate((edges1,edges2,edges3,edges4,edges5,edges6),\
        axis=1).T

    edges = np.sort(edges,axis=1)

    edgeNode1 = allNodes[(edges[:,0]-1).astype(int),:]
    edgeNode2 = allNodes[(edges[:,1]-1).astype(int),:]

    nodalDistance = np.linalg.norm(edgeNode1-edgeNode2, axis=1)
    edgeDistance = (nodalDistance - (allDiameters[(edges[:,0]-1).\
        astype(int)]/2) - (allDiameters[(edges[:,1]-1).astype(int)])/2)/2


    # Make unit vector from edgeNode 1 to edgeNode2, multiply vector 
    # by sum(agg1 and edgeDistance) and add to edgeNode2
    edgePoints = (edgeNode1-edgeNode2)/np.array([nodalDistance,]*3).T*\
        (np.array([allDiameters[(edges[:,1]-1).astype(int)],]*3).T/2+\
        np.array([edgeDistance,]*3).T)+edgeNode2


    # Form Edge Point List
    edgePoints = np.concatenate(np.split(edgePoints,6),axis=1)

    # Definition of Face Points faceNPoint[Coordinates]

    # Face 1 (Nodes: 2,3,4) 
    faceNodalDistance = np.vstack((np.linalg.norm(allNodes[(allTets[:,1]-1).astype(int),:]-edgePoints[:,15:18], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,2]-1).astype(int),:]-edgePoints[:,12:15], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,3]-1).astype(int),:]-edgePoints[:,9:12], axis=1))).T
    
    faceOffsetDistance = np.vstack(((faceNodalDistance[:,0] - allDiameters[(allTets[:,1]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,1] - allDiameters[(allTets[:,2]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,2] - allDiameters[(allTets[:,3]-1).astype(int)]/2)/2)).T

    facePoints = np.hstack(((allNodes[(allTets[:,1]-1).astype(int),:]-edgePoints[:,15:18])/\
        np.array([faceNodalDistance[:,0],]*3).T\
        *np.array([faceOffsetDistance[:,0],]*3).T + edgePoints[:,15:18],\
        (allNodes[(allTets[:,2]-1).astype(int),:]-edgePoints[:,12:15])/\
        np.array([faceNodalDistance[:,1],]*3).T\
        *np.array([faceOffsetDistance[:,1],]*3).T + edgePoints[:,12:15],\
        (allNodes[(allTets[:,3]-1).astype(int),:]-edgePoints[:,9:12])/\
        np.array([faceNodalDistance[:,2],]*3).T\
        *np.array([faceOffsetDistance[:,2],]*3).T + edgePoints[:,9:12]))

    face1x = (facePoints[:,0]+facePoints[:,3]+facePoints[:,6])/3
    face1y = (facePoints[:,1]+facePoints[:,4]+facePoints[:,7])/3
    face1z = (facePoints[:,2]+facePoints[:,5]+facePoints[:,8])/3

    face1Point = np.vstack((face1x,face1y,face1z)).T

    # Face 2 (Nodes: 1,3,4)
    faceNodalDistance = np.vstack((np.linalg.norm(allNodes[(allTets[:,3]-1).astype(int),:]-edgePoints[:,3:6], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,2]-1).astype(int),:]-edgePoints[:,6:9], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,0]-1).astype(int),:]-edgePoints[:,15:18], axis=1))).T
    
    faceOffsetDistance = np.vstack(((faceNodalDistance[:,0] - allDiameters[(allTets[:,3]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,1] - allDiameters[(allTets[:,2]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,2] - allDiameters[(allTets[:,0]-1).astype(int)]/2)/2)).T

    facePoints = np.hstack(((allNodes[(allTets[:,3]-1).astype(int),:]-edgePoints[:,3:6])/\
        np.array([faceNodalDistance[:,0],]*3).T\
        *np.array([faceOffsetDistance[:,0],]*3).T + edgePoints[:,3:6],\
        (allNodes[(allTets[:,2]-1).astype(int),:]-edgePoints[:,6:9])/\
        np.array([faceNodalDistance[:,1],]*3).T\
        *np.array([faceOffsetDistance[:,1],]*3).T + edgePoints[:,6:9],\
        (allNodes[(allTets[:,0]-1).astype(int),:]-edgePoints[:,15:18])/\
        np.array([faceNodalDistance[:,2],]*3).T\
        *np.array([faceOffsetDistance[:,2],]*3).T + edgePoints[:,15:18]))

    face1x = (facePoints[:,0]+facePoints[:,3]+facePoints[:,6])/3
    face1y = (facePoints[:,1]+facePoints[:,4]+facePoints[:,7])/3
    face1z = (facePoints[:,2]+facePoints[:,5]+facePoints[:,8])/3

    face2Point = np.vstack((face1x,face1y,face1z)).T

    # Face 3 (Nodes: 1,2,4)
    faceNodalDistance = np.vstack((np.linalg.norm(allNodes[(allTets[:,0]-1).astype(int),:]-edgePoints[:,12:15], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,1]-1).astype(int),:]-edgePoints[:,6:9], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,3]-1).astype(int),:]-edgePoints[:,0:3], axis=1))).T
    
    faceOffsetDistance = np.vstack(((faceNodalDistance[:,0] - allDiameters[(allTets[:,0]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,1] - allDiameters[(allTets[:,1]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,2] - allDiameters[(allTets[:,3]-1).astype(int)]/2)/2)).T

    facePoints = np.hstack(((allNodes[(allTets[:,0]-1).astype(int),:]-edgePoints[:,12:15])/\
        np.array([faceNodalDistance[:,0],]*3).T\
        *np.array([faceOffsetDistance[:,0],]*3).T + edgePoints[:,12:15],\
        (allNodes[(allTets[:,1]-1).astype(int),:]-edgePoints[:,6:9])/\
        np.array([faceNodalDistance[:,1],]*3).T\
        *np.array([faceOffsetDistance[:,1],]*3).T + edgePoints[:,6:9],\
        (allNodes[(allTets[:,3]-1).astype(int),:]-edgePoints[:,0:3])/\
        np.array([faceNodalDistance[:,2],]*3).T\
        *np.array([faceOffsetDistance[:,2],]*3).T + edgePoints[:,0:3]))

    face1x = (facePoints[:,0]+facePoints[:,3]+facePoints[:,6])/3
    face1y = (facePoints[:,1]+facePoints[:,4]+facePoints[:,7])/3
    face1z = (facePoints[:,2]+facePoints[:,5]+facePoints[:,8])/3

    face3Point = np.vstack((face1x,face1y,face1z)).T

    # Face 4 (Nodes: 1,2,3)
    faceNodalDistance = np.vstack((np.linalg.norm(allNodes[(allTets[:,2]-1).astype(int),:]-edgePoints[:,0:3], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,1]-1).astype(int),:]-edgePoints[:,3:6], axis=1),\
        np.linalg.norm(allNodes[(allTets[:,0]-1).astype(int),:]-edgePoints[:,9:12], axis=1))).T
    
    faceOffsetDistance = np.vstack(((faceNodalDistance[:,0] - allDiameters[(allTets[:,2]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,1] - allDiameters[(allTets[:,1]-1).astype(int)]/2)/2,\
        (faceNodalDistance[:,2] - allDiameters[(allTets[:,0]-1).astype(int)]/2)/2)).T

    facePoints = np.hstack(((allNodes[(allTets[:,2]-1).astype(int),:]-edgePoints[:,0:3])/\
        np.array([faceNodalDistance[:,0],]*3).T\
        *np.array([faceOffsetDistance[:,0],]*3).T + edgePoints[:,0:3],\
        (allNodes[(allTets[:,1]-1).astype(int),:]-edgePoints[:,3:6])/\
        np.array([faceNodalDistance[:,1],]*3).T\
        *np.array([faceOffsetDistance[:,1],]*3).T + edgePoints[:,3:6],\
        (allNodes[(allTets[:,0]-1).astype(int),:]-edgePoints[:,9:12])/\
        np.array([faceNodalDistance[:,2],]*3).T\
        *np.array([faceOffsetDistance[:,2],]*3).T + edgePoints[:,9:12]))

    face1x = (facePoints[:,0]+facePoints[:,3]+facePoints[:,6])/3
    face1y = (facePoints[:,1]+facePoints[:,4]+facePoints[:,7])/3
    face1z = (facePoints[:,2]+facePoints[:,5]+facePoints[:,8])/3

    face4Point = np.vstack((face1x,face1y,face1z)).T

    # Definition of Tet-Points [Coordinates]
    tetNodalDistance = np.vstack((np.linalg.norm(allNodes[(allTets[:,0]-1).astype(int),:]-face1Point, axis=1),\
        np.linalg.norm(allNodes[(allTets[:,1]-1).astype(int),:]-face2Point, axis=1),\
        np.linalg.norm(allNodes[(allTets[:,2]-1).astype(int),:]-face3Point, axis=1),\
        np.linalg.norm(allNodes[(allTets[:,3]-1).astype(int),:]-face4Point, axis=1))).T     

    tetOffsetDistance = np.vstack(((tetNodalDistance[:,0] - allDiameters[(allTets[:,0]-1).astype(int)]/2)/2,\
        (tetNodalDistance[:,1] - allDiameters[(allTets[:,1]-1).astype(int)]/2)/2,\
        (tetNodalDistance[:,2] - allDiameters[(allTets[:,2]-1).astype(int)]/2)/2,\
        (tetNodalDistance[:,3] - allDiameters[(allTets[:,3]-1).astype(int)]/2)/2)).T

    tetPoints = np.hstack(((allNodes[(allTets[:,0]-1).astype(int),:]-face1Point)/\
        np.array([tetNodalDistance[:,0],]*3).T*\
        np.array([tetOffsetDistance[:,0],]*3).T + face1Point,\
        (allNodes[(allTets[:,1]-1).astype(int),:]-face2Point)/\
        np.array([tetNodalDistance[:,1],]*3).T*\
        np.array([tetOffsetDistance[:,1],]*3).T + face2Point,\
        (allNodes[(allTets[:,2]-1).astype(int),:]-face3Point)/\
        np.array([tetNodalDistance[:,2],]*3).T*\
        np.array([tetOffsetDistance[:,2],]*3).T + face3Point,\
        (allNodes[(allTets[:,3]-1).astype(int),:]-face4Point)/\
        np.array([tetNodalDistance[:,3],]*3).T*\
        np.array([tetOffsetDistance[:,3],]*3).T + face4Point))

    tetx = (tetPoints[:,0]+tetPoints[:,3]+tetPoints[:,6]+tetPoints[:,9])/4
    tety = (tetPoints[:,1]+tetPoints[:,4]+tetPoints[:,7]+tetPoints[:,10])/4
    tetz = (tetPoints[:,2]+tetPoints[:,5]+tetPoints[:,8]+tetPoints[:,11])/4

    tetPoints = np.vstack((tetx,tety,tetz)).T


    # Coordinates for each facet in each tet. Using facet indexing from Cusatis et al. (2011a)
    # Note that edges are defined as:
    # E1 = E12 or edgePoints[:,0:3]
    # E2 = E13 or edgePoints[:,3:6]
    # E3 = E14 or edgePoints[:,6:9]
    # E4 = E23 or edgePoints[:,9:12]
    # E5 = E24 or edgePoints[:,12:15]
    # E6 = E34 or edgePoints[:,15:18]
    facet1  = np.concatenate(([tetPoints,face3Point,edgePoints[:,0:3]]),axis=1)     #(T, F3, E1)
    facet2  = np.concatenate(([tetPoints,face4Point,edgePoints[:,0:3]]),axis=1)     #(T, F4, E1)
    facet3  = np.concatenate(([tetPoints,face2Point,edgePoints[:,3:6]]),axis=1)     #(T, F2, E2)
    facet4  = np.concatenate(([tetPoints,face4Point,edgePoints[:,3:6]]),axis=1)     #(T, F4, E2)
    facet5  = np.concatenate(([tetPoints,face2Point,edgePoints[:,6:9]]),axis=1)     #(T, F2, E3)
    facet6  = np.concatenate(([tetPoints,face3Point,edgePoints[:,6:9]]),axis=1)     #(T, F3, E3)
    facet7  = np.concatenate(([tetPoints,face1Point,edgePoints[:,9:12]]),axis=1)    #(T, F1, E4)
    facet8  = np.concatenate(([tetPoints,face4Point,edgePoints[:,9:12]]),axis=1)    #(T, F4, E4)
    facet9  = np.concatenate(([tetPoints,face1Point,edgePoints[:,12:15]]),axis=1)   #(T, F1, E5)
    facet10 = np.concatenate(([tetPoints,face3Point,edgePoints[:,12:15]]),axis=1)   #(T, F3, E5)
    facet11 = np.concatenate(([tetPoints,face1Point,edgePoints[:,15:18]]),axis=1)   #(T, F1, E6)
    facet12 = np.concatenate(([tetPoints,face2Point,edgePoints[:,15:18]]),axis=1)   #(T, F2, E6)


    # Old version below. Keep for historical purposes for now.
    #facet1  = np.concatenate(([tetPoints,face1Point,edgePoints[:,9:12]]),axis=1)
    #facet2  = np.concatenate(([tetPoints,face1Point,edgePoints[:,12:15]]),axis=1)
    #facet3  = np.concatenate(([tetPoints,face1Point,edgePoints[:,15:18]]),axis=1)
    #facet4  = np.concatenate(([tetPoints,face2Point,edgePoints[:,3:6]]),axis=1)
    #facet5  = np.concatenate(([tetPoints,face2Point,edgePoints[:,6:9]]),axis=1)
    #facet6  = np.concatenate(([tetPoints,face2Point,edgePoints[:,15:18]]),axis=1)
    #facet7  = np.concatenate(([tetPoints,face3Point,edgePoints[:,0:3]]),axis=1)
    #facet8  = np.concatenate(([tetPoints,face3Point,edgePoints[:,6:9]]),axis=1)
    #facet9  = np.concatenate(([tetPoints,face3Point,edgePoints[:,12:15]]),axis=1)
    #facet10 = np.concatenate(([tetPoints,face4Point,edgePoints[:,0:3]]),axis=1)
    #facet11 = np.concatenate(([tetPoints,face4Point,edgePoints[:,3:6]]),axis=1)
    #facet12 = np.concatenate(([tetPoints,face4Point,edgePoints[:,9:12]]),axis=1)

    facetPointData = np.concatenate(([tetPoints,face1Point,face2Point,face3Point,face4Point,edgePoints[:,0:3],edgePoints[:,3:6],edgePoints[:,6:9],edgePoints[:,9:12],edgePoints[:,12:15],edgePoints[:,15:18]]),axis=0)

    # Cell data for each facet in each tet
    facetCellData1  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(len(tetPoints)+1,2*len(tetPoints)+1),np.arange(8*len(tetPoints)+1,9*len(tetPoints)+1))).T
    facetCellData2  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(len(tetPoints)+1,2*len(tetPoints)+1),np.arange(9*len(tetPoints)+1,10*len(tetPoints)+1))).T
    facetCellData3  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(len(tetPoints)+1,2*len(tetPoints)+1),np.arange(10*len(tetPoints)+1,11*len(tetPoints)+1))).T
    facetCellData4  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(2*len(tetPoints)+1,3*len(tetPoints)+1),np.arange(6*len(tetPoints)+1,7*len(tetPoints)+1))).T
    facetCellData5  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(2*len(tetPoints)+1,3*len(tetPoints)+1),np.arange(7*len(tetPoints)+1,8*len(tetPoints)+1))).T
    facetCellData6  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(2*len(tetPoints)+1,3*len(tetPoints)+1),np.arange(10*len(tetPoints)+1,11*len(tetPoints)+1))).T
    facetCellData7  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(3*len(tetPoints)+1,4*len(tetPoints)+1),np.arange(5*len(tetPoints)+1,6*len(tetPoints)+1))).T
    facetCellData8  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(3*len(tetPoints)+1,4*len(tetPoints)+1),np.arange(7*len(tetPoints)+1,8*len(tetPoints)+1))).T
    facetCellData9  = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(3*len(tetPoints)+1,4*len(tetPoints)+1),np.arange(9*len(tetPoints)+1,10*len(tetPoints)+1))).T
    facetCellData10 = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(4*len(tetPoints)+1,5*len(tetPoints)+1),np.arange(5*len(tetPoints)+1,6*len(tetPoints)+1))).T
    facetCellData11 = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(4*len(tetPoints)+1,5*len(tetPoints)+1),np.arange(6*len(tetPoints)+1,7*len(tetPoints)+1))).T
    facetCellData12 = np.vstack((np.arange(1,len(tetPoints)+1),np.arange(4*len(tetPoints)+1,5*len(tetPoints)+1),np.arange(8*len(tetPoints)+1,9*len(tetPoints)+1))).T

    facetCellData = np.concatenate(([facetCellData1,facetCellData2,facetCellData3,facetCellData4,facetCellData5,facetCellData6,\
        facetCellData7,facetCellData8,facetCellData9,facetCellData10,facetCellData11,facetCellData12]),axis=0)-1


    # Combination of nonrepeating facets for general tet (12)
    tetFacets = np.concatenate(([facet1,facet2,facet3,facet4,facet5,facet6,\
        facet7,facet8,facet9,facet10,facet11,facet12]),axis=1)
    facets = tetFacets.reshape(-1,9)

    threes = 3*np.array([np.ones((len(facets)))]).T

    # Calculate the center of each facet
    facetCenters = np.array((facets[:,0]+facets[:,3]+facets[:,6],\
        facets[:,1]+facets[:,4]+facets[:,7],\
        facets[:,2]+facets[:,5]+facets[:,8])).T/threes

    # Calculate the area of each facet
    vectorAB = np.array((tetFacets.reshape(-1,9)[:,3]-\
        tetFacets.reshape(-1,9)[:,0],tetFacets.reshape(-1,9)[:,4]-\
        tetFacets.reshape(-1,9)[:,1],tetFacets.reshape(-1,9)[:,5]-\
        tetFacets.reshape(-1,9)[:,2])).T
    vectorAC = np.array((tetFacets.reshape(-1,9)[:,6]-\
        tetFacets.reshape(-1,9)[:,0],tetFacets.reshape(-1,9)[:,7]-\
        tetFacets.reshape(-1,9)[:,1],tetFacets.reshape(-1,9)[:,8]-\
        tetFacets.reshape(-1,9)[:,2])).T
    facetAreas = 0.5 * np.linalg.norm(np.cross(vectorAB,vectorAC),axis=1)
    
    # Calculate the normal of each facet
    facetNormals = np.cross(vectorAB,vectorAC)/np.array([np.linalg.norm\
        (np.cross(vectorAB,vectorAC),axis=1),]*3).T

    # Specify tet-node connectivity for facets (i.e. facet 0 connected by node 0 and 1)
    tetn1 = [0,0,0,0,0,0,1,1,1,1,2,2]
    tetn2 = [1,1,2,2,3,3,2,2,3,3,3,3]

    return tetFacets, facetCenters, facetAreas, facetNormals, \
        tetn1, tetn2, tetPoints, allDiameters, facetPointData, facetCellData





