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
## and their corresponding material and diameter for LDPM and CSL models.
##
## ===========================================================================

from pathlib import Path

def mkVtk_particles(internalNodes,parDiameterList,materialList,geoName,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - internalNodes:List of particle centers
    - parDiameterList:  List of particle diameters
    - materialList: List of particle materials
    - geoName:      Name of the geometry
    - tempPath:     Path to the temporary directory
    --------------------------------------------------------------------------
    ### Outputs ###
    - A VTK file for visualizing particles
    --------------------------------------------------------------------------
    """

    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-para-particles.000.vtk'),"w") as f:                                       
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured grid legacy vtk file with point scalar data\n')            
        f.write('ASCII\n')    
        f.write('\n')  
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(internalNodes)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in internalNodes))
        f.write('\n\n')  
        f.write('POINT_DATA ' + str(len(internalNodes)) + '\n')
        f.write('SCALARS Diameter double\n')
        f.write('LOOKUP_TABLE default\n')
        for x in parDiameterList:
            f.write("%s\n" % x)
        f.write('\n')  
        f.write('SCALARS Material double\n')
        f.write('LOOKUP_TABLE default\n')
        for x in materialList:
            f.write("%s\n" % x)
