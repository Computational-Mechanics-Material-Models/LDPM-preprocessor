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
## This functions reads the output node and tet file from Tetgen and 
## constructs NumPy arrays with all of the nodes and tetrahedra.
##
## ===========================================================================

import numpy as np


def read_LDPMCSL_tetgen(nodeFile, tetFile, edgeFile):                                       

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    nodeFile:        file path of the node file to read
    tetFile:         file path of the tetrahedron file to read
    --------------------------------------------------------------------------
    ### Outputs ###
    allNodes:        numpy array with node coordinates for all tetrahedra
    allTets:         numpy array with the vertex indices of each tetrahedron
    --------------------------------------------------------------------------
    """

    allNodes = np.loadtxt(nodeFile, usecols=(1,2,3),skiprows=1)                                   
    allTets = np.loadtxt(tetFile, usecols=(1,2,3,4),skiprows=1)  
    allEdges = np.loadtxt(edgeFile, usecols=(1,2),skiprows=1) 

    return allNodes, allTets, allEdges