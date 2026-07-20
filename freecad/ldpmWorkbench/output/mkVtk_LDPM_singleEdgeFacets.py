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
## Function to generate VTK file for visualization in Paraview of facets
## and LDPM and CSL models.
##
## ===========================================================================

import numpy as np
from pathlib import Path


def mkVtk_LDPM_singleEdgeFacets(geoName,tempPath,allEdges,facetData,tetFacets):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - geoName:          Name of the geometry file
    - tempPath:         Path to the temporary directory
    - tetFacets:        Facet data from the tetrahedral mesh
    --------------------------------------------------------------------------
    ### Outputs ###
    - A VTK file that can be visualized in Paraview
    --------------------------------------------------------------------------
    """


    # Find the lines in facetData that correspond to the edge (have the first column equal to the edge)
    edgeFacets = np.where(facetData[:,0] == 0)[0]

    # Get facet vertices (columns 3-5 of the facetData) for the edge facets
    edgeFacetVertices = facetData[edgeFacets,2:5]

    # Get the coordinates for these vertices
    tetFacets = tetFacets.reshape(-1,3)
    singleEdgeFacetPoint = tetFacets[edgeFacetVertices.astype(int),:]   #facetPointData[edgeFacetVertices.astype(int),:]

    singleEdgeFacetPoints = []

    # Store each value from singleEdgeFacetPoint to a new numpy array
    for i in range(len(singleEdgeFacetPoint)):
        for j in range(len(singleEdgeFacetPoint[i])):
            for k in range(len(singleEdgeFacetPoint[i][j])):
                singleEdgeFacetPoints.append(singleEdgeFacetPoint[i][j][k])

    # Reshape singleEdgeFacetPoints to be 3 elements wide
    singleEdgeFacetPoints = np.array(singleEdgeFacetPoints).reshape(-1,3)
    

    # Make cells for the edge facets
    singleEdgeFacetCells = np.arange(0,len(edgeFacets)*3).reshape(-1,3)


    with open(Path(tempPath + geoName + \
        '-para-singleEdgeFacets.000.vtk'),"w") as f:                                                                          
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Facet Visual File\n') 
        f.write('ASCII\n')    
        f.write('DATASET POLYDATA\n')        

        f.write('POINTS ' + str(len(singleEdgeFacetPoints)) + ' float \n') 
        f.write("\n".join(" ".join(map(str, x)) for x in singleEdgeFacetPoints))
        f.write('\n\n')  

        f.write('POLYGONS ' + str(len(singleEdgeFacetCells)) + ' ' \
            + str(round(len(singleEdgeFacetCells)*4)) +'\n3 ')
        f.write("\n3 ".join(" ".join(map(str, x)) for x in singleEdgeFacetCells))

        f.write('\n\n')  
