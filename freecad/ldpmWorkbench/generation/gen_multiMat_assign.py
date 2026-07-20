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


def gen_multiMat_assign(
    allNodes,
    materialList,
    aggVoxels,
    itzVoxels,
    binderVoxels,
    internalNodes,
    multiMatX,
    multiMatY,
    multiMatZ,
    multiMatRes,
    minC,
    phaseMode=3,
):

    phase = _multi_phase(phaseMode)

    def get_voxel_centers(voxels):
        voxels = np.asarray(voxels)
        if voxels.size == 0:
            return np.empty((0, 3))
        xVoxels = np.floor(voxels / (multiMatZ * multiMatY))
        yVoxels = np.floor((voxels - xVoxels * multiMatZ * multiMatY) / multiMatZ)
        zVoxels = voxels - xVoxels * multiMatZ * multiMatY - yVoxels * multiMatZ

        voxel_coords = np.stack([xVoxels, yVoxels, zVoxels], axis=-1) * multiMatRes + minC
        voxel_centers = voxel_coords + (multiMatRes / 2) - multiMatRes / 2
        return voxel_centers

    if phase == 2:
        phase_pairs = [
            (aggVoxels, 3),
            (binderVoxels, 2),
        ]
    else:
        phase_pairs = [
            (aggVoxels, 3),
            (itzVoxels, 1),
            (binderVoxels, 2),
        ]

    centers_list = []
    materials_list = []
    for voxels, mat_id in phase_pairs:
        centers = get_voxel_centers(voxels)
        if centers.shape[0] == 0:
            continue
        centers_list.append(centers)
        materials_list.append(np.full(centers.shape[0], mat_id, dtype=int))

    if not centers_list:
        raise ValueError("No voxels available for the selected multimaterial phase.")

    voxel_centers = np.concatenate(centers_list, axis=0)
    materials = np.concatenate(materials_list)

    n_surface = len(allNodes) - len(internalNodes)
    for i in range(n_surface):
        node = allNodes[i]
        distances = np.linalg.norm(voxel_centers - node, axis=1)
        closest_index = np.argmin(distances)
        materialList[i] = materials[closest_index]

    return materialList
