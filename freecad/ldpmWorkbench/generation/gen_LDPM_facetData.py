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


def _normalize_phase_mode(phaseMode):
    if phaseMode is None:
        return 3
    if isinstance(phaseMode, str):
        text = phaseMode.strip().lower().replace(" ", "")
        if text.startswith("2"):
            return 2
        if text.startswith("3"):
            return 3
        raise ValueError(f"Unknown phaseMode string: {phaseMode!r}")
    mode = int(phaseMode)
    if mode not in (2, 3):
        raise ValueError(f"phaseMode must be 2 or 3; got {phaseMode!r}")
    return mode


def _rule_interface_materials(materialRule, phaseMode):
    tables = {
        1: (3, 3, 1),
        2: (3, 3, 2),
        3: (3, 2, 1),
        4: (3, 2, 2),
        5: (1, 3, 1),
        6: (1, 3, 2),
        7: (1, 2, 1),
        8: (1, 2, 2),
    }
    old_agg_itz, old_agg_binder, old_itz_binder = tables[materialRule]
    if phaseMode == 2:
        remap = {1: 2, 2: 2, 3: 1}
        return remap[old_agg_itz], remap[old_agg_binder], remap[old_itz_binder]
    remap = {1: 2, 2: 3, 3: 1}
    return remap[old_agg_itz], remap[old_agg_binder], remap[old_itz_binder]


def _pick_by_volume(m1, m2, vol1, vol2):
    if vol1 == vol2:
        return m1
    if vol1 > vol2:
        return m1
    return m2


def gen_LDPM_facetData(allNodes,allTets,tetFacets,facetCenters,\
    facetAreas,facetNormals,tetn1,tetn2,materialList,materialRule,\
    multiMaterial,cementStructure,edgeMaterialList,facetCellData,particleID,
    phaseMode=3):

    mode = _normalize_phase_mode(phaseMode)

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
    facetData = np.empty([len(allTets)*12,19])

    # Initialize a matrix for facet material information
    facetMaterial = np.empty([len(allTets)*12,])

    # Initialize a matrix for particle material information
    particleMaterial = np.empty([len(allTets)*12,2])

    # Initialize a matrix for particle material ID information
    particleIDs = np.empty([len(allTets)*12,2]) 

    facetCellData = (facetCellData.reshape(-1,3)).astype(int)

    for x in range(0,len(allTets)):

        for y in range(0,12):

            # [Tet Nodes:(IDx IDy IDz) Vol pArea Centers:(cx cy cz) pNormals:(px py pz) pTan1:(qx qy qz) pTan2:(sx sy sz) mF]
            # Note that the order of the facets is Tet 1 (Facet 1-12),Tet 2 (Facet 1-12),...,Tet N (Facet 1-12)
            facetData[12*x+y,0]     = x                       # Tet ID      
            facetData[12*x+y,1:4]   = np.array([3*(12*x+y), 3*(12*x+y)+1, 3*(12*x+y)+2]) # Global Facet Vertex ID
            facetData[12*x+y,4]     = subtetVol[12*x+y]       # Subtet Volume
            facetData[12*x+y,5]     = pArea[12*x+y]           # Projected Facet Area
            facetData[12*x+y,6:9]   = facetCenters[12*x+y,:]  # Facet Centroid
            facetData[12*x+y,9:12]  = pn[12*x+y,:]            # Projected Facet Normal
            facetData[12*x+y,12:15] = ptan1[12*x+y,:]         # Projected Tangent 1
            facetData[12*x+y,15:18] = ptan2[12*x+y,:]         # Projected Tangent 2

            # Store particle materials
            particleMaterial[12*x+y,0] = materialList[allTets[x,tetn1[y]].astype(int)-1].astype(int)
            particleMaterial[12*x+y,1] = materialList[allTets[x,tetn2[y]].astype(int)-1].astype(int)

            particleIDs[12*x+y,0] = particleID[allTets[x,tetn1[y]].astype(int)-1].astype(int)
            particleIDs[12*x+y,1] = particleID[allTets[x,tetn2[y]].astype(int)-1].astype(int)

            m1 = int(particleMaterial[12*x+y,0])
            m2 = int(particleMaterial[12*x+y,1])
            vol1 = facetVol1[12*x+y]
            vol2 = facetVol2[12*x+y]
            pid1 = int(particleIDs[12*x+y,0])
            pid2 = int(particleIDs[12*x+y,1])

            # Material Flag           
            if multiMaterial in ['off','Off','N','n','No','no']:
                facetData[12*x+y,18]    = 0                       # Material Flag 
                facetMaterial[12*x+y]   = 0                       # Material Flag

            else:

                if materialRule == 9 or materialRule == 10:
                    if (pid1 != pid2) and (pid1 > 0) and (pid2 > 0):
                        facet_mat = 2
                    elif m1 == m2:
                        facet_mat = m1
                    else:
                        facet_mat = _pick_by_volume(m1, m2, vol1, vol2)
                    facetData[12*x+y,18] = facet_mat
                    facetMaterial[12*x+y] = facet_mat

                elif materialRule > 0 and materialRule <= 8:

                    aggITZ, aggBinder, itzBinder = _rule_interface_materials(materialRule, mode)

                    if m1 == m2:
                        facet_mat = m1
                    elif mode == 2:
                        pair = {m1, m2}
                        if pair == {1, 2}:
                            facet_mat = aggBinder
                        else:
                            facet_mat = _pick_by_volume(m1, m2, vol1, vol2)
                    else:
                        pair = {m1, m2}
                        if pair == {1, 2}:
                            facet_mat = aggITZ
                        elif pair == {1, 3}:
                            facet_mat = aggBinder
                        elif pair == {2, 3}:
                            facet_mat = itzBinder
                        else:
                            facet_mat = _pick_by_volume(m1, m2, vol1, vol2)

                    facetData[12*x+y,18] = facet_mat
                    facetMaterial[12*x+y] = facet_mat

                else:

                    facetData[12*x+y,18] = 0
                    facetMaterial[12*x+y] = 0              

    return facetData,facetMaterial,subtetVol,facetVol1,facetVol2,particleMaterial
