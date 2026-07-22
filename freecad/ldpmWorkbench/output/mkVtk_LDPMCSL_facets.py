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
## and their corresponding material for LDPM models.
##
## ===========================================================================

import numpy as np
from pathlib import Path


def mkVtk_LDPMCSL_facets(geoName, tempPath, tetFacets, facetMaterial, facetData=None):

    FacetPoints = tetFacets.reshape(-1, 3)
    FacetCells = np.arange(0, len(FacetPoints)).reshape(-1, 3)

    e_rf = None
    str_rf = None
    frc_rf = None
    if facetData is not None:
        facetData = np.asarray(facetData)
        ncols = facetData.shape[1] if facetData.ndim == 2 else 0
        if ncols == 22:
            e_rf = facetData[:, 19]
            str_rf = facetData[:, 20]
            frc_rf = facetData[:, 21]
        elif ncols == 27:
            e_rf = facetData[:, 24]
            str_rf = facetData[:, 25]
            frc_rf = facetData[:, 26]

    n_fields = 1
    if e_rf is not None:
        n_fields = 4

    with open(Path(tempPath + geoName + "-para-facets.000.vtk"), "w") as f:
        f.write("# vtk DataFile Version 2.0\n")
        f.write("Facet Visual File\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")

        f.write("POINTS " + str(len(FacetPoints)) + " float \n")
        f.write("\n".join(" ".join(map(str, x)) for x in FacetPoints))
        f.write("\n\n")

        f.write(
            "POLYGONS "
            + str(len(FacetCells))
            + " "
            + str(round(len(FacetCells) * 4))
            + "\n3 "
        )
        f.write("\n3 ".join(" ".join(map(str, x)) for x in FacetCells))

        f.write("\n\nCELL_DATA " + str(len(FacetCells)) + "\n")
        f.write("FIELD FieldData " + str(n_fields) + "\n")
        f.write("Material 1 " + str(len(FacetCells)) + " float\n")
        f.write("\n".join(map(str, facetMaterial)))
        f.write("\n")

        if e_rf is not None:
            f.write("E_rf 1 " + str(len(FacetCells)) + " float\n")
            f.write("\n".join(map(str, e_rf)))
            f.write("\n")
            f.write("str_rf 1 " + str(len(FacetCells)) + " float\n")
            f.write("\n".join(map(str, str_rf)))
            f.write("\n")
            f.write("frc_rf 1 " + str(len(FacetCells)) + " float\n")
            f.write("\n".join(map(str, frc_rf)))
            f.write("\n")

        f.write("\n\n")
