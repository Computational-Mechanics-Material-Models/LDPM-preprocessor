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
## Function to generate and write a data file of all facets in an LDPM
## model, for later use in Project Chrono.
##
## ===========================================================================

from pathlib import Path
import numpy as np


def mkData_LDPMCSL_faceFacets(geoName,tempPath,surfaceNodes,surfaceFaces):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    - surfaceNodes:         Array of all vertices in the mesh
    - surfaceFaces:         Array of all surface faces in the mesh
    --------------------------------------------------------------------------
    ### Outputs ###
    - A data file of all face facets in the model
    - A data file of all surface nodes in the model (used for surface construction in fluid-solid transition)
    - A data file of all surface faces in the model (used for surface construction in fluid-solid transition)
    --------------------------------------------------------------------------
    """
    
    faceFacets = np.empty((len(surfaceFaces)*6,10))

    for x in range(len(surfaceFaces)):

        # Face triangle
        #      0
        #     / \
        #    /   \
        #   1-----2

        # [n x1 y1 z1 x2 y2 z2 x3 y3 z3]
        # Node 0
        faceFacets[6*x,:] = np.concatenate(([surfaceFaces[x,0]],surfaceNodes[surfaceFaces[x,0]],(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2,((surfaceNodes[surfaceFaces[x,0]]+(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,1]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,2]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2)/2)/3))
        faceFacets[6*x+1,:] = np.concatenate(([surfaceFaces[x,0]],surfaceNodes[surfaceFaces[x,0]],(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2,((surfaceNodes[surfaceFaces[x,0]]+(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,1]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,2]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2)/2)/3))

        # Node 1
        faceFacets[6*x+2,:] = np.concatenate(([surfaceFaces[x,1]],surfaceNodes[surfaceFaces[x,1]],(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2,((surfaceNodes[surfaceFaces[x,0]]+(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,1]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,2]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2)/2)/3))
        faceFacets[6*x+3,:] = np.concatenate(([surfaceFaces[x,1]],surfaceNodes[surfaceFaces[x,1]],(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2,((surfaceNodes[surfaceFaces[x,0]]+(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,1]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,2]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2)/2)/3))

        # Node 2
        faceFacets[6*x+4,:] = np.concatenate(([surfaceFaces[x,2]],surfaceNodes[surfaceFaces[x,2]],(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2,((surfaceNodes[surfaceFaces[x,0]]+(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,1]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,2]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2)/2)/3))
        faceFacets[6*x+5,:] = np.concatenate(([surfaceFaces[x,2]],surfaceNodes[surfaceFaces[x,2]],(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2,((surfaceNodes[surfaceFaces[x,0]]+(surfaceNodes[surfaceFaces[x,1]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,1]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,2]])/2)/2+(surfaceNodes[surfaceFaces[x,2]]+(surfaceNodes[surfaceFaces[x,0]]+surfaceNodes[surfaceFaces[x,1]])/2)/2)/3))

    headerText = '\
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
// Face Facet Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// n x1 y1 z1 x2 y2 z2 x3 y3 z3\n\
// One line per face facet, first number is the tet node index\n\
// Note: All indices are zero-indexed\n\
//\n\
// ================================================================================'

    np.savetxt(Path(tempPath + geoName + \
        '-data-faceFacets.dat'), faceFacets, fmt='%.10g', comments = '', delimiter=' '\
        ,header=headerText)
    
    np.savetxt(Path(tempPath + geoName + \
        '-data-surfaceNodes.dat'), surfaceNodes, fmt='%.10g', comments = '', delimiter=' '\
        ,header=headerText)
        
    np.savetxt(Path(tempPath + geoName + \
        '-data-surfaceFaces.dat'), surfaceFaces, fmt='%.10g', comments = '', delimiter=' '\
        ,header=headerText)