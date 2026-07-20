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
## Primary Authors: Hao Yin, Matthew Troemner
## ===========================================================================
##
## This function generates the flow edges for the LDPM or CSL model.
##
## ===========================================================================

import numpy as np

from freecad.ldpmWorkbench.generation.check_LDPMCSL_pointInside     import check_LDPMCSL_pointInside


def gen_LDPMCSL_flowEdges(htcLength,allNodes,allTets,tetPoints,maxPar,\
                meshVertices,meshTets,coord1,coord2,coord3,coord4,maxC):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - htcLength:        Length of the surface element extensions
    - allNodes:         Array of all nodes in the model
    - allTets:          Array of all tetrahedrons in the model
    - tetPoints:        Array of all tetrahedron points in the model
    - maxPar:           Maximum particle size
    - meshVertices:     Array of all mesh vertices in the model
    - meshTets:         Array of all mesh tetrahedrons in the model
    - coord1:           Coordinates of the first vertex of each tet
    - coord2:           Coordinates of the second vertex of each tet
    - coord3:           Coordinates of the third vertex of each tet
    - coord4:           Coordinates of the fourth vertex of each tet
    - maxC:             Maximum extents
    --------------------------------------------------------------------------
    ### Outputs ###
    - edgeData:         Array of all flow edges in the model
    --------------------------------------------------------------------------
    """      



    # Generate list of all faces in mesh
    faces = np.sort(np.concatenate((np.vstack((allTets[:,0],allTets[:,1],allTets[:,2])).transpose(),\
        np.vstack((allTets[:,0],allTets[:,1],allTets[:,3])).transpose(),\
        np.vstack((allTets[:,0],allTets[:,2],allTets[:,3])).transpose(),\
        np.vstack((allTets[:,1],allTets[:,2],allTets[:,3])).transpose())),axis=1)

    # Generate list of unique faces in mesh
    ufaces, inverse, unique_counts = np.unique(faces,return_inverse=True,return_counts=True,axis=0)

    outerFace = np.zeros(len(ufaces))
    innerFace = np.zeros([len(ufaces),2])

    outerFaceID = np.zeros(len(ufaces))
    innerFaceID = np.zeros([len(ufaces),2])

    j = 0
    k = 0

    for i in range(0,len(ufaces)):

        location = np.where(inverse==i)[0]

        if len(location) == 1:

            outerFaceID[j] = location[0]

            if location[0] < len(faces)/4:
                outerFace[j] = int(location[0])
            elif location[0] < 2*len(faces)/4:
                outerFace[j] = int(location[0] - len(faces)/4)
            elif location[0] < 3*len(faces)/4:
                outerFace[j] = int(location[0] - 2*len(faces)/4)
            else:
                outerFace[j] = int(location[0] - 3*len(faces)/4)
            j = j+1

        else:
            for x in range(0,2):

                innerFaceID[k,x] = location[x]

                if location[x] < len(faces)/4:
                    innerFace[k,x] = int(location[x])
                elif location[x] < 2*len(faces)/4:
                    innerFace[k,x] = int(location[x] - len(faces)/4)
                elif location[x] < 3*len(faces)/4:
                    innerFace[k,x] = int(location[x] - 2*len(faces)/4)
                else:
                    innerFace[k,x] = int(location[x] - 3*len(faces)/4)
            k = k+1

    # Trim extra rows of zeros
    outerFace = np.trim_zeros(outerFace)
    innerFace = innerFace[~np.all(innerFace == 0, axis=1)]

    outerFaceID = np.trim_zeros(outerFaceID)
    innerFaceID = innerFaceID[~np.all(innerFaceID == 0, axis=1)]

    # Vectors of sides of faces (for area calc)
    # Case 1
    c1v1 = allNodes[(faces[innerFaceID[:,0].astype(int),:][:,1]-1).astype(int),:]-allNodes[(faces[innerFaceID[:,0].astype(int),:][:,0]-1).astype(int),:]
    c1v2 = allNodes[(faces[innerFaceID[:,0].astype(int),:][:,2]-1).astype(int),:]-allNodes[(faces[innerFaceID[:,0].astype(int),:][:,0]-1).astype(int),:]
    # Case 2/3
    c2v1 = allNodes[(faces[outerFaceID.astype(int),:][:,1]-1).astype(int),:]-allNodes[(faces[outerFaceID.astype(int),:][:,0]-1).astype(int),:]
    c2v2 = allNodes[(faces[outerFaceID.astype(int),:][:,2]-1).astype(int),:]-allNodes[(faces[outerFaceID.astype(int),:][:,0]-1).astype(int),:]
    # Combined Vectors
    v1 = np.concatenate((c1v1,c2v1,c2v1))
    v2 = np.concatenate((c1v2,c2v2,c2v2))

    # Edge element points
    # Case 1: Two Tet Points
    case1Points = np.concatenate((tetPoints[(innerFace[:,0]).astype(int)],tetPoints[(innerFace[:,1]).astype(int)]),axis=1)
    # Case 2: Tet Point to Face Point
    case2Points = np.concatenate(((allNodes[(faces[outerFaceID.astype(int),:][:,0]-1).astype(int),:]+allNodes[(faces[outerFaceID.astype(int),:][:,1]-1).astype(int),:]+allNodes[(faces[outerFaceID.astype(int),:][:,2]-1).astype(int),:])/3,tetPoints[(outerFace).astype(int),:]),axis=1)
    # Case 3: Face Point to Extension
    case3Points = np.empty([len(case2Points),6])

    for x in range(len(case2Points)):
        option1 = np.concatenate((case2Points[x,0:3],htcLength*(np.cross(c2v1[x,:],c2v2[x,:]))/np.array([np.linalg.norm(np.cross(c2v1[x,:],c2v2[x,:])),]*3).T+case2Points[x,0:3]))
    
        # Obtain extents for floating bin
        binMin = option1[3:6]-maxPar
        binMax = option1[3:6]+maxPar

        # Check if point is inside the mesh         
        inside = check_LDPMCSL_pointInside(meshVertices,meshTets,option1[3:6],\
            binMin,binMax,coord1,coord2,coord3,coord4)


        if inside == True:
            case3Points[x,:] = np.concatenate((case2Points[x,0:3],htcLength*(np.cross(c2v2[x,:],c2v1[x,:]))/np.array([np.linalg.norm(np.cross(c2v2[x,:],c2v1[x,:])),]*3).T+case2Points[x,0:3]))

        else:
            case3Points[x,:] = option1


    # Position of internal face centers (Correction: this point should be the intersection of line T1T2 and face)
    # ref: http://geomalgorithms.com/a05-_intersect-1.html
    inCenter = np.zeros([case1Points.shape[0],3])
    for i in range(0,case1Points.shape[0]):
        normals = (np.cross(v1,v2))/np.array([np.linalg.norm(np.cross(v1,v2),axis=1),]*3).T # case 1,2 normals
        n = np.copy(normals)[i,:]
        wvector = case1Points[i,0:3] - allNodes[(faces[innerFaceID[:,0].astype(int),:][:,0]-1).astype(int),:]
        w = np.copy(wvector)[i,:]
        u = case1Points[i,3:6] - case1Points[i,0:3]
        tI = -np.dot(n,w)/np.dot(n,u)
        inCenter[i,:] = case1Points[i,0:3] + tI*u.T
    
    # inCenter = (allNodes[(faces[innerFaceID[:,0].astype(int),:][:,0]-1).astype(int),:]+allNodes[(faces[innerFaceID[:,0].astype(int),:][:,1]-1).astype(int),:]+allNodes[(faces[innerFaceID[:,0].astype(int),:][:,2]-1).astype(int),:])/3

    # Pyramidal Volume
    # Case 1, volume 1
    p1 = allNodes[(faces[innerFaceID[:,0].astype(int),:][:,0]-1).astype(int),:]
    p2 = allNodes[(faces[innerFaceID[:,0].astype(int),:][:,1]-1).astype(int),:]
    p3 = allNodes[(faces[innerFaceID[:,0].astype(int),:][:,2]-1).astype(int),:]
    p4 = case1Points[:,0:3]
    volCalc1 = np.expand_dims(np.transpose(p1-p4).T, axis=1)
    volCalc2 = np.expand_dims(np.transpose(np.cross((p2-p4),\
        (p3-p4))).T, axis=2)
    c1vol1 = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6)

    # Case 1, volume 2
    p5 = case1Points[:,3:6]
    volCalc1 = np.expand_dims(np.transpose(p1-p5).T, axis=1)
    volCalc2 = np.expand_dims(np.transpose(np.cross((p2-p5),\
        (p3-p5))).T, axis=2)
    c1vol2 = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6)

    # Case 2, total volume
    p1 = allNodes[(faces[outerFaceID.astype(int),:][:,0]-1).astype(int),:]
    p2 = allNodes[(faces[outerFaceID.astype(int),:][:,1]-1).astype(int),:]
    p3 = allNodes[(faces[outerFaceID.astype(int),:][:,2]-1).astype(int),:]
    p4 = case2Points[:,3:6]
    volCalc1 = np.expand_dims(np.transpose(p1-p4).T, axis=1)
    volCalc2 = np.expand_dims(np.transpose(np.cross((p2-p4),\
        (p3-p4))).T, axis=2)
    c2vol = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6)        

    # Case 3, total volume
    c3vol = htcLength*0.5*np.linalg.norm(np.cross(c2v1,c2v2),axis=1)

    # Edge Data Matrix
    # [x1 y1 z1 x2 y2 z2 A n1 n2 n3 L1 L2 V1 V2 c]
    edgeData = np.zeros([len(innerFace)+2*len(outerFace),15])

    edgeData[:,0:6]              = np.concatenate((case1Points,case2Points,case3Points))
    edgeData[:,6]                = 0.5*np.linalg.norm(np.cross(v1,v2),axis=1) # Area
    edgeData[:,7:10]             = (np.cross(v1,v2))/np.array([np.linalg.norm(np.cross(v1,v2),axis=1),]*3).T # case 1,2 normals
    edgeData[-case3Points.shape[0]:,7:10] = (edgeData[-case3Points.shape[0]:,0:3]-edgeData[-case3Points.shape[0]:,3:6])/np.array([np.linalg.norm(edgeData[-case3Points.shape[0]:,0:3]-edgeData[-case3Points.shape[0]:,3:6],axis=1),]*3).T # case 3 normals
    
    # Check normal is in right direction and fix if needed
    for x in range(len(edgeData)):
        edgeData[x,7:10] = edgeData[x,7:10]*((np.dot((edgeData[x,3:6]-edgeData[x,0:3]),edgeData[x,7:10]) > 0).astype(int)*2-1)
    
    edgeData[:,10]               = np.concatenate((np.linalg.norm(inCenter-case1Points[:,0:3],axis=1),np.linalg.norm(case2Points[:,0:3]-case2Points[:,3:6],axis=1),np.linalg.norm(case3Points[:,0:3]-case3Points[:,3:6],axis=1)))
    
    edgeData[0:len(inCenter),11] = np.linalg.norm(inCenter-case1Points[:,3:6],axis=1) # L2
    
    edgeData[:,12]               = np.concatenate((c1vol1,c2vol,c3vol)) # V1
    
    edgeData[0:len(inCenter),13] = c1vol2 # V2
    edgeData[:,14]               = np.concatenate((np.ones(len(case1Points)),2*np.ones(len(case2Points)),3*np.ones(len(case3Points))))

    return edgeData