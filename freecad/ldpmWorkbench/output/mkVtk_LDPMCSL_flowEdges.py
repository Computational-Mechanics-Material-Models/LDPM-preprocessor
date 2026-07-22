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
## Function to generate a VTK file for visualization in Paraview of all
## flow edges in the mesh.
##
## ===========================================================================

import numpy as np
from pathlib import Path


def mkVtk_LDPMCSL_flowEdges(geoName,edgeData,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - edgeData:     Array of all flow edges in the model
    - geoName:      Name of the geometry
    - tempPath:     Path to the temporary directory
    --------------------------------------------------------------------------
    ### Outputs ###
    - A VTK file for visualizing all flow edge elements
    --------------------------------------------------------------------------
    """

    edgeVTKdata = np.copy(edgeData) # since np.unique operation will change the original variable edgeData, use np.copy here instead
    # Store Nodal Data
    nodes = np.unique(edgeVTKdata[:,0:6].reshape(-1,3),axis=0)
    
    # Store Element Data
    for x in range(len(edgeVTKdata)):

        edgeVTKdata[x,0] = (np.where(~(nodes[:,0:3]-edgeVTKdata[x,0:3]).any(axis=1))[0])
        edgeVTKdata[x,1] = (np.where(~(nodes[:,0:3]-edgeVTKdata[x,3:6]).any(axis=1))[0])     

    edgeVTKdata = np.delete(edgeVTKdata,[2,3,4,5],1)
    
    cell_types = edgeVTKdata[:,-1].astype(int)

    cells = edgeVTKdata[:,0:2].astype(int)

    with open(Path(tempPath + geoName + \
        '-para-flowEdges.000.vtk'),"w") as f:                                                                          
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured Grid\n')            
        f.write('ASCII\n')    
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(nodes)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in nodes))
        f.write('\n\n')  
        f.write('CELLS ' + str(len(edgeVTKdata)) + ' ' \
            + str(len(edgeVTKdata)*3) +'\n2 ')
        f.write("\n2 ".join(" ".join(map(str, x)) for x in cells))
        f.write('\n\n')  
        f.write('CELL_TYPES ' + str(len(edgeVTKdata)) +'\n')
        for x in cell_types:
            f.write("%s\n" % 3)