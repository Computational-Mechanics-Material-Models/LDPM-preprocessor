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
## Function to write a data file of all facet vertices.
##
## ===========================================================================

import numpy as np
from pathlib import Path


def mkData_LDPMCSL_facetsVertices(geoName,tempPath,tetFacets):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - geoName:          Name of the geometry file
    - tempPath:         Path to the temporary directory
    - facetPointData:   List of facet vertex points
    --------------------------------------------------------------------------
    ### Outputs ###
    - A data file of facet vertices
    --------------------------------------------------------------------------
    """

    facetPoints = tetFacets.reshape(-1,3)

    # Remove any duplicate points and keep the original order
    #_, idx = np.unique(facetPoints, return_index=True, axis=0)
    #facetPoints = facetPoints[np.sort(idx)]


    # Write the data file
    np.savetxt(Path(tempPath + geoName + \
        '-data-facetsVertices.dat'), facetPoints, fmt='%.10g', delimiter=' ', comments=''\
        ,header='\
// ================================================================================\n\
// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor\n\
//\n\
// Copyright (c) 2023 \n\
// All rights reserved. \n\
//\n\
// Use of the code that generated this file is governed by a BSD-style license that\n\
// can be found in the LICENSE file at the top level of the distribution and at\n\
// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE\n\
//\n\
// ================================================================================\n\
// Facet Vertex Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// X Y Z\n\
//\n\
// ================================================================================')
    

