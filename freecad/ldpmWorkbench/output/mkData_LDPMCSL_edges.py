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
## Function to generate and write a data file of all edges in a CSL
## model, for later use in Project Chrono.
##
## ===========================================================================

from pathlib import Path
import numpy as np

def mkData_LDPMCSL_edges(geoName,tempPath,allEdges):
    
    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - geoName:      Name of the geometry file
    - tempPath:     Path to the temporary directory
    - allEdges:     Array of all edges in the model
    --------------------------------------------------------------------------
    ### Outputs ###
    - A data file of all edges in the model
    --------------------------------------------------------------------------
    """

    allEdges = allEdges-1

    np.savetxt(Path(tempPath + geoName + \
        '-data-edges.dat'), allEdges.astype(int), fmt='%i', delimiter=' ', comments=''\
        ,header='\
// ================================================================================\n\
// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor\n\
//\n\
// Copyright (c) 2023 \n\
// All rights reserved. \n\
//\n\
// Use of the code that generated this file is governed by a BSD-style license that\n\
// can be found in the LICENSE file at the top level of the distribution and at\n\
// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE\n\
//\n\
// ================================================================================\n\
// Edge Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// Node 1 Node 2\n\
// Note: Node numbers are zero-indexed\n\
//\n\
// ================================================================================')


