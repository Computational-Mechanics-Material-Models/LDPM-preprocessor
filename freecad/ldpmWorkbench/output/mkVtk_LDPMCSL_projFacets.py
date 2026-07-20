## ===========================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2024 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be
## found in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ===========================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## 
## ===========================================================================
##
## Description coming soon...
##
## ===========================================================================


import numpy as np
from pathlib import Path


def mkVtk_LDPMCSL_projFacets(geoName,projectedFacet,tempPath):

    facetsPoints = projectedFacet.reshape(-1,3)
    cells = (np.arange(0,round(len(facetsPoints))).\
        reshape(-1,3)).astype(int)
    cell_types = np.array([5,]*round(len(facetsPoints)/3))

    with open(Path(tempPath + geoName + \
        '-para-projectedFacet.000.vtk'),"w") as f:                                                                          
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured Grid\n')            
        f.write('ASCII\n')    
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(facetsPoints)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in facetsPoints))
        f.write('\n\n')  
        f.write('CELLS ' + str(round(len(facetsPoints)/3)) + ' ' \
            + str(round(len(facetsPoints)/3*4)) +'\n3 ')
        f.write("\n3 ".join(" ".join(map(str, x)) for x in cells))
        f.write('\n\n')  
        f.write('CELL_TYPES ' + str(round(len(facetsPoints)/3)) +'\n')
        for x in cell_types:
            f.write("%s\n" % x)    