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


def mkData_LDPMCSL_facetfiberInt(geoName,FiberdataList,TotalIntersections,MaxInterPerFacet,tempPath):

    # Generate file for fiber-facet interaction data

        np.savetxt(Path(tempPath + geoName + \
            '-data-fiberfacet.dat'), FiberdataList, fmt='%.10g', delimiter=' '\
            ,header='\
FacetFiber Data Generated with LDPM Mesh Generation Tool\n\
Format: Intersection number followed by one line per Interaction\n\
Intersection [N]\n\
[Te Fa fN fM fL S L df I]')

        f = open(Path(tempPath + geoName + \
            '-data-fiberfacet.dat'), "r")
        contents = f.readlines()
        f.close()

        contents.insert(4, '\n')
        contents.insert(5, 'Number of Total Intersection: ' + str(int(TotalIntersections)) + '\n')
        contents.insert(6, 'Number of Maximum Intersection: ' + str(int(MaxInterPerFacet)) + '\n')
        for x in range(0,int(TotalIntersections)):
            contents.insert(2*x+7, 'Intersection: ' + str(x+1) + '\n')

        f = open(Path(tempPath + geoName + \
            '-data-fiberfacet.dat'), "w")
        contents = "".join(contents)
        f.write(contents)
        f.close()

