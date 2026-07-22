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


def _refine_pair(sortedData, i, id_a, id_b, sim_a, act_a, sim_b, act_b):
    if abs(sim_a - act_a) > abs(sim_b - act_b):
        if sim_a - act_a > 0:
            sortedData[i, 2] = id_b
        else:
            sortedData[i, 2] = id_a
    else:
        if sim_b - act_b > 0:
            sortedData[i, 2] = id_a
        else:
            sortedData[i, 2] = id_b
    return sortedData


def gen_multiMat_refine(sortedData, itzVolFracSim,
    binderVolFracSim, aggVolFracSim, itzVolFracAct, binderVolFracAct, aggVolFracAct, i,
    phaseMode=3):

    phase = _multi_phase(phaseMode)
    mat_a = sortedData[i, 3]
    mat_b = sortedData[i, 4]

    # Same material case
    if mat_a == mat_b:
        return sortedData

    pair = {mat_a, mat_b}
    # 2-phase Aggregate-Binder Case (2-3); no ITZ
    if phase == 2:
        if pair == {2, 3}:
            return _refine_pair(
                sortedData, i, 2, 3,
                binderVolFracSim, binderVolFracAct,
                aggVolFracSim, aggVolFracAct,
            )
        return sortedData

    # Aggregate-ITZ Case (1-3)
    if pair == {1, 3}:
        return _refine_pair(
            sortedData, i, 1, 3,
            itzVolFracSim, itzVolFracAct,
            aggVolFracSim, aggVolFracAct,
        )
    # Aggregate-Binder Case (2-3)
    if pair == {2, 3}:
        return _refine_pair(
            sortedData, i, 2, 3,
            binderVolFracSim, binderVolFracAct,
            aggVolFracSim, aggVolFracAct,
        )
    # ITZ-Binder Case (1-2)
    if pair == {1, 2}:
        return _refine_pair(
            sortedData, i, 1, 2,
            itzVolFracSim, itzVolFracAct,
            binderVolFracSim, binderVolFracAct,
        )
    return sortedData
