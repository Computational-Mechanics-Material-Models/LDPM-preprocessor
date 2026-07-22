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
## This file contains the function to check if the voxel system is larger 
## than the geometry.
##
## ===========================================================================

import numpy as np

def check_multiMat_size(multiMatX,multiMatY,multiMatZ,multiMatRes,minC,maxC):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - multiMatX:        Number of voxels in the x direction
    - multiMatY:        Number of voxels in the y direction
    - multiMatZ:        Number of voxels in the z direction
    - multiMatRes:      Resolution of the voxels
    - minC:             Minimum coordinates of the geometry
    - maxC:             Maximum coordinates of the geometry
    --------------------------------------------------------------------------
    ### Outputs ###
    - Boolean:          True if the voxel system is larger than the geometry,
                        False if not
    --------------------------------------------------------------------------
    """  

    # Calculate the size of the voxel system and the geometry
    multiMatSize = np.array((multiMatX,multiMatY,multiMatZ))*multiMatRes
    geoSize = maxC-minC

    # Check if the voxel system is larger than the geometry
    if ((multiMatSize-geoSize)>=0).all():
        return True
    else:
        error_msg = 'Error: The voxel system is smaller than the geometry. Please use a larger voxel file or smaller geometry.'
        print(error_msg)
        raise ValueError(error_msg)