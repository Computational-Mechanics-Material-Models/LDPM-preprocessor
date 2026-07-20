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


def gen_multiMat_reform(allTets,facetData,sortedData):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - allTets:         list of all tets
    - facetData:       datastructure with all facet data
    - sortedData:      datastructure with all sorted data
    --------------------------------------------------------------------------
    ### Outputs ###
    - facetData:       datastructure with all facet data
    - facetMaterial:   list of all facet materials
    --------------------------------------------------------------------------
    """  

    reSortedData = sortedData[sortedData[:,0].argsort()]

    facetMaterial = reSortedData[:,2]

    for x in range(0,len(allTets)):

        for y in range(0,12):

            facetData[36*x+3*y+2,9] = facetMaterial[12*x+y]
            
    return facetData,facetMaterial