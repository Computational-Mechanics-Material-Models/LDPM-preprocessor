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


def mkIges_LDPMCSL_flowEdges(geoName,edgeData,tempPath):

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
    pass


    # THIS SECTION IS IN PROGRESS TO MAKE A VALID IGES FILE THAT CAN THEN BE IMPORTED BY FREECAD FOR VIEWING
    """
    with open(Path(tempPath + geoName + \
        '-fC-flowEdges.000.iges'),"w") as f:                                                                          
        f.write('                                                                        S0000001\n')
        f.write(',,31HOpen CASCADE IGES processor 7.6,13HFilename.iges,                  G0000001\n')
        f.write('16HOpen CASCADE 7.6,31HOpen CASCADE IGES processor 7.6,32,308,15,308,15,G0000002\n')
        f.write(',1.,2,2HMM,1,0.01,15H20230711.102426,1E-07,2000.1,,,11,0,               G0000003\n')
        f.write('15H20230711.102426,;                                                    G0000004\n')
        f.write('     402       1       0       0       0       0       0       000000000D0000001\n')
        f.write('     402       0       0       1       1                               0D0000002\n')
        for x in range(len(edgeData)):
            f.write('     110       ' + str(x+2) + '       0       0       0       0       0       000020000D000000' + str(2*x+3) + '\n')
            f.write('     110       0       0       1       0                               0D000000' + str(2*x+4) + '\n')      
        f.write('402,' + str(len(edgeData)) + ',3,5,7,9,11,13;                                             0000001P0000001\n')
        for x in range(len(edgeData)):
            f.write('110,' + str(edgeData[x,0]) + ',' + str(edgeData[x,1]) + ',' + str(edgeData[x,2]) + ',' + str(edgeData[x,3]) + ',' + str(edgeData[x,4]) + ',' + str(edgeData[x,5]) + ';                     000000' + str(2*x+3) + 'P000000' + str(x+2) + '\n')
        f.write('S      1G      4D     10P      5                                        T0000001\n')

    """
    