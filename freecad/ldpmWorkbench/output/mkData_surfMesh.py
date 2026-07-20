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
## Description coming soon...
##
##
## ===========================================================================

import os
import numpy as np
from pathlib import Path

from freecad.ldpmWorkbench import TETGENPATH


def mkData_surfMesh(surfaceNodes,surfaceFaces,geoName,tempPath):
    
    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - internalNodes:    Internal nodes of the geometry
    - surfaceNodes:     External nodes of the geometry
    - surfaceFaces:     External faces of the geometry
    - geoName:          Name of the geometry
    - tempPath:         Path to the temporary folder
    --------------------------------------------------------------------------
    ### Outputs ###
    - None
    --------------------------------------------------------------------------
    """  


    # Make external faces file
    with open(Path(tempPath + geoName + \
        '-para-faces.000.vtk'),"w") as f:                                                                          
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Facet Visual File\n') 
        f.write('ASCII\n')    
        f.write('DATASET POLYDATA\n')        

        f.write('POINTS ' + str(len(surfaceNodes)) + ' float \n') 
        f.write("\n".join(" ".join(map(str, x)) for x in surfaceNodes))
        f.write('\n\n')  

        f.write('POLYGONS ' + str(len(surfaceFaces)) + ' ' \
            + str(round(len(surfaceFaces)*4)) +'\n3 ')
        f.write("\n3 ".join(" ".join(map(str, x)) for x in surfaceFaces))

