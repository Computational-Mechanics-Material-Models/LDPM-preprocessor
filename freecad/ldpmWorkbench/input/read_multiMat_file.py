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
## This functions reads in the material file and constructs a NumPy array with
## the material flags for each voxel.
##
## ===========================================================================

import numpy as np

def read_multiMat_file(materialFile):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    materialFile:        File path of the material file to read
    --------------------------------------------------------------------------
    ### Outputs ###
    multiMatX:           Number of voxels in the x direction
    multiMatY:           Number of voxels in the y direction
    multiMatZ:           Number of voxels in the z direction
    multiMatRes:         Size of each voxel
    multiMatVoxels:      List of voxels with their material flags
    --------------------------------------------------------------------------
    """

    # Read the material file
    with open(materialFile) as f:
        version = str(f.readlines(1))
        multiMatX = str(f.readlines(2))
        multiMatY = str(f.readlines(3))
        multiMatZ = str(f.readlines(4))
        multiMatRes = str(f.readlines(5))

    multiMatX = float(multiMatX.split(":")[1].strip().replace("\\n']", ""))
    multiMatY = float(multiMatY.split(":")[1].strip().replace("\\n']", ""))
    multiMatZ = float(multiMatZ.split(":")[1].strip().replace("\\n']", ""))
    multiMatRes = float(multiMatRes.split(":")[1].strip().replace("\\n']", ""))

    # Store the voxels in a numpy array
    multiMatVoxels = np.loadtxt(materialFile, skiprows=5)

    return multiMatX, multiMatY, multiMatZ, multiMatRes, multiMatVoxels