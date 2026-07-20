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
## Function to calculate the volume of a mesh composed of tetrahedrons
##
## ===========================================================================


import numpy as np



def calc_LDPMCSL_meshVolume(vertices, tets):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    vertices:          an array of vertex coordinates for the mesh
    tets:              an array of tetrahedron vertices for the mesh
    --------------------------------------------------------------------------
    ### Outputs ###
    sum(tetVolume):    volume of the mesh
    --------------------------------------------------------------------------
    """

    # Check if tets array is valid
    if len(tets) == 0:
        raise Exception("No tetrahedra found in mesh. The geometry may have failed to mesh properly. Check Gmsh errors above.")
    
    if tets.ndim != 2 or tets.shape[1] != 4:
        raise Exception(f"Invalid tetrahedra array shape: {tets.shape}. Expected 2D array with 4 columns. The mesh generation may have failed.")
    
    # Convert tets to integer array
    tets = tets.astype(int)
    
    # Get coordinates of vertices for each tetrahedron
    coord1 = vertices[tets[:, 0] - 1]
    coord2 = vertices[tets[:, 1] - 1]
    coord3 = vertices[tets[:, 2] - 1]
    coord4 = vertices[tets[:, 3] - 1]

    # Calculate the volume of all tetrahedrons in one go
    tetVolume = np.abs(np.sum(np.cross((coord2 - coord4),(coord3 - coord4))*(
        coord1 - coord4), axis=1)) / 6

    # Return the sum of all tetrahedron volumes
    return np.sum(tetVolume)

