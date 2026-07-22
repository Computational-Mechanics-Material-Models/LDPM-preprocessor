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
## Description coming soon...
##
## ================================================================================

import numpy as np


def sort_multiMat_mat(facetMaterial,facetVol1,facetVol2,particleMaterial,subtetVol):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - facetMaterial:   list of all facet materials
    - facetVol1:       volume of facet 1
    - facetVol2:       volume of facet 2
    - particleMaterial:material of all particles
    - subtetVol:       volume of subtet
    --------------------------------------------------------------------------
    ### Outputs ###
    - sortedData:      datastructure with all sorted data
    --------------------------------------------------------------------------
    """  

    # [#, Volume Difference, Selected Material, Material 1, Material 2, subtetVol]
    condensedData = np.vstack((np.arange(len(facetMaterial)),abs(facetVol1-facetVol2),facetMaterial,particleMaterial[:,0],particleMaterial[:,1],subtetVol)).transpose()

    sortedData = condensedData[condensedData[:,1].argsort()]

    return sortedData