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
    
    centers = np.array([seg['center'] for seg in pathSegments])
    tangents = np.array([seg['tangent'] for seg in pathSegments])
    segment_ids = np.array([seg['id'] for seg in pathSegments])
    lengths = np.array([seg['length'] for seg in pathSegments])
    
    with open(Path(tempPath + geoName + '-orientationPath.vtk'), "w") as f:
        f.write('# vtk DataFile Version 2.0\n')
        f.write('Orientation path segments with tangent vectors\n')
        f.write('ASCII\n')
        f.write('\n')
        f.write('DATASET UNSTRUCTURED_GRID\n')
        f.write('POINTS ' + str(len(centers)) + ' double\n')
        f.write("\n".join(" ".join(map(str, x)) for x in centers))
        f.write('\n\n')
        f.write('POINT_DATA ' + str(len(centers)) + '\n')
        f.write('VECTORS tangent float\n')
        f.write("\n".join(" ".join(map(str, x)) for x in tangents))
        f.write('\n\n')
        f.write('SCALARS segment_id int\n')
        f.write('LOOKUP_TABLE default\n')
        f.write("\n".join(str(x) for x in segment_ids))
        f.write('\n\n')
        f.write('SCALARS segment_length float\n')
        f.write('LOOKUP_TABLE default\n')
        f.write("\n".join(str(x) for x in lengths))
        f.write('\n')
