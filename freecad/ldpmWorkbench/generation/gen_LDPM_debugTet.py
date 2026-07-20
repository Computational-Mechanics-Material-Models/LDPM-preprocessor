## ================================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be found
## in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ================================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ================================================================================
##
## This file contains the function to generate the initial data for a single tet
##
## ================================================================================

import numpy as np





def gen_LDPM_debugTet(type):
  
    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - 
    --------------------------------------------------------------------------
    ### Outputs ###
    - 
    --------------------------------------------------------------------------
    """  

    # Define the geometry name
    if type == "Regular":
        geoName = 'LDPM_debugRegTet'
    else:
        geoName = 'LDPM_debugIrregTet'

    # Define the number of nodes
    numNodes = 4

    # Define the number of tets
    numTets = 1

    # Define the nodes for the regular (equilateral) tet
    if type == "Regular":
        allNodes = np.array([[0,0,0],
                             [1,0,0],
                             [0.5,np.sqrt(3)/2,0],
                             [0.5,np.sqrt(3)/6,np.sqrt(6)/3]])
    else:
        allNodes = np.array([[1,0,0],
                             [2.0,1.5,3],
                             [-1,0.5,0],
                             [0.5,2,1]])

    # Define the tets for the tet
    allTets = np.array([[1,2,3,4]])

    # Define the parDiameterList (all diameter values are the same and equal to 0.6)
    if type == "Regular":
        parDiameterList = np.array([0.6,0.6,0.6,0.6])
    else:
        parDiameterList = np.array([0.6,0.9,1.0,1.2])

    # Define the materialList (all material values are the same and equal to 1)
    materialList = np.ones(len(parDiameterList))

    # Define the minPar 
    minPar = 0.6
    

    return allNodes,allTets,parDiameterList,materialList,minPar,geoName
