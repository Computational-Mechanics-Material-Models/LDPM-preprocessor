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
## Function to generate VTK file for visualization in Paraview of facets for a
## single polyhedral cell in LDPM and CSL.
##
## ===========================================================================

import numpy as np
from pathlib import Path


def mkVtk_LDPM_singleCell(allNodes,allTets,parDiameterList,tetFacets,geoName,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - allNodes:     List of all nodes
    - allTets:      List of all tetrahedra
    - parDiameterList:  List of particle diameters
    - tetFacets:    List of facets for each tetrahedron
    - geoName:      Name of the geometry
    - tempPath:     Path to the temporary directory
    --------------------------------------------------------------------------
    ### Outputs ###
    - A VTK file that can be visualized in Paraview
    --------------------------------------------------------------------------
    """


    # Use the tet in the middle of the list so that it is not on the boundary
    for i in range(4):
        index = allTets[round(len(allTets)/2),i]

        # Find locations in tet list which contain the given vertex
        location = np.argwhere(allTets==index)   
        
        # Initialize empty facet list for vertex
        cellFacetNodes=np.zeros(([len(location)*6,9]))

        # Store facets for given cell. Using facet indexing from genTessellationLDPM.py (same as Cusatis 2011a)
        for x in range(0,len(location)):
            if location[x,1] == 0:
                facets = [0,1,2,3,4,5]
            elif location[x,1] == 1:
                facets = [0,1,6,7,8,9]
            elif location[x,1] == 2:
                facets = [2,3,6,7,10,11]
            elif location[x,1] == 3:
                facets = [4,5,8,9,10,11]
            
            # Stores facets. One line per facet (9 values for 3 nodes) 
            cellFacetNodes[x*6:x*6+6,:]     = tetFacets[location[x,0],facets[0]*9:facets[0]*9+9]
            cellFacetNodes[x*6+1:x*6+6+1,:] = tetFacets[location[x,0],facets[1]*9:facets[1]*9+9]
            cellFacetNodes[x*6+2:x*6+6+2,:] = tetFacets[location[x,0],facets[2]*9:facets[2]*9+9]
            cellFacetNodes[x*6+3:x*6+6+3,:] = tetFacets[location[x,0],facets[3]*9:facets[3]*9+9]
            cellFacetNodes[x*6+4:x*6+6+4,:] = tetFacets[location[x,0],facets[4]*9:facets[4]*9+9]
            cellFacetNodes[x*6+5:x*6+6+5,:] = tetFacets[location[x,0],facets[5]*9:facets[5]*9+9]
        
        # Make triangle connectivity for facets
        cellFacets = np.arange(len(cellFacetNodes)*3).reshape(-1,3).astype(int)

        with open(Path(tempPath + geoName + \
            '-para-singleCellFacets' + str(int(i)) + '.000.vtk'),"w") as f:                                                                          
            f.write('# vtk DataFile Version 2.0\n')
            f.write('Facet Visual File\n') 
            f.write('ASCII\n')    
            f.write('DATASET POLYDATA\n')        

            f.write('POINTS ' + str(int(len(cellFacetNodes)*3)) + ' float \n') 
            f.write("\n".join(" ".join(map(str, x)) for x in cellFacetNodes))
            f.write('\n\n')  

            f.write('POLYGONS ' + str(len(cellFacets)) + ' ' \
                + str(round(len(cellFacets)*4)) +'\n3 ')
            f.write("\n3 ".join(" ".join(map(str, x)) for x in cellFacets))

            f.write('\n\n')   
