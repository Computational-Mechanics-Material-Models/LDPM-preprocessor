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
## Function to generate and write a data file of all facets in an LDPM
## model, for later use in Project Chrono.
##
## ===========================================================================

from pathlib import Path
import numpy as np


def mkData_LDPMCSL_facets(geoName,tempPath,facetData):
    
    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - geoName:              Name of the geometry file
    - tempPath:             Path to the temporary directory
    - facetData:            Array of all facets in the model
    --------------------------------------------------------------------------
    ### Outputs ###
    - A data file of all facets in the model
    --------------------------------------------------------------------------
    """

    if np.size(facetData,axis=1) == 19:
        headerText = '\
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
// Facet Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// Tet IDx IDy IDz Vol pArea cx cy cz px py pz qx qy qz sx sy sz mF\n\
// One line per facet, ordering is Tet 1 (Facet 1-12),...,Tet N (Facet 1-12)\n\
// Note: All indices are zero-indexed\n\
//\n\
// ================================================================================'
    elif np.size(facetData,axis=1) == 22:
        headerText = '\
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
// Facet Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// Tet IDx IDy IDz Vol pArea cx cy cz px py pz qx qy qz sx sy sz mF E_rf str_rf frc_rf\n\
// One line per facet, ordering is Tet 1 (Facet 1-12),...,Tet N (Facet 1-12)\n\
// Note: All indices are zero-indexed\n\
//\n\
// ================================================================================'
    elif np.size(facetData,axis=1) == 24:
        headerText = '\
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
// Facet Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// Edge Tet IDx IDy IDz Vol pArea cx cy cz Cx Cy Cz pAreaT px py pz qx qy qz sx sy sz mF\n\
// One line per facet, ordering is by edge number\n\
// Note: All indices are zero-indexed\n\
//\n\
// ================================================================================'
    elif np.size(facetData,axis=1) == 27:
        headerText = '\
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
// Facet Data File\n\
// ================================================================================\n\
//\n\
// Data Structure:\n\
// Edge Tet IDx IDy IDz Vol pArea cx cy cz Cx Cy Cz pAreaT px py pz qx qy qz sx sy sz mF E_rf str_rf frc_rf\n\
// One line per facet, ordering is by edge number\n\
// Note: All indices are zero-indexed\n\
//\n\
// ================================================================================'
    else:
        raise ValueError(
            f"Unsupported facetData width {np.size(facetData, axis=1)}; "
            "expected 19, 22, 24, or 27."
        )


    np.savetxt(Path(tempPath + geoName + \
        '-data-facets.dat'), facetData, fmt='%.10g', comments = '', delimiter=' '\
        ,header=headerText)