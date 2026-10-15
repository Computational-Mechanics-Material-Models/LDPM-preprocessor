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

_CHUNK = 200000


def _write_lines(handle, lines):
    batch = []
    for line in lines:
        batch.append(line)
        if len(batch) >= _CHUNK:
            handle.write("\n".join(batch))
            handle.write("\n")
            batch.clear()
    if batch:
        handle.write("\n".join(batch))
        handle.write("\n")


def mkVtk_LDPMCSL_facets(geoName, tempPath, tetFacets, facetMaterial, facetData=None):

    FacetPoints = tetFacets.reshape(-1, 3)
    n_facets = len(FacetPoints) // 3

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
        _write_lines(f, (" ".join(map(str, point)) for point in FacetPoints))
        f.write("\n")

        f.write(
            "POLYGONS "
            + str(n_facets)
            + " "
            + str(n_facets * 4)
            + "\n"
        )
        _write_lines(
            f,
            (
                "3 %d %d %d" % (3 * index, 3 * index + 1, 3 * index + 2)
                for index in range(n_facets)
            ),
        )

        f.write("\nCELL_DATA " + str(n_facets) + "\n")
        f.write("FIELD FieldData " + str(n_fields) + "\n")
        f.write("Material 1 " + str(n_facets) + " float\n")
        _write_lines(f, map(str, facetMaterial))

        if e_rf is not None:
            f.write("E_rf 1 " + str(n_facets) + " float\n")
            _write_lines(f, map(str, e_rf))
            f.write("str_rf 1 " + str(n_facets) + " float\n")
            _write_lines(f, map(str, str_rf))
            f.write("frc_rf 1 " + str(n_facets) + " float\n")
            _write_lines(f, map(str, frc_rf))

        f.write("\n\n")
