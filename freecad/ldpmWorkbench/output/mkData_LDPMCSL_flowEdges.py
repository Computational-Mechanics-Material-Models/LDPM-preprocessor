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
## This function writes the flow edges as a data file.
##
## ===========================================================================

from pathlib import Path
import numpy as np

def mkData_LDPMCSL_flowEdges(geoName,edgeData,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - geoName:      Name of the geometry file
    - tempPath:     Path to the temporary directory
    - edgeData:     Array of all flow edges in the model
    --------------------------------------------------------------------------
    ### Outputs ###
    - A data file of all flow edges in the model
    --------------------------------------------------------------------------
    """


    edgeFiledata = np.copy(edgeData)
    # Store Nodal Data
    nodes = np.unique(edgeFiledata[:,0:6].reshape(-1,3),axis=0)
    
    # Store Element Data
    for x in range(len(edgeFiledata)):
        
        edgeFiledata[x,0] = (np.where(~(nodes[:,0:3]-edgeFiledata[x,0:3]).any(axis=1))[0])+1
        edgeFiledata[x,1] = (np.where(~(nodes[:,0:3]-edgeFiledata[x,3:6]).any(axis=1))[0])+1     
    
    edgeFiledata = np.delete(edgeFiledata,[2,3,4,5],1)

    np.savetxt(Path(tempPath + geoName + '-data-flowEdges.dat'), nodes, fmt='%.16g', delimiter=' '\
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
// Flow Edge Node and Element Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// X Y Z\n\
//\n\
// ================================================================================')    

    with open(Path(tempPath + geoName + '-data-edgeEle-geom.dat'),'ab') as f:
        np.savetxt(f, edgeFiledata[:,:], fmt='%.16g', delimiter=' ',header='\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// i1 i2 A n1 n2 n3 L1 L2 V1 V2 c\n\
//\n\
// ================================================================================')    