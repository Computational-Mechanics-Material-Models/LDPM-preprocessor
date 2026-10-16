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
## 
## ===========================================================================
##
## Description coming soon...
##
## ===========================================================================



import numpy as np
from pathlib import Path


def mkVtk_orientationPath(pathSegments, geoName, tempPath):
    
    if pathSegments is None or len(pathSegments) == 0:
        return

    n = len(pathSegments)
    starts = np.array([seg["start"] for seg in pathSegments], dtype=float)
    ends = np.array([seg["end"] for seg in pathSegments], dtype=float)
    tangents = np.array([seg["tangent"] for seg in pathSegments], dtype=float)
    segment_ids = np.array([seg["id"] for seg in pathSegments])
    lengths = np.array([seg["length"] for seg in pathSegments], dtype=float)

    with open(Path(tempPath + geoName + "-orientationPath.vtk"), "w") as f:
        f.write("# vtk DataFile Version 2.0\n")
        f.write("Orientation path segments with tangent vectors\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")
        f.write("POINTS " + str(2 * n) + " double\n")
        for i in range(n):
            f.write(
                str(starts[i, 0])
                + " "
                + str(starts[i, 1])
                + " "
                + str(starts[i, 2])
                + "\n"
            )
            f.write(
                str(ends[i, 0])
                + " "
                + str(ends[i, 1])
                + " "
                + str(ends[i, 2])
                + "\n"
            )
        f.write("\nLINES " + str(n) + " " + str(3 * n) + "\n")
        for i in range(n):
            f.write("2 " + str(2 * i) + " " + str(2 * i + 1) + "\n")
        f.write("\nCELL_DATA " + str(n) + "\n")
        f.write("VECTORS tangent float\n")
        f.write("\n".join(" ".join(map(str, x)) for x in tangents))
        f.write("\n\n")
        f.write("SCALARS segment_id int\n")
        f.write("LOOKUP_TABLE default\n")
        f.write("\n".join(str(int(x)) for x in segment_ids))
        f.write("\n\n")
        f.write("SCALARS segment_length float\n")
        f.write("LOOKUP_TABLE default\n")
        f.write("\n".join(str(x) for x in lengths))
        f.write("\n")
