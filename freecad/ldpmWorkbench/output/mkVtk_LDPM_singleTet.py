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
## Function to generate a VTK file for visualization in Paraview of a single
## tetrahedron for LDPM models.
##
## ===========================================================================

from pathlib import Path


def mkVtk_LDPM_singleTet(allNodes,allTets,geoName,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - allNodes:     List of all nodes
    - allTets:      List of all tetrahedra
    - geoName:      Name of the geometry
    - tempPath:     Path to the temporary directory
    --------------------------------------------------------------------------
    ### Outputs ###
    - A VTK file for visualizing particles
    --------------------------------------------------------------------------
    """
    
    # Use the tet in the middle of the list so that it is not on the boundary
    tet = allTets[round(len(allTets)/2),:]-1

    # Extract the nodes for the first tetrahedron
    allNodes = [allNodes[int(tet[0])],\
              allNodes[int(tet[1])],\
              allNodes[int(tet[2])],\
              allNodes[int(tet[3])]]

    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-para-singleTet.000.vtk'),"w") as f:                                       
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured grid\n')            
        f.write('ASCII\n')    
        f.write('\n')  
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(allNodes)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in allNodes))
        f.write('\n\n')  
        f.write('CELLS 1 5\n')
        f.write("4 0 1 2 3\n")
        f.write('\n')  
        f.write('CELL_TYPES 1\n')
        f.write('10\n')  