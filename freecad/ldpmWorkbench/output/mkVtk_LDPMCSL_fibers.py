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


def mkVtk_LDPMCSL_fibers(p1Fiber,p2Fiber,dFiber,lFiber,orienFibers,geoName,tempPath):

    fiberCenter = (p2Fiber-p1Fiber)/2+p1Fiber
    vectorValues = np.array(([dFiber,dFiber]))
    fiberVector = np.concatenate((lFiber,np.array([vectorValues,]*len(fiberCenter))),axis=1)

    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-para-fibers000.vtk'),"w") as f:                                       
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Unstructured grid legacy vtk file with point vector data\n')            
        f.write('ASCII\n')    
        f.write('\n')  
        f.write('DATASET UNSTRUCTURED_GRID\n')        
        f.write('POINTS ' + str(len(fiberCenter)) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in fiberCenter))
        f.write('\n\n')  
        f.write('POINT_DATA ' + str(len(fiberCenter)) + '\n')
        f.write('VECTORS Size float\n')
        f.write("\n".join(" ".join(map(str, x)) for x in fiberVector))
        f.write('\n\n')  
        f.write('VECTORS Orientation float\n')
        f.write("\n".join(" ".join(map(str, x)) for x in orienFibers))
    
    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-para-fibers-poly000.vtk'),"w") as f:                                       
        f.write('# vtk DataFile Version 2.0\n')
        f.write('POLYDATA legacy vtk file with point vector data\n')            
        f.write('ASCII\n')    
        f.write('\n')  
        f.write('DATASET POLYDATA\n')        
        f.write('POINTS ' + str(len(fiberCenter)*2) + ' double \n')  
        f.write("\n".join(" ".join(map(str, x)) for x in p1Fiber))
        f.write('\n')
        f.write("\n".join(" ".join(map(str, x)) for x in p2Fiber))
        f.write('\n\n')  
        f.write('LINES ' + str(len(fiberCenter)) +" "+ str(len(fiberCenter)*3) + '\n') 
        for i in range(len(fiberCenter)):
            f.write(f"2 {i} {i + len(fiberCenter)}\n")        
        f.write('\n')
