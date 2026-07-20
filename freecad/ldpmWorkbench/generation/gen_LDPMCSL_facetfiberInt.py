## ===========================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2024 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be
## found in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ===========================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
##
## ===========================================================================
##
## Calculate the intersection of fiber with facets
##
## ===========================================================================

import numpy as np
import math


def gen_LDPMCSL_facetfiberInt(p1Fiber,p2Fiber,dFiber,lFiber,orienFibers,\
        geoName,allTets,allNodes,tetFacets,dataList,tetn1,tetn2,facetNormals,facetCenters):
    
    # Number of total fiber
    NumberofFibers = len(p1Fiber[:,1])
    #print('NumberofFibers',NumberofFibers)
    # Initialize a data array and matrix for interseted fiber
    FiberdataList = []
    ProjectedFacet = []
    FibertetList = []
    IntersectedFiber = []
    No = 0.0
    TotalTet = 0.0
    TotalFiber = 0.0
    
    tets_coords = allNodes[allTets.astype(int) - 1]  # shape (numTets,4,3)
    tets_min = np.min(tets_coords, axis=1)            # shape (numTets, 3)
    tets_max = np.max(tets_coords, axis=1)            # shape (numTets, 3)
    
    lFiber = lFiber.reshape(-1, 1)
    
    # box of fiber
    # fibers_min = np.minimum(p1Fiber, p2Fiber) - (lFiber + dFiber)  # → (25465, 3)
    # fibers_max = np.maximum(p1Fiber, p2Fiber) + (lFiber + dFiber)
    
    fibers_min = np.minimum(p1Fiber, p2Fiber)
    fibers_max = np.maximum(p1Fiber, p2Fiber)
    
    # print("fibers_min shape:", fibers_min.shape)
    # print("tets_max shape:", tets_max.shape)
    
    
    group_size = 5000  # you can tune this value based on memory
    total_fibers = p1Fiber.shape[0]
    all_pairs = []

    for i in range(0, total_fibers, group_size):
        fm = fibers_min[i:i + group_size]
        fM = fibers_max[i:i + group_size]

        # Expand dims for broadcasting
        fm_exp = fm[:, None, :]         # (F, 1, 3)
        fM_exp = fM[:, None, :]         # (F, 1, 3)
        tmin_exp = tets_min[None, :, :] # (1, T, 3)
        tmax_exp = tets_max[None, :, :] # (1, T, 3)

        overlap = np.all((fm_exp <= tmax_exp) & (fM_exp >= tmin_exp), axis=2)  # (C, T)

        tet_idx, fiber_idx = np.where(overlap.T)  # get (T, C) and transpose
        fiber_idx += i  # adjust index to original fiber range

        if len(fiber_idx) > 0:
            # all_pairs.append(np.column_stack((fiber_idx,tet_idx)))
            all_pairs.append(np.column_stack((tet_idx, fiber_idx)))

    # Combine all into final array
    if all_pairs:
        FibertetList = np.vstack(all_pairs)
        FibertetList = FibertetList[FibertetList[:, 0].argsort()]
    else:
        FibertetList = np.empty((0, 2), dtype=int)

    # print("FibertetList shape:", FibertetList.shape)

    
    #######################################################
    # For fiberfacet using Matthew's rotational matrix

    # Store facets as set of three points
    facets = tetFacets.reshape(-1,9)

    # Store particles accociated with facets
    p1 = allNodes[(allTets[:,tetn1]-1).astype(int),:].reshape(-1,3)
    p2 = allNodes[(allTets[:,tetn2]-1).astype(int),:].reshape(-1,3)


    # Projected facet normal
    pn = (p2-p1)/np.array([np.linalg.norm(p2-p1,axis=1),]*3).T
    pn = pn.reshape(-1,3)
    #print('n',pn)


    dot_check = np.einsum('ij,ij->i', pn, facetNormals[:, 0:3])
    negative_idx = dot_check < 0

    facetNormals[negative_idx] *= -1
    facets[negative_idx] = facets[negative_idx][:,[0,1,2,6,7,8,3,4,5]]
    
    
    
    # Formation of rotation stacked matrix (nFacets x 3 x 3)
    
    v = np.cross(facetNormals, pn.reshape(-1,3))               # (n, 3)
    v_norm_sq = np.sum(v**2, axis=1)                           # (n,)
    v_norm_sq[v_norm_sq == 0] = 1.0                            # avoid div by zero

    # Skew symmetric matrices, shape (n,3,3)
    ssc = np.zeros((len(v), 3, 3))
    ssc[:, 0, 1] = -v[:, 2]
    ssc[:, 0, 2] = v[:, 1]
    ssc[:, 1, 0] = v[:, 2]
    ssc[:, 1, 2] = -v[:, 0]
    ssc[:, 2, 0] = -v[:, 1]
    ssc[:, 2, 1] = v[:, 0]

    # dot product of normals (cos theta)
    cos_theta = np.einsum('ij,ij->i', facetNormals, pn.reshape(-1,3))  # (n,)
    cos_theta = cos_theta[:, None, None]  # (n,1,1) — one reshape only!

    I = np.broadcast_to(np.eye(3), (len(v), 3, 3))  # (n,3,3)

    ssc_ssc = np.matmul(ssc, ssc)  # (n,3,3)

    v_norm_sq = v_norm_sq[:, None, None]  # (n,1,1)

    # Rodrigues rotation formula:
    R = I + ssc + ssc_ssc * (1 - cos_theta) / v_norm_sq  # (n,3,3)
    


    # Make vectors from center to corners of the facets
    vectorOA = np.expand_dims(facetCenters[:,0:3]-facets[:,0:3], axis=2)
    vectorOB = np.expand_dims(facetCenters[:,0:3]-facets[:,3:6], axis=2)
    vectorOC = np.expand_dims(facetCenters[:,0:3]-facets[:,6:9], axis=2)

    R_T = R.transpose(0, 2, 1)
    pvectorOA = np.squeeze(np.matmul(R_T, vectorOA))  # (n,3)
    pvectorOB = np.squeeze(np.matmul(R_T, vectorOB))
    pvectorOC = np.squeeze(np.matmul(R_T, vectorOC))
    
    RcoordP1= facetCenters-pvectorOA
    RcoordP2= facetCenters-pvectorOB
    RcoordP3= facetCenters-pvectorOC

    # Compute the plane supporting the triangle (coordP1, coordP2, coordP3)  normal: nprojectedfacet offset: d
    vector12 = RcoordP2-RcoordP1
    vector23 = RcoordP3-RcoordP2
    vector13 = RcoordP3-RcoordP1
    vector31 = RcoordP1-RcoordP3

    Normal = np.cross(vector12,vector13)/np.array([np.linalg.norm(np.cross(vector12,vector13),axis=1),]*3).T

    RcoordP1=np.array(RcoordP1).reshape(-1,3)
    RcoordP2=np.array(RcoordP2).reshape(-1,3)
    RcoordP3=np.array(RcoordP3).reshape(-1,3)
    vector12=np.array(vector12).reshape(-1,3)
    vector31=np.array(vector31).reshape(-1,3)
    vector23=np.array(vector23).reshape(-1,3)
    vector13=np.array(vector13).reshape(-1,3)
    Normal=np.array(Normal).reshape(-1,3)
    projectedFacet = np.concatenate((RcoordP1,RcoordP2,RcoordP3))
    
    # print("Alltet shape:", allTets.shape)
    # print("Normal shape:", Normal.shape)
    # print("max x tet", np.max(FibertetList[:, 0]))
    # print("max z fiber", np.max(FibertetList[:, 1]))

    for i in range(0,len(FibertetList)):
        

        x=int(FibertetList[i,0])
        z=int(FibertetList[i,1])

        TotalTet = TotalTet + 1    
        
        
        # print("i ", i," x ",x," z ",z)
        
        p12 = p2Fiber[z] - p1Fiber[z]
        p1 = p1Fiber[z]


        # Check the intersection of this inside fiber with 12 facsets of tet
        for y in range(0,12):


            normal_idx = 12 * x + y

            # Normal and origin of the facet
            normal_vec = Normal[normal_idx]
            coord_vec = RcoordP1[normal_idx]
            vector12_vec = vector12[normal_idx]
            
            offsetd = -np.dot(normal_vec, coord_vec)
                
            # Dot products for all fibers
            facetnormalDotp12Fiber = np.dot(normal_vec, p12)
            facetnormalDotp1Fiber = np.dot(normal_vec, p1)

            # Ignore line parallel to (or lying in) the plane
            if abs(facetnormalDotp12Fiber) > 0.0:
                t = - (offsetd + facetnormalDotp1Fiber)/facetnormalDotp12Fiber

            # Check if the intersection point is between p1Fiber and p2Fiber
                if t >= 0.0 and t <= 1.0:
            
                    P = p1 + t * p12
                    PP1 = P - RcoordP1[normal_idx]
                    N12 = np.cross(vector12[normal_idx], PP1)
                    CheckEdge1 = np.dot(normal_vec, N12)

                    if (CheckEdge1>=0):

                        PP2 = P - RcoordP2[normal_idx]
                        N23 = np.cross(vector23[normal_idx], PP2)
                        CheckEdge2 = np.dot(normal_vec, N23)

                        if (CheckEdge2>=0):

                            PP3 = P - RcoordP3[normal_idx]
                            N31 = np.cross(vector31[normal_idx], PP3)
                            CheckEdge3 = np.dot(normal_vec, N31)
                        
                            if (CheckEdge3>=0):

                                # Determination of Short and Long lenght of fiber intersected facet
                                
                                IntersectedFiber.append(np.array([z]))
                                No += 1
                                dist_p1 = np.linalg.norm(P - p1Fiber[z])
                                dist_p2 = np.linalg.norm(P - p2Fiber[z])
                                
                                FiberShortLength = min(dist_p1, dist_p2)
                                FiberLongLength = max(dist_p1, dist_p2)

                                tetindex = x+1
                                facetindex = y+1
                                InterPerFacet = 1.0
                                OneIntersectedFiber = np.array([tetindex, facetindex, orienFibers[z,0], orienFibers[z,1], orienFibers[z,2],\
                                    FiberShortLength, FiberLongLength, dFiber, InterPerFacet])
                                FiberdataList.append(OneIntersectedFiber)
                                
            TotalIntersections = No


    # Convert to NumPy array only once and reshape
    FiberdataList = np.reshape(np.asarray(FiberdataList), (-1, 9))
    FiberdataList = FiberdataList[np.lexsort(FiberdataList[:, ::-1].T)]
    IntersectedFiber = np.unique(IntersectedFiber)
    TotalFiber = IntersectedFiber.size
    #print('TotalFiber',TotalFiber)
    #print(IntersectedFiber)


    for k in range(1,len(FiberdataList)):
        if ((FiberdataList[k,0]==FiberdataList[k-1,0]) and (FiberdataList[k,1]==FiberdataList[k-1,1])):
            FiberdataList[k,8] = FiberdataList[k-1,8] + 1
    
    
    MaxInterPerFacet = np.max(FiberdataList[:,8])

    return FiberdataList,TotalIntersections,MaxInterPerFacet,TotalTet,TotalFiber,IntersectedFiber,projectedFacet    

