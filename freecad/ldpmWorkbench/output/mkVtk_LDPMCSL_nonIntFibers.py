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
## Primary Authors: Matthew Troemner
## ===========================================================================
##
## Description coming soon...
##
## ===========================================================================


import numpy as np
from pathlib import Path


def mkVtk_LDPMCSL_nonIntFibers(p1Fiber,p2Fiber,dFiber,lFiber,orienFibers,geoName,IntersectedFiber,tempPath):

    Nonp1Fiber = []
    NonorienFibers = []
    fiberVector = []

    for i in range(0,len(p1Fiber)):

        if i not in IntersectedFiber:
            lenght = lFiber[i,0]
            Vector = np.array([lenght,dFiber,dFiber])
            fiberVector.append(Vector)
            Nonp1Fiber.append(p1Fiber[i])
            NonorienFibers.append(orienFibers[i])

    Nonp1Fiber=np.array(Nonp1Fiber).reshape(-1,3)
    NonorienFibers=np.array(NonorienFibers).reshape(-1,3)
    fiberVector=np.array(fiberVector).reshape(-1,3)

    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-para-nonintersectedfibers.000.vtk'),"w") as f:                                       
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured grid legacy vtk file with point vector data\n')            
        f.write('ASCII\n')    
        f.write('\n')  
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(Nonp1Fiber)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in Nonp1Fiber))
        f.write('\n\n')  
        f.write('POINT_DATA ' + str(len(Nonp1Fiber)) + '\n')
        f.write('VECTORS Size float\n')
        f.write("\n".join(" ".join(map(str, x)) for x in fiberVector))
        f.write('\n\n')  
        f.write('VECTORS Orientation float\n')
        f.write("\n".join(" ".join(map(str, x)) for x in NonorienFibers))    