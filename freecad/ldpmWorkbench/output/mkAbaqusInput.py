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
## ===========================================================================

# pyright: reportMissingImports=false
from pathlib import Path
import FreeCAD as App
from femtools import membertools
import numpy as np

def mkAbaqusInput(elementType, analysisName, materialProps, materialPropsDesc, materialPropsVals, simProps, simPropsValues, \
    nodesFilename, elemFilename, facetsFilename, geoName, outDir, outName):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - elementType:      The type of element that will be used
    - analysisName:     The name of the analysis
    - materialProps:    The names of the material properties
    - materialPropsVals:The values of the material properties
    - simProps:         The names of the simulation properties
    - simPropsValues:   The values of the simulation properties
    - nodesFilename:    The name of the file containing the nodes
    - elemFilename:     The name of the file containing the tets
    - facetsFilename:   The name of the file containing the facets
    - geoName:          The name of the geometry
    - outDir:           The output directory
    - outName:          The output name
    --------------------------------------------------------------------------
    ### Outputs ###
    - An input file for Abaqus
    --------------------------------------------------------------------------
    """


    doc = App.ActiveDocument

    if elementType == 'LDPM':
        analysis = doc.getObject("LDPManalysis")

    # Read in the nodes from the nodes file and store in a numpy array
    # Assume that the file has the following format:
    #// ================================================================================
    #// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor
    #//
    #// Copyright (c) 2023 
    #// All rights reserved. 
    #//
    #// Use of the code that generated this file is governed by a BSD-style license that
    #// can be found in the LICENSE file at the top level of the distribution and at
    #// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
    #//
    #// ================================================================================
    #// Node Data File
    #// ================================================================================
    #//
    #// Data Structure:
    #// X Y Z 
    #//
    #// ================================================================================
    #0 25 44.98529816
    #0 22.22222137 50
    #0 27.77777863 50
    #0 50 22.22222137
    #0 45.12414169 25.00591087
    with open(Path(outDir + outName + '/' + nodesFilename)) as f:
        allNodes = np.loadtxt(f, skiprows=18)

    # Read in the tets from the tets file and store in a numpy array
    # Assume that the file has the following format:
    #// ================================================================================
    #// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor
    #//
    #// Copyright (c) 2023 
    #// All rights reserved. 
    #//
    #// Use of the code that generated this file is governed by a BSD-style license that
    #// can be found in the LICENSE file at the top level of the distribution and at
    #// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
    #//
    #// ================================================================================
    #// Tetrahedra Data File
    #// ================================================================================
    #//
    #// Data Structure:
    #// Node 1 Node 2 Node 3 Node 4
    #// Note: Node numbers are zero-indexed
    #//
    #// ================================================================================
    #66 90 92 785
    #707 585 1080 992    
    with open(Path(outDir + outName + '/' + elemFilename)) as f:
        allTets = np.loadtxt(f, skiprows=19)

    # Increase all tet indices by 1 to account for the fact that Abaqus is 1-indexed
    allTets = allTets + 1




    with open(Path(outDir + outName + '/' + geoName + '-mesh.inp'),"w") as f:

        f.write('*Heading\n')
        f.write('** Job name: ' + geoName + ' Model name: Model-' + geoName + '\n')
        f.write('** Generated by: Abaqus/CAE 2019\n')
        f.write('**\n')
        f.write('** PARTS\n')
        f.write('**\n')
        f.write('*Part, name=' + geoName + '\n')
        f.write('*Node\n')
        for x in range(0,len(allNodes)):
                f.write(str(x+1) + ', ' + str(allNodes[x,0]) + ', ' \
                    + str(allNodes[x,1]) + ', '  + str(allNodes[x,2]) \
                    + '\n')
        f.write('*Element, type=C3D4\n')
        for x in range(0,len(allTets)):
                f.write(str(x+1) + ', ' + str(allTets[x,0].astype(int)) \
                    + ', ' \
                    + str(allTets[x,1].astype(int)) + ', '  \
                    + str(allTets[x,2].astype(int)) \
                    + ', '  + str(allTets[x,3].astype(int)) +'\n')
        f.write('*End Part\n')
        f.write('**\n')
        f.write('**\n')
        f.write('** ASSEMBLY\n')
        f.write('**\n')
        f.write('*Assembly, name=Assembly\n')
        f.write('**\n')
        f.write('*Instance, name=' + geoName + '-1, part=' + geoName + '\n')
        f.write('*End Instance\n')
        f.write('**\n')
        f.write('*End Assembly\n')
