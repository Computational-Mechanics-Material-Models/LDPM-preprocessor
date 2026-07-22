## ================================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be found
## in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ================================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ================================================================================
##
## This file contains the function to generate the facet data
##
## ================================================================================

import numpy as np





def gen_CSL_facetData(allNodes,allEdges,allTets,tetFacets,facetCenters,\
    facetAreas,facetNormals,tetn1,tetn2,materialList,materialRule,\
    multiMaterial,cementStructure,edgeMaterialList,facetCellData):
  
    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - allNodes:        (x, y, z) coordinates of each node
    - allTets:         (n1, n2, n3, n4) node numbers of each tet
    - tetFacets:       Coordinates of each facet
    - facetCenters:    (x, y, z) coordinates of each facet center
    - facetAreas:      area of each facet
    - facetNormals:    (x, y, z) direction of each facet normal
    - tetn1:           number of the first node
    - tetn2:           number of the second node
    - materialList:    list of materials
    - materialRule:    material rule
    - multiMaterial:   boolean value that is True if the material rule is multi-material
    - cementStructure: boolean value that is True if the material rule is cement structure
    - edgeMaterialList:list of edge materials
    - facetCellData:   list of facet cell data
    --------------------------------------------------------------------------
    ### Outputs ###
    - facetData:       datastructure with all facet data
    - facetMaterial:   material of each facet
    - subtetVol:       volume of each subtet
    - facetVol1:       volume of each facet pyramid 1
    - facetVol2:       volume of each facet pyramid 2
    - particleMaterial:material of each particle
    --------------------------------------------------------------------------
    """  


    facets = tetFacets.reshape(-1, 9)
    p1 = allNodes[(allTets[:, tetn1] - 1).astype(int), :].reshape(-1, 3)
    p2 = allNodes[(allTets[:, tetn2] - 1).astype(int), :].reshape(-1, 3)

    # Projected facet normal
    pn = (p2 - p1) / np.linalg.norm(p2 - p1, axis=1).reshape(-1, 1)

    InitialNormal = np.empty((len(allTets) * 12, 3))
    coords = np.empty((len(allTets) * 12, 3, 3))

    k = 0
    for i in range(len(allTets)):
        for j in range(12):
            Check = np.dot(pn[12 * i + j], facetNormals[12 * i + j])
            if Check < 0:
                InitialNormal[k] = -1 * facetNormals[12 * i + j]
                coords[k, 0] = facets[12 * i + j, 0:3]
                coords[k, 1] = facets[12 * i + j, 6:9]
                coords[k, 2] = facets[12 * i + j, 3:6]
            else:
                InitialNormal[k] = facetNormals[12 * i + j]
                coords[k, 0] = facets[12 * i + j, 0:3]
                coords[k, 1] = facets[12 * i + j, 3:6]
                coords[k, 2] = facets[12 * i + j, 6:9]
            k += 1

    InitialNormal=np.array(InitialNormal).reshape(-1,3)
    coords = np.array(coords).reshape(-1,9)
    facetNormals=InitialNormal
    facets = coords.reshape(-1,9)


    # Formation of rotation stacked matrix (3 x 3 x nFacets)
    v = np.cross(facetNormals,pn.reshape(-1,3))
    zeros = np.zeros(len(v),)
    ssc = np.array(([[zeros, -v[:,2], v[:,1]],[ v[:,2], zeros, -v[:,0]],\
        [ -v[:,1], v[:,0], zeros]]))
    identity = np.dstack([np.eye(3)]*len(v))
    mulNormalsPn = np.matmul(np.expand_dims(pn.reshape(-1,3), axis=1),np.expand_dims(facetNormals, axis=2)).T
    numer = (np.matmul(ssc.T,ssc.T).T)*(1-mulNormalsPn)
    denom = (np.matmul(np.expand_dims(v.reshape(-1,3), axis=1),np.expand_dims(v, axis=2)).T)
    used_for_R = np.zeros_like(numer)
    np.divide(numer, denom, out=used_for_R, where=np.abs(denom) > 1e-15)

    R = identity + ssc + used_for_R


    # Clear not needed variables from memory
    del Check
    del v
    del zeros
    del identity
    del mulNormalsPn
    del ssc        

    # Generate a random vector of size n x 3
    r = np.random.rand(facetNormals.shape[0], 3)

    # Make vectors that are orthogonal to the facet normal   
    tan1 = np.cross(facetNormals,r)/np.array([np.linalg.norm(np.cross(facetNormals,r),axis=1),]*3).T
    tan1 = np.expand_dims(tan1, axis=2)
    
    # Define 1st projected tangential
    ptan1 = np.squeeze(np.matmul(np.transpose(R.T,(0, 2, 1)),tan1))/\
        np.array([np.linalg.norm(np.squeeze(np.matmul(np.transpose(R.T,\
            (0, 2, 1)),tan1)),axis=1),]*3).T

    # Define 2nd projected tangential
    ptan2 = np.cross(pn,ptan1)/np.array([np.linalg.norm(np.cross(pn,ptan1),\
        axis=1),]*3).T

    # Store only the edge point of the facets
    edgePoints = tetFacets.reshape(-1, 9)[:,6:9]

    # Make a vector from the facet edge point to the facet center
    edgeToCenter = edgePoints - facetCenters

    # Rotate the vector to the new coordinate system
    edgeToCenterRot = np.squeeze(np.matmul(np.transpose(R.T,(0, 2, 1)),\
        np.expand_dims(edgeToCenter, axis=2)))
    
    # Store the new center coordinates from the rotatation
    projectedFacetCenters = edgePoints - edgeToCenterRot

    # Sub-tet Volume
    coord1 = facets[:,0:3]
    coord2 = facets[:,3:6]
    coord3 = facets[:,6:9]
    volCalc1 = np.expand_dims(np.transpose(coord1-p1).T, axis=1)
    volCalc2 = np.expand_dims(np.transpose(np.cross((coord2-p1),\
        (coord3-p1))).T, axis=2)
    volCalc3 = np.expand_dims(np.transpose(coord1-p2).T, axis=1)
    volCalc4 = np.expand_dims(np.transpose(np.cross((coord2-p2),\
        (coord3-p2))).T, axis=2)
    facetVol1 = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6)
    facetVol2 = np.squeeze(abs(np.matmul(volCalc3,volCalc4))/6)
    subtetVol = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6 \
        + abs(np.matmul(volCalc3,volCalc4))/6)




    # Clear not needed variables from memory
    del R
    del tan1
    del coord1
    del coord2
    del coord3
    del p1
    del p2
    del volCalc1
    del volCalc2
    del volCalc3
    del volCalc4

    # Projected Area
    areaCalc1 = np.squeeze(np.matmul(np.expand_dims(facetNormals, axis=1),\
        np.expand_dims(pn, axis=2)))
    areaCalc2 = np.linalg.norm(facetNormals, axis=1)\
        *np.linalg.norm(pn, axis=1)
    pArea = abs(areaCalc1/areaCalc2*facetAreas)

    # Initialize a data matrix for all facet data
    facetData = np.empty([len(allTets)*12,24])

    # Initialize a matrix for facet material information
    facetMaterial = np.empty([len(allTets)*12,])

    # Initialize a matrix for particle material information
    particleMaterial = np.empty([len(allTets)*12,2])


    

    facetCellData = (facetCellData.reshape(-1,3)).astype(int)


    edges = np.concatenate(((allTets[:, tetn1] - 1).astype(int).reshape(-1, 1),(allTets[:, tetn2] - 1).astype(int).reshape(-1, 1)),axis=1)

    for x in range(0,len(allTets)):

        for y in range(0,12):

            # Find the column index where the row in allEdges matches edges[12*x+y,:]
            nodeA=list(np.where((allEdges.astype(int)-1 == edges[12*x+y,:]).all(axis=1))[0])
            nodeB=list(np.where((allEdges.astype(int)-1 == np.flip(edges[12*x+y,:])).all(axis=1))[0])

            edgeID = int(np.asarray(nodeA+nodeB).astype(int))
            
            # [Edge Tet Vertices:(IDx IDy IDz) Vol pArea Projected Center:(cx cy cz) Polygon Center:(Cx Cy Cz) pAreaT pNormals:(px py pz) pTan1:(qx qy qz) pTan2:(sx sy sz) mF]
            # Note that the order of the facets is Tet 1 (Facet 1-12),Tet 2 (Facet 1-12),...,Tet N (Facet 1-12)
            facetData[12*x+y,0]     = edgeID                  # Edge ID  
            facetData[12*x+y,1]     = x                       # Tet ID
            facetData[12*x+y,2:5]   = np.array([3*(12*x+y), 3*(12*x+y)+1, 3*(12*x+y)+2]) # Global Facet Vertex ID
            facetData[12*x+y,5]     = subtetVol[12*x+y]       # Subtet Volume
            facetData[12*x+y,6]     = pArea[12*x+y]           # Projected Facet Area
            facetData[12*x+y,7:10]  = projectedFacetCenters[12*x+y,:]  # Facet Centroid (projected)
            facetData[12*x+y,10:13] = 0                       # Centroid of all edge facets (goes here, calculated below)         
            facetData[12*x+y,13]    = 0                       # Area of all edge facets (goes here, calculated below)
            facetData[12*x+y,14:17] = pn[12*x+y,:]            # Projected Facet Normal
            facetData[12*x+y,17:20] = ptan1[12*x+y,:]         # Projected Tangent 1
            facetData[12*x+y,20:23] = ptan2[12*x+y,:]         # Projected Tangent 2
            facetData[12*x+y,23]    = 0                       # Material Flag (Coming Soon)

    # Sort the facet data by edge ID
    facetData = facetData[facetData[:, 0].argsort()]

    # Find maximum Edge ID
    maxEdgeID = int(np.max(facetData[:,0]))



    # Calculate the centroid of all facets for each edge, weighted based on projected area (pArea)
    for x in range(0,maxEdgeID+1):
                
        # Find the row indices where the edge ID matches the edge ID in facetData
        edgeRows = list(np.where(facetData[:,0] == x)[0])

        # Find the sum of the centroids (weighted) of all facets for the edge
        edgeCentroidSum = np.sum(facetData[edgeRows,7:10]*np.expand_dims(facetData[edgeRows,6], axis=1), axis=0)

        # Find the sum of the projected area of all facets for the edge
        edgeAreaSum = np.sum(facetData[edgeRows,6])

        # Assign the area of all facets for the edge to the area column in facetData
        facetData[edgeRows,13] = edgeAreaSum

        # Find the centroid of all facets for the edge
        edgeCentroid = edgeCentroidSum/edgeAreaSum

        # Assign the centroid of all facets for the edge to the centroid column in facetData
        facetData[edgeRows,10:13] = edgeCentroid           

    return facetData,facetMaterial,subtetVol,facetVol1,facetVol2,particleMaterial
