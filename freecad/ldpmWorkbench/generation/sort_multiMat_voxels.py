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
## Description coming soon...
##
## ===========================================================================

import numpy as np


def _multi_phase(phaseMode):
    if isinstance(phaseMode, str):
        text = phaseMode.strip().lower().replace(" ", "")
        if text.startswith("2"):
            return 2
        if text.startswith("3"):
            return 3
        raise ValueError(f"Unknown multimaterial phase: {phaseMode!r}")
    phase = int(phaseMode)
    if phase not in (2, 3):
        raise ValueError(f"Unknown multimaterial phase: {phaseMode!r}")
    return phase


def sort_multiMat_voxels(multiMatVoxels, phaseMode=3):

    phase = _multi_phase(phaseMode)
    multiMatVoxels = np.asarray(multiMatVoxels)
    voxelNumbering = np.arange(len(multiMatVoxels)) + 1

    aggFull = (multiMatVoxels > 3) * voxelNumbering
    aggVoxels = aggFull[aggFull != 0]

    binderFull = (multiMatVoxels == 0) * voxelNumbering
    binderVoxels = binderFull[binderFull != 0]

    if phase == 2:
        itzVoxels = np.array([], dtype=voxelNumbering.dtype)
    else:
        itzFull = (multiMatVoxels == 2) * voxelNumbering
        itzVoxels = itzFull[itzFull != 0]

    if len(aggVoxels) > 0:
        aggVoxelIDs = multiMatVoxels[aggVoxels - 1]
    else:
        aggVoxelIDs = np.array([], dtype=multiMatVoxels.dtype)

    return aggVoxels, itzVoxels, binderVoxels, aggVoxelIDs
