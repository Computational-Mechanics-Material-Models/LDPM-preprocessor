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
##
## ================================================================================

import numpy as np


def _normalize_phase_mode(phaseMode):
    if isinstance(phaseMode, str):
        text = phaseMode.strip().lower().replace(" ", "")
        if text.startswith("2"):
            return 2
        if text.startswith("3"):
            return 3
        raise ValueError(f"Unknown phaseMode string: {phaseMode!r}")
    mode = int(phaseMode)
    if mode not in (2, 3):
        raise ValueError(f"phaseMode must be 2 or 3; got {phaseMode!r}")
    return mode


def _safe_frac(part, total):
    if total == 0:
        return 0.0
    return float(part) / float(total)


def check_multiMat_matVol(
    subtetVol,
    facetMaterial,
    aggVoxels,
    itzVoxels,
    binderVoxels,
    phaseMode=3,
):

    mode = _normalize_phase_mode(phaseMode)
    subtetVol = np.asarray(subtetVol)
    facetMaterial = np.asarray(facetMaterial)

    if mode == 2:
        aggVol = float(np.sum(subtetVol * (facetMaterial == 1)))
        binderVol = float(np.sum(subtetVol * (facetMaterial == 2)))
        itzVol = 0.0
        total_sim = sum((itzVol, binderVol, aggVol)) or 1.0
        agg_n = len(aggVoxels) if aggVoxels is not None else 0
        binder_n = len(binderVoxels) if binderVoxels is not None else 0
        total_act = (agg_n + binder_n) or 1
        itzVolFracSim = 0.0
        binderVolFracSim = _safe_frac(binderVol, total_sim)
        aggVolFracSim = _safe_frac(aggVol, total_sim)
        itzVolFracAct = 0.0
        binderVolFracAct = _safe_frac(binder_n, total_act)
        aggVolFracAct = _safe_frac(agg_n, total_act)
        return (
            itzVolFracSim,
            binderVolFracSim,
            aggVolFracSim,
            itzVolFracAct,
            binderVolFracAct,
            aggVolFracAct,
        )

    aggVol = float(np.sum(subtetVol * (facetMaterial == 1)))
    itzVol = float(np.sum(subtetVol * (facetMaterial == 2)))
    binderVol = float(np.sum(subtetVol * (facetMaterial == 3)))
    total_sim = sum((itzVol, binderVol, aggVol)) or 1.0

    agg_n = len(aggVoxels) if aggVoxels is not None else 0
    itz_n = len(itzVoxels) if itzVoxels is not None else 0
    binder_n = len(binderVoxels) if binderVoxels is not None else 0
    total_act = (agg_n + itz_n + binder_n) or 1

    itzVolFracSim = _safe_frac(itzVol, total_sim)
    binderVolFracSim = _safe_frac(binderVol, total_sim)
    aggVolFracSim = _safe_frac(aggVol, total_sim)
    itzVolFracAct = _safe_frac(itz_n, total_act)
    binderVolFracAct = _safe_frac(binder_n, total_act)
    aggVolFracAct = _safe_frac(agg_n, total_act)

    return (
        itzVolFracSim,
        binderVolFracSim,
        aggVolFracSim,
        itzVolFracAct,
        binderVolFracAct,
        aggVolFracAct,
    )
