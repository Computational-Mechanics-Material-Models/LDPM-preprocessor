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
## Function to generate a VTK file for visualization in Paraview of particles
## and their corresponding diameter for LDPM and CSL models.
##
## ===========================================================================

from pathlib import Path


def mkVtk_LDPM_singleEdgeParticles(allNodes,allEdges,allDiameters,geoName,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - allNodes:     List of all nodes
    - allDiameters: List of all particle diameters (including fictitious)
    - allEdges:      List of all edges
    - geoName:      Name of the geometry
    - tempPath:     Path to the temporary directory
    --------------------------------------------------------------------------
    ### Outputs ###
    - A VTK file for visualizing particles
    --------------------------------------------------------------------------
    """
    
    # Use the edge in the middle of the list so that it is not on the boundary
    edge = allEdges[0,:]-1

    # Extract the nodes for that edge
    allNodes = [allNodes[int(edge[0])],\
                allNodes[int(edge[1])]]

    # Extract the particle diameters for that edge
    allDiameters = [allDiameters[int(edge[0])],\
                    allDiameters[int(edge[1])]]

    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-para-singleEdgeParticles.000.vtk'),"w") as f:                                       
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured grid legacy vtk file with point scalar data\n')            
        f.write('ASCII\n')    
        f.write('\n')  
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(allNodes)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in allNodes))
        f.write('\n\n')  
        f.write('POINT_DATA ' + str(len(allNodes)) + '\n')
        f.write('SCALARS Diameter double\n')
        f.write('LOOKUP_TABLE default\n')
        for x in allDiameters:
            f.write("%s\n" % x)
        f.write('\n')  
