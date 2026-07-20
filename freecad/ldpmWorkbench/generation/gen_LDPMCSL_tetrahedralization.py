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




def gen_LDPMCSL_tetrahedralization(internalNodes,surfaceNodes,surfaceFaces,geoName,tempPath):
    
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

    # Prepare file of internal nodes and external nodes/faces for Tetgen
    nodeRange = np.arange(len(internalNodes))+1
    nodeList = np.vstack((nodeRange,internalNodes.T)).T
    surfaceFaces = surfaceFaces+1

    # Make external faces file for Tetgen
    with open(Path(tempPath + geoName + '2D.mesh'),"w") as f:                                       
        f.write('MeshVersionFormatted 2\n')   
        f.write('Dimension\n')   
        f.write('3\n')   
        f.write('Vertices\n')   
        f.write(str(len(surfaceNodes)) + '\n')                                   
        for x in range(0,len(surfaceNodes)):
                f.write(str(surfaceNodes[x,0]) + '    ' \
                    + str(surfaceNodes[x,1]) + '    '  + str(surfaceNodes[x,2]) \
                    + '    0\n')
        f.write('Triangles\n')
        f.write(str(len(surfaceFaces)) + '\n')  
        for x in range(0,len(surfaceFaces)):
                f.write(str(surfaceFaces[x,0]) + '    ' \
                    + str(surfaceFaces[x,1]) + '    '  + str(surfaceFaces[x,2]) \
                    + '    0\n')
        f.write('End\n')

    
    # Make internal nodes file for Tetgen
    with open(Path(tempPath + geoName + '2D.a.node'),"w") as f:                                       
        f.write(str(len(internalNodes)) + ' 3 0 0\n ')                                   
        f.write("\n ".join(" ".join(map(str, x)) for x in nodeList))


    # Run Tetgen with appropriate switches
    # The used switches are:
    # -p:    Tetrahedralize a piecewise linear complex
    # -Y:    Preserves the input surface mesh
    # -i:    Inserts a list of additional points
    # -O0/1: Specifies the level of mesh optimization - only flips with default optimization
    # -S0:   Specifies the maximum number of Steiner points
    # -k:    Refines mesh to produce a better quality mesh
    # -Q:    Quiet mode
    # -e:    Outputs also internal mesh edges

    tetgenCommand = str(Path(TETGENPATH + '/tetgen')) + ' -pYiO0/1S0kQe ' \
        + str(Path(tempPath + geoName + '2D.mesh'))
    os.system(tetgenCommand)

    # Check if Tetgen ran by trying to rename the output VTK
    try:
        os.replace(
            Path(tempPath + geoName + '2D.1.vtk'),
            Path(tempPath + geoName + '-para-mesh.vtk'),
        )
    except Exception:
        print("Tetgen failed during tetrahedralization.")
        print("If this issue persists, you may need to use another geometry or particle distribution.")
        raise

    try:
        os.remove(Path(tempPath + geoName + '2D.1.face'))
    except OSError:
        pass
    try:
        os.remove(Path(tempPath + geoName + '2D.a.node'))
    except OSError:
        pass

    os.replace(Path(tempPath + geoName + '2D.1.ele'), Path(tempPath + geoName + '.ele'))
    os.replace(Path(tempPath + geoName + '2D.1.node'), Path(tempPath + geoName + '.node'))
    os.replace(Path(tempPath + geoName + '2D.1.edge'), Path(tempPath + geoName + '.edge'))
