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
## This function, calculates the maximum edge length of a triangular mesh 
## defined by its vertices and faces.
##
## ===========================================================================

import numpy as np

def calc_LDPMCSL_surfMeshSize(vertices, faces):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    vertices:            (x,y,z) coordinates of each vertex
    faces:               (v1,v2,v3) vertex indices for each triangle node
    --------------------------------------------------------------------------
    ### Outputs ###
    maxEdgeLength:     Scalar of the longest edge length in the mesh
    --------------------------------------------------------------------------
    """

    # Calculate the edge lengths for all faces
    edgeLength1 = np.linalg.norm(vertices[faces[:,1].astype(int) - 1, 0:3] - vertices[faces[:,0].astype(int) - 1, 0:3], axis=1)
    edgeLength2 = np.linalg.norm(vertices[faces[:,2].astype(int) - 1, 0:3] - vertices[faces[:,1].astype(int) - 1, 0:3], axis=1)
    edgeLength3 = np.linalg.norm(vertices[faces[:,2].astype(int) - 1, 0:3] - vertices[faces[:,0].astype(int) - 1, 0:3], axis=1)

    # Combine the edge lengths and find the maximum
    allEdgeLengths = np.concatenate((edgeLength1, edgeLength2, edgeLength3))
    maxEdgeLength = np.amax(allEdgeLengths)

    return maxEdgeLength
