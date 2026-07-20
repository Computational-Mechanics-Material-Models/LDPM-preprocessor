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
## Determine the maximum and minimum extents of a bounding box surrounding the 
## input mesh vertices.
##
## ===========================================================================

import numpy as np


def calc_LDPMCSL_surfMeshExtents(vertices):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    vertices:        (x,y,z) coordinates of each vertex.
    --------------------------------------------------------------------------
    ### Outputs ###
    minExtent:       Coordinate of minimum bounding box corner
    maxExtent:       Coordinate of maximum bounding box corner
    --------------------------------------------------------------------------
    """

    minExtent = np.amin(vertices, axis=0)
    maxExtent = np.amax(vertices, axis=0)

    return minExtent, maxExtent