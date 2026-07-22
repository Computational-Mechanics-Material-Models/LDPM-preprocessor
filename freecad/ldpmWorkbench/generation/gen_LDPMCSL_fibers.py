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
## 
## ===========================================================================
## 
## This file contains the function to generate a fiber and outputs the
## location of the fiber as well other fiber properties. 
##
## ===========================================================================


import numpy as np
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_orientationPath import get_zone_from_point

def gen_LDPMCSL_fibers(vertices,tets,coord1,coord2,coord3,coord4,maxIter,\
    lFiber,maxC,maxAggD,fiberOrientation,orientationStrength,triangles,\
    cutFiber,pathSegments=None):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - vertices:             List of vertices of the mesh
    - tets:                 List of tetrahedrons of the mesh
    - coord1:               Coordinate 1 of the tets
    - coord2:               Coordinate 2 of the tets
    - coord3:               Coordinate 3 of the tets
    - coord4:               Coordinate 4 of the tets
    - maxIter:              Maximum number of iterations to try to place a fiber
    - lFiber:               Length of the fiber
    - maxC:                 Maximum distance from the surface
    - maxAggD:              Maximum aggregate diameter
    - fiberOrientation:     Orientation of the fiber
    - orientationStrength:  Strength of the orientation
    - triangles:            List of triangles of the mesh
    - cutFiber:             Option to cut the fiber
    --------------------------------------------------------------------------
    ### Outputs ###
    - p1Fiber:              First node of the fiber
    - p2Fiber:              Second node of the fiber
    - orienFiber:           Orientation of the fiber
    - lFiber:               Length of the fiber
    --------------------------------------------------------------------------
    """



    # Generate random numbers to use in generation
    randomN1 = np.random.rand(maxIter*3)
    randomN2 = np.random.rand(maxIter*3)
    iterReq=0
    
    # Compute tet bounding boxes
    tets_min = np.min(vertices[tets - 1], axis=1)
    tets_max = np.max(vertices[tets - 1], axis=1)
    
    tets_min_global = np.min(vertices[tets - 1], axis=(0, 1))
    tets_max_global = np.max(vertices[tets - 1], axis=(0, 1))
    
    orienFiber_cached = None
    
    # Generate random nodal location
    while True:

        iterReq = iterReq + 3
        
        orienFiber_cached = None

        if iterReq >= len(randomN1):
            error_msg = "Fiber placement failed: exceeded the %r specified maximum iterations allowed." % (maxIter)
            print(error_msg)
            raise RuntimeError(error_msg)

        # Random point selection in random tet prism container
        # tetIndex = int(np.around(randomN1[iterReq] * len(tets))) - 1
        tetIndex = int(randomN1[iterReq] * len(tets))
        if tetIndex == len(tets):
            tetIndex -= 1
        
        tetVerts = vertices[tets[tetIndex]-1]
        
        # Random barycentric coordinates (x1 to x4)
        weight = np.sort(np.random.rand(3))
        x1 = weight[0]
        x2 = weight[1] - weight[0]
        x3 = weight[2] - weight[1]
        x4 = 1.0 - weight[2]

        # Generate a random point inside the tetrahedron
        p1Fiber = x1 * tetVerts[0] + x2 * tetVerts[1] + x3 * tetVerts[2] + x4 * tetVerts[3]

        if np.any(p1Fiber < tets_min_global) or np.any(p1Fiber > tets_max_global):
            print("p1fiber outside the box", p1Fiber)
            print("tetVerts", tetVerts)
            
        # tetMin = np.amin(tetVerts, axis=0)
        # tetMax = np.amax(tetVerts, axis=0)
        
        if pathSegments is not None and len(pathSegments) > 0:
            zone_id, segment_tangent = get_zone_from_point(p1Fiber, pathSegments)
            
            if zone_id is not None and segment_tangent is not None:
                strength = (6**(4-4*orientationStrength)-1)/200
                v = np.empty(2)
                j = 0
                while j < 2:
                    y = np.random.normal(0, strength, 1)
                    if y > -1 and y < 1:
                        v[j] = y
                        j = j+1
                
                orienFiber1 = segment_tangent.copy() / np.linalg.norm(segment_tangent)
                orienFiber2 = np.array((1,np.arctan2(orienFiber1[1],orienFiber1[0]),np.arccos(orienFiber1[2]/(orienFiber1[0]**2+orienFiber1[1]**2+orienFiber1[2]**2)**0.5)))
                orienFiber3 = np.array((1,orienFiber2[1]+np.pi*v[0],orienFiber2[2]+np.pi/2*v[1]))
                orienFiber = np.array((np.sin(orienFiber3[2])*np.cos(orienFiber3[1]),np.sin(orienFiber3[2])*np.sin(orienFiber3[1]),np.cos(orienFiber3[2])))
                
                if orientationStrength < 1.0:
                    randSign = np.random.rand(1)
                    if randSign<0.5:
                        sign = -1
                    else:
                        sign = 1
                    orienFiber = sign*orienFiber
                
                orienFiber_cached = orienFiber
            else:
                continue
        else:
            if np.allclose(fiberOrientation, 0.0):
                orienFiber1 = np.array((1,randomN2[iterReq+1]*2*np.pi,randomN2[iterReq+2]*np.pi))
                orienFiber2 = np.array((np.sin(orienFiber1[2])*np.cos(orienFiber1[1]),np.sin(orienFiber1[2])*np.sin(orienFiber1[1]),np.cos(orienFiber1[2])))
                orienFiber = np.array((orienFiber2[0],orienFiber2[1],orienFiber2[2]))/\
                    np.linalg.norm(np.array((orienFiber2[0],orienFiber2[1]\
                    ,orienFiber2[2])))
            else:
                strength = (6**(4-4*orientationStrength)-1)/200
                v = np.empty(2)
                j = 0
                while j < 2:
                    y = np.random.normal(0, strength, 1)
                    if y > -1 and y < 1:
                        v[j] = y
                        j = j+1
                
                orienFiber1 = np.array((fiberOrientation[0],fiberOrientation[1],fiberOrientation[2]))/\
                    np.linalg.norm(np.array((fiberOrientation[0],fiberOrientation[1],fiberOrientation[2])))
                orienFiber2 = np.array((1,np.arctan2(orienFiber1[1],orienFiber1[0]),np.arccos(orienFiber1[2]/(orienFiber1[0]**2+orienFiber1[1]**2+orienFiber1[2]**2)**0.5)))
                orienFiber3 = np.array((1,orienFiber2[1]+np.pi*v[0],orienFiber2[2]+np.pi/2*v[1]))
                orienFiber = np.array((np.sin(orienFiber3[2])*np.cos(orienFiber3[1]),np.sin(orienFiber3[2])*np.sin(orienFiber3[1]),np.cos(orienFiber3[2])))
                
                randSign = np.random.rand(1)
                if randSign<0.5:
                    sign = -1
                else:
                    sign = 1
                orienFiber = sign*orienFiber
        
        if orienFiber_cached is not None:
            orienFiber = orienFiber_cached
        
        p2Fiber = p1Fiber+orienFiber*lFiber
        
        # p1Fiber = pCFiber - 0.5 * lFiber * orienFiber
        # p2Fiber = pCFiber + 0.5 * lFiber * orienFiber

        # Obtain extents for floating bin
        # binMin = np.amin(np.vstack((p1Fiber,p2Fiber)), axis=0)-maxAggD-lFiber
        # binMax = np.amax(np.vstack((p1Fiber,p2Fiber)), axis=0)+maxAggD+lFiber

        # Check if fiber is inside the mesh    
        inside = False     
        # inside = insideCheckFiber(vertices,tets,p1Fiber,p2Fiber,\
        #     binMin,binMax,coord1,coord2,coord3,coord4,maxC)
        inside = point_in_any_tet(p2Fiber, vertices, tets, tets_min, tets_max)

        # Indicate placed fiber and break While Loop
        if inside == True:
            if np.any(p2Fiber < tets_min_global) or np.any(p2Fiber > tets_max_global):
                print("p2fiber outside the box ", p2Fiber)
            return p1Fiber, p2Fiber, orienFiber, lFiber
        
        # Find point fiber intersects external surface and trim accordingly
        else:

            # Find point fiber intersects external surface and trim accordingly
            if cutFiber in ['on','On','Y','y','Yes','yes']:                  

                # Get all surface triangle coordinates
                triangles = triangles.astype(int)
            
                coords0 = vertices[triangles[:,0]-1]
                coords1 = vertices[triangles[:,1]-1]
                coords2 = vertices[triangles[:,2]-1] 

                averageTriangles = (coords0+coords1+coords2)/3
                # averageFiber = (p1Fiber+p2Fiber)/2

                # Find distance to nearest surface triangle
                distances = np.linalg.norm(averageTriangles-p2Fiber,axis=1)
                # nearest = np.where(distances == np.amin(distances))
                nearest = np.argmin(distances)

                # Store the plane of this triangle
                p0 = coords0[nearest]
                p1 = coords1[nearest]
                p2 = coords2[nearest]
                # p0 = coords0[nearest,:]
                # p1 = coords1[nearest,:]
                # p2 = coords2[nearest,:]

                p01 = p1-p0
                p02 = p2-p0

                fiberVector = p2Fiber-p1Fiber

                # Compute distance to cutting plane
                t = np.dot(np.cross(p01, p02), (p1Fiber - p0)) / np.dot(-fiberVector, np.cross(p01, p02))
                # t = (np.dot(np.squeeze(np.cross(p01,p02)),np.squeeze((p1Fiber-p0))))/(np.dot(np.squeeze(-fiberVector),np.squeeze(np.cross(p01,p02))))

                # New point 2 for fiber after cutting
                p2Fiber = p1Fiber+fiberVector*t
                
               
                # Verfiy cut fiber is inside the mesh      
                inside = False   
                inside = point_in_any_tet(p2Fiber, vertices, tets, tets_min, tets_max)

                if np.logical_and(inside == True,np.linalg.norm(p1Fiber-p2Fiber)<lFiber):

                    fiberLength = np.linalg.norm(p1Fiber-p2Fiber)
                    
                    return p1Fiber, p2Fiber, orienFiber, fiberLength


            # If not trimming then discard fiber and try again
            else:

                pass


def point_in_tet(p, A, B, C, D):
    v0, v1, v2 = B - A, C - A, D - A
    vp = p - A
    mat = np.column_stack((v0, v1, v2))
    try:
        bary = np.linalg.solve(mat, vp)
    except np.linalg.LinAlgError:
        return False
    u, v, w = bary
    return (u >= 0) and (v >= 0) and (w >= 0) and (u + v + w <= 1)

def point_in_any_tet(p, vertices, tets, tets_min, tets_max):
    mask = np.all((tets_min <= p) & (tets_max >= p), axis=1)
    idx = np.where(mask)[0]
    for i in idx:
        A = vertices[tets[i][0] - 1]
        B = vertices[tets[i][1] - 1]
        C = vertices[tets[i][2] - 1]
        D = vertices[tets[i][3] - 1]
        if point_in_tet(p, A, B, C, D):
            return True
    return False
