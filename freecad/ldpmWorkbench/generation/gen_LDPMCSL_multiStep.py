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
import math
import time
import functools
import os
from pathlib import Path


import sys
import platform

import multiprocessing
from multiprocessing import Pool
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

if platform.system() != 'Windows':
    try:
        multiprocessing.set_start_method('fork', force=True)
    except:
        pass
    USE_PROCESSES = True
else:
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except:
        pass
    USE_PROCESSES = True

from freecad.ldpmWorkbench.input.read_multiMat_file                                  import read_multiMat_file
from freecad.ldpmWorkbench.generation.check_multiMat_size                            import check_multiMat_size
from freecad.ldpmWorkbench.generation.sort_multiMat_voxels                           import sort_multiMat_voxels
from freecad.ldpmWorkbench.generation.calc_sieveCurve                                import calc_sieveCurve
from freecad.ldpmWorkbench.generation.calc_parVolume                                 import calc_parVolume
from freecad.ldpmWorkbench.generation.gen_particleList                               import gen_particleList
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_subParticle                        import gen_LDPMCSL_subParticle
from freecad.ldpmWorkbench.generation.gen_particleMPI                                import gen_particleMPI
from freecad.ldpmWorkbench.generation.check_particleOverlapMPI                       import check_particleOverlapMPI
from freecad.ldpmWorkbench.generation.gen_particle                                   import gen_particle
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_fibers                             import gen_LDPMCSL_fibers


def configure_multiprocessing_for_freecad():
    exe = Path(sys.executable)
    name = exe.name.lower()

    if platform.system() == "Windows" and not name.startswith("python"):
        candidate = exe.parent / "pythonw.exe"
        if not candidate.is_file():
            candidate = exe.parent / "python.exe"
        if candidate.is_file():
            exe = candidate

    if exe.is_file():
        try:
            multiprocessing.set_executable(str(exe))
        except Exception:
            pass

    roots = []
    try:
        pkg_root = Path(__file__).resolve().parents[3]
        if (pkg_root / "freecad").is_dir():
            roots.append(str(pkg_root))
    except Exception:
        pass

    for p in sys.path:
        if not p:
            continue
        try:
            if (Path(p) / "freecad").is_dir() and p not in roots:
                roots.append(p)
        except Exception:
            pass

    if roots:
        existing = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
        merged = []
        for p in roots + existing:
            if p and p not in merged:
                merged.append(p)
        os.environ["PYTHONPATH"] = os.pathsep.join(merged)

    return str(exe)


def _verbose_on(value):
    return str(value).strip().lower() in ["on", "y", "yes", "true", "1"]


def _log(message):
    text = str(message)
    if not text.endswith("\n"):
        text += "\n"
    try:
        import FreeCAD as App
        App.Console.PrintMessage(text)
        if platform.system() == 'Windows':
            try:
                from PySide2 import QtWidgets
                QtWidgets.QApplication.processEvents()
            except ImportError:
                try:
                    from PySide import QtWidgets
                    QtWidgets.QApplication.processEvents()
                except ImportError:
                    pass
    except Exception:
        sys.stdout.write(text)
        sys.stdout.flush()


def _emit_progress(message, verbose_on):
    _log(message)



def _phase_list_val(lst, index, default=0.0):
    if lst is None or index >= len(lst):
        return float(default)
    try:
        return float(lst[index])
    except (TypeError, ValueError):
        return float(default)


def gen_multiMat_phase_particle_list(
    phaseVol, grainMin, grainMax, grainFuller, grainSieveD, grainSieveP,
    simMin, simMax, fillerC_phase, fillerDensity_phase, fillerOnlyPhases,
    wcRatio, cementC, airFrac, flyashC, silicaC, scmC,
    flyashDensity, silicaDensity, scmDensity, cementDensity, densityWater,
    verbose="On",
):
    if grainSieveD != (0 or None or [] or ""):
        [newGrainSieveCurveD, newGrainSieveCurveP, grainNewSet, grainW_min, grainW_max] = calc_sieveCurve(
            grainMin, grainMax, grainSieveD, grainSieveP
        )
    else:
        newGrainSieveCurveD, newGrainSieveCurveP, grainNewSet, grainW_min, grainW_max = 0, 0, 0, 0, 0

    if fillerOnlyPhases:
        [volGrainFracPar, volGrains, cdf, cdf1, kappa_i] = calc_parVolume(
            phaseVol, 0.0, 0.0, 0.0, grainFuller,
            0.0, 0.0, 0.0, fillerC_phase,
            0.0, 0.0, 0.0, fillerDensity_phase, 0.0, 0.0,
            grainMin, grainMax, newGrainSieveCurveD, newGrainSieveCurveP,
            grainNewSet, grainW_min, grainW_max,
        )
    else:
        [volGrainFracPar, volGrains, cdf, cdf1, kappa_i] = calc_parVolume(
            phaseVol, wcRatio, cementC, airFrac, grainFuller,
            flyashC, silicaC, scmC, fillerC_phase,
            flyashDensity, silicaDensity, scmDensity, fillerDensity_phase, cementDensity, densityWater,
            grainMin, grainMax, newGrainSieveCurveD, newGrainSieveCurveP,
            grainNewSet, grainW_min, grainW_max,
        )

    if simMin >= simMax:
        raise ValueError(
            "Phase min particle ({}) must be less than max ({}).".format(simMin, simMax)
        )
    if grainMin >= grainMax or grainMax <= 0:
        raise ValueError(
            "Phase grain min ({}) must be less than max ({}).".format(grainMin, grainMax)
        )

    return gen_particleList(
        volGrains, simMin, simMax, grainMin, grainMax,
        newGrainSieveCurveD, cdf, kappa_i, grainNewSet, grainFuller, verbose,
    )


def gen_LDPMCSL_multiStep(tempPath, numCPU, numIncrements, maxIter, parOffset, maxEdgeLength, max_dist, minPar_sim, maxPar_sim,minPar_exp, maxPar_exp, sieveCurveDiameter, sieveCurvePassing, wcRatio, cementC, airFrac, fullerCoef, flyashC, silicaC, scmC, fillerC, flyashDensity, silicaDensity, scmDensity, fillerDensity, cementDensity, densityWater, multiMatToggle, aggFile, multiMatFile, grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP, grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP, grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP, tetVolume, minC, maxC, verbose, fiberToggle, fiberFile, fiberDiameter, fiberLength, fiberVol, fiberOrientation1, fiberOrientation2, fiberOrientation3, fiberPref, fiberCutting, fiberIntersections, fiberOutputFiles, surfaceFaces, phaseMode=3, phaseMinPar=None, phaseMaxPar=None, phaseOffsetCoefList=None, phaseFillerContent=None, phaseFillerDensity=None, fillerOnlyPhases=False):

    verbose_on = _verbose_on(verbose)

    if phaseMinPar is None:
        phaseMinPar = []
    if phaseMaxPar is None:
        phaseMaxPar = []
    if phaseOffsetCoefList is None:
        phaseOffsetCoefList = []
    if phaseFillerContent is None:
        phaseFillerContent = []
    if phaseFillerDensity is None:
        phaseFillerDensity = []

    if not verbose_on:
        _emit_progress("External: loading mesh data...", verbose_on)

    # Load back in these seven matrices from their temporary files:
    # coord1, coord2, coord3, coord4, meshVertices, meshTets, surfaceNodes

    use_phase_sim = len(phaseMinPar) > 0 and len(phaseMaxPar) > 0
    if multiMatToggle == "On" and use_phase_sim:
        n_check = 2 if phaseMode == 2 else 3
        for i in range(n_check):
            smin = _phase_list_val(phaseMinPar, i)
            smax = _phase_list_val(phaseMaxPar, i)
            if smin >= smax:
                raise ValueError(
                    "Phase {} min particle ({}) must be less than max ({}).".format(
                        i + 1, smin, smax
                    )
                )
    elif minPar_sim >= maxPar_sim:
        error_msg = f"Min particle size ({minPar_sim:.3f}) must be less than max ({maxPar_sim:.3f})."
        _log(error_msg)
        raise ValueError(error_msg)


    maxC = np.array(maxC)
    minC = np.array(minC)

    # Read in the seven matrices from their temporary files
    coord1 = np.load(tempPath + 'coord1.npy')
    coord2 = np.load(tempPath + 'coord2.npy')
    coord3 = np.load(tempPath + 'coord3.npy')
    coord4 = np.load(tempPath + 'coord4.npy')
    meshVertices = np.load(tempPath + 'meshVertices.npy')
    meshTets = np.load(tempPath + 'meshTets.npy')
    surfaceNodes = np.load(tempPath + 'surfaceNodes.npy')

    def _phase_sim(i, grainMin, grainMax):
        if use_phase_sim:
            return _phase_list_val(phaseMinPar, i, grainMin), _phase_list_val(phaseMaxPar, i, grainMax)
        return grainMin, grainMax

    def _phase_filler(i):
        if fillerOnlyPhases and len(phaseFillerContent) > 0:
            return (
                _phase_list_val(phaseFillerContent, i, 0.0),
                _phase_list_val(phaseFillerDensity, i, 0.0),
            )
        return fillerC, fillerDensity

    def _phase_offset(i, simMin):
        if len(phaseOffsetCoefList) > i:
            return _phase_list_val(phaseOffsetCoefList, i, 0.2) * simMin
        return parOffset

    if multiMatToggle == "On":


        # Read in aggregate file
        try:
            [multiMatX,multiMatY,multiMatZ,multiMatRes,aggDistinctVoxels] = read_multiMat_file(aggFile)
        except:
            pass


        # Read in multi-material file
        [multiMatX,multiMatY,multiMatZ,multiMatRes,multiMatVoxels] = read_multiMat_file(multiMatFile)


        # Confirm if the voxelated multi-material file is larger than the provided geometry
        topoCheck = check_multiMat_size(multiMatX,multiMatY,multiMatZ,multiMatRes,minC,maxC)


        # Organize and store voxels of each material
        sortedVoxels = sort_multiMat_voxels(multiMatVoxels, phaseMode=phaseMode)
        [aggVoxels,itzVoxels,binderVoxels,aggVoxelIDs] = sortedVoxels
        try:
            [aggVoxels,discard2,discard3,aggVoxelIDs] = sort_multiMat_voxels(aggDistinctVoxels, phaseMode=phaseMode)
        except:
            pass

        if phaseMode == 2:
            itzVoxels = np.array([])
            itzGrainsDiameterList = np.array([])
            for i in range(2):
                if i == 0:
                    [grainMin,grainMax,grainFuller,grainSieveD,grainSieveP] = [grainAggMin,grainAggMax,grainAggFuller,grainAggSieveD,grainAggSieveP]
                else:
                    [grainMin,grainMax,grainFuller,grainSieveD,grainSieveP] = [grainBinderMin,grainBinderMax,grainBinderFuller,grainBinderSieveD,grainBinderSieveP]
                simMin, simMax = _phase_sim(i, grainMin, grainMax)
                fc, fd = _phase_filler(i)
                denom = (len(aggVoxels)+len(binderVoxels)) or 1
                nVox = len(aggVoxels) if i == 0 else len(binderVoxels)
                phaseVol = tetVolume * nVox / denom
                [maxGrainsNum, grainsDiameterList] = gen_multiMat_phase_particle_list(
                    phaseVol, grainMin, grainMax, grainFuller, grainSieveD, grainSieveP,
                    simMin, simMax, fc, fd, fillerOnlyPhases,
                    wcRatio, cementC, airFrac, flyashC, silicaC, scmC,
                    flyashDensity, silicaDensity, scmDensity, cementDensity, densityWater,
                    verbose,
                )
                if i == 0:
                    aggGrainsDiameterList = grainsDiameterList
                else:
                    binderGrainsDiameterList = grainsDiameterList
            parDiameterList = np.concatenate((aggGrainsDiameterList,binderGrainsDiameterList))
            internalNodes = (np.zeros((len(aggGrainsDiameterList)+len(binderGrainsDiameterList),3))+2)*maxC
            materialList = np.ones(len(parDiameterList)) if len(parDiameterList) > 0 else np.array([])
        else:
            phase_specs = [
                (0, grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP, len(aggVoxels)),
                (1, grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP, len(itzVoxels)),
                (2, grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP, len(binderVoxels)),
            ]
            denom = (len(aggVoxels)+len(itzVoxels)+len(binderVoxels)) or 1
            lists_by_phase = [None, None, None]
            for phase_i, grainMin, grainMax, grainFuller, grainSieveD, grainSieveP, nVox in phase_specs:
                simMin, simMax = _phase_sim(phase_i, grainMin, grainMax)
                fc, fd = _phase_filler(phase_i)
                phaseVol = tetVolume * nVox / denom
                [maxGrainsNum, grainsDiameterList] = gen_multiMat_phase_particle_list(
                    phaseVol, grainMin, grainMax, grainFuller, grainSieveD, grainSieveP,
                    simMin, simMax, fc, fd, fillerOnlyPhases,
                    wcRatio, cementC, airFrac, flyashC, silicaC, scmC,
                    flyashDensity, silicaDensity, scmDensity, cementDensity, densityWater,
                    verbose,
                )
                lists_by_phase[phase_i] = grainsDiameterList
            aggGrainsDiameterList = lists_by_phase[0]
            itzGrainsDiameterList = lists_by_phase[1]
            binderGrainsDiameterList = lists_by_phase[2]
            parDiameterList = np.concatenate((aggGrainsDiameterList,itzGrainsDiameterList,binderGrainsDiameterList))
            internalNodes = (np.zeros((len(aggGrainsDiameterList)+\
                len(binderGrainsDiameterList)+len(itzGrainsDiameterList),3))+2)*maxC
            materialList = np.ones(len(parDiameterList)) if len(parDiameterList) > 0 else np.array([])




    if multiMatToggle == "Off":


        # Shift sieve curve if needed
        if sieveCurveDiameter != (0 or None or [] or ""):
            # Shifts sieve curve to appropriate range
            [newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max] = calc_sieveCurve(minPar_exp, maxPar_exp, sieveCurveDiameter, sieveCurvePassing)
        else:
            newSieveCurveD, newSieveCurveP, w_min, w_max, NewSet = 0, 0, 0, 0, 0

        # Calculates volume of particles needed
        [volFracPar, parVolTotal, cdf, cdf1, kappa_i] = calc_parVolume(tetVolume, wcRatio, cementC,
                                                    airFrac, fullerCoef, 
                                                    flyashC, silicaC, scmC, fillerC,
                                                    flyashDensity, silicaDensity, 
                                                    scmDensity, fillerDensity, cementDensity,
                                                    densityWater, minPar_exp, maxPar_exp,
                                                    newSieveCurveD, newSieveCurveP, 
                                                    NewSet, w_min, w_max)



        if verbose_on:
            _log("Calculating particle list...")
        elif not verbose_on:
            _emit_progress("External: building particle list...", verbose_on)
        # Calculate list of particle diameters for placement
        [maxParNum,parDiameterList] = gen_particleList(parVolTotal,minPar_sim, maxPar_sim, minPar_exp, maxPar_exp,newSieveCurveD,\
            cdf,kappa_i,NewSet,fullerCoef, verbose)

        # Initialize empty particle nodes list outside geometry
        internalNodes = (np.zeros((len(parDiameterList),3))+2)*maxC
        
        materialList = np.ones(len(parDiameterList)) if len(parDiameterList) > 0 else np.array([])













    ########################## Begin Placing Particles ##############################

    # Initialize values
    newMaxIter = 50
    particlesPlaced = 0


    # Initialize particleID list of length of internalNodes
    particleID = np.zeros(len(internalNodes))

    if multiMatToggle == "On":

            def _place_phase_grains(phase_index, grainsDiameterList, voxels, placeMin, placeMax, voxelIDs, node_offset, phaseParOffset):
                nonlocal newMaxIter
                target = len(grainsDiameterList)
                phase_num = phase_index + 1
                start_time = time.time()
                iterReq = 0
                placed = []
                write_idx = 0
                for x in range(target):
                    try:
                        [newMaxIter, node, iterReq, pid] = gen_LDPMCSL_subParticle(
                            surfaceNodes, grainsDiameterList[x], meshVertices, meshTets, newMaxIter, maxIter, placeMin, placeMax,
                            phaseParOffset, parDiameterList, coord1, coord2, coord3, coord4, maxEdgeLength, max_dist, internalNodes,
                            multiMatX, multiMatY, multiMatZ, multiMatRes, voxels, voxelIDs, minC, maxC)
                        internalNodes[node_offset + write_idx, :] = node
                        particleID[node_offset + write_idx] = pid
                        placed.append(grainsDiameterList[x])
                        write_idx += 1
                    except RuntimeError:
                        iterReq = 0
                    elapsed = time.time() - start_time
                    done = x + 1
                    avg_time = elapsed / done if done > 0 else 0.0
                    eta = avg_time * max(0, target - done)
                    if verbose_on and target > 0:
                        step = max(1, int(np.rint(target / 100)))
                        if x % step == 0:
                            _log(
                                f"[{x}/{target}] Particle placement in process... Phase {phase_num}"
                                f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
                            )
                n_placed = len(placed)
                if verbose_on:
                    _log(f"Particle placement completed Phase {phase_num} ({n_placed}/{n_placed})")
                return np.asarray(placed) if n_placed > 0 else np.array([])

            if phaseMode == 2:
                sim0, sim0max = _phase_sim(0, grainAggMin, grainAggMax)
                sim1, sim1max = _phase_sim(1, grainBinderMin, grainBinderMax)
                aggGrainsDiameterList = _place_phase_grains(0, aggGrainsDiameterList, aggVoxels, sim0, sim0max, aggVoxelIDs, 0, _phase_offset(0, sim0))
                n0 = len(aggGrainsDiameterList)
                n1 = len(binderGrainsDiameterList)
                internalNodes = np.vstack([np.asarray(internalNodes[:n0]), (np.zeros((n1, 3)) + 2) * maxC])
                particleID = np.concatenate([np.asarray(particleID[:n0]), np.zeros(n1)])
                parDiameterList = np.concatenate([aggGrainsDiameterList, binderGrainsDiameterList])
                binderGrainsDiameterList = _place_phase_grains(1, binderGrainsDiameterList, binderVoxels, sim1, sim1max, 0, n0, _phase_offset(1, sim1))
                n1 = len(binderGrainsDiameterList)
                internalNodes = np.asarray(internalNodes[:n0 + n1])
                particleID = np.asarray(particleID[:n0 + n1])
                parDiameterList = np.concatenate([aggGrainsDiameterList, binderGrainsDiameterList])
                materialList = np.concatenate((
                    np.ones(len(aggGrainsDiameterList)) * 3,
                    np.ones(len(binderGrainsDiameterList)) * 2
                ))
                minPar_sim = min(sim0, sim1)
            else:
                sim0, sim0max = _phase_sim(0, grainAggMin, grainAggMax)
                sim1, sim1max = _phase_sim(1, grainITZMin, grainITZMax)
                sim2, sim2max = _phase_sim(2, grainBinderMin, grainBinderMax)
                aggGrainsDiameterList = _place_phase_grains(0, aggGrainsDiameterList, aggVoxels, sim0, sim0max, aggVoxelIDs, 0, _phase_offset(0, sim0))
                n0 = len(aggGrainsDiameterList)
                n1 = len(itzGrainsDiameterList)
                n2 = len(binderGrainsDiameterList)
                internalNodes = np.vstack([np.asarray(internalNodes[:n0]), (np.zeros((n1 + n2, 3)) + 2) * maxC])
                particleID = np.concatenate([np.asarray(particleID[:n0]), np.zeros(n1 + n2)])
                parDiameterList = np.concatenate([aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList])
                itzGrainsDiameterList = _place_phase_grains(1, itzGrainsDiameterList, itzVoxels, sim1, sim1max, 0, n0, _phase_offset(1, sim1))
                n1 = len(itzGrainsDiameterList)
                n2 = len(binderGrainsDiameterList)
                internalNodes = np.vstack([np.asarray(internalNodes[:n0 + n1]), (np.zeros((n2, 3)) + 2) * maxC])
                particleID = np.concatenate([np.asarray(particleID[:n0 + n1]), np.zeros(n2)])
                parDiameterList = np.concatenate([aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList])
                binderGrainsDiameterList = _place_phase_grains(
                    2, binderGrainsDiameterList, binderVoxels, sim2, sim2max, 0,
                    n0 + n1, _phase_offset(2, sim2)
                )
                n2 = len(binderGrainsDiameterList)
                internalNodes = np.asarray(internalNodes[:n0 + n1 + n2])
                particleID = np.asarray(particleID[:n0 + n1 + n2])
                parDiameterList = np.concatenate([aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList])
                materialList = np.concatenate((
                    np.ones(len(aggGrainsDiameterList)) * 3,
                    np.ones(len(itzGrainsDiameterList)) * 1,
                    np.ones(len(binderGrainsDiameterList)) * 2
                ))
                minPar_sim = min(sim0, sim1, sim2)
            particlesPlaced = len(parDiameterList)


    # Create empty lists if not cementStructure
    PoresDiameterList, ClinkerDiameterList, CHDiameterList, CSH_LDDiameterList, CSH_HDDiameterList = 0,0,0,0,0






    if multiMatToggle == "Off":

        use_parallel = (numCPU > 1) and USE_PROCESSES and (platform.system() != 'Windows')
        
        if use_parallel:
            worker_exe = configure_multiprocessing_for_freecad()
            if verbose_on:
                _log("Particle placement in process... ({} CPUs)".format(numCPU))
            
            batch_size = max(10, len(parDiameterList) // (numCPU * 4))
            
            try:
                executor = ProcessPoolExecutor(max_workers=numCPU)
                try:
                    while particlesPlaced < len(parDiameterList):
                        batch_end = min(particlesPlaced + batch_size, len(parDiameterList))
                        particle_batch = parDiameterList[particlesPlaced:batch_end]

                        futures = []
                        for parDiam in particle_batch:
                            future = executor.submit(gen_particleMPI, surfaceNodes, maxParNum, minC, maxC, 
                                                    meshVertices, meshTets, coord1, coord2, coord3, coord4,
                                                    newMaxIter, maxIter, minPar_sim, maxPar_sim, parOffset,
                                                    verbose, parDiameterList, maxEdgeLength, max_dist, 
                                                    internalNodes.copy(), parDiam)
                            futures.append(future)
                        
                        outputMPI = [future.result() for future in futures]

                        nodeMPI = np.array(outputMPI)[:,0:3]
                        diameter = np.array(outputMPI)[:,3]
                        newMaxIter = int(max(np.array(outputMPI)[:,4]))

                        for x in range(len(nodeMPI)):
                            internalNodes[particlesPlaced+x,:] = nodeMPI[x,:]

                            if x > 0:
                                binMin = np.array(([nodeMPI[x,0]-diameter[x]/2-maxPar_sim/2-parOffset,\
                                    nodeMPI[x,1]-diameter[x]/2-maxPar_sim/2-parOffset,nodeMPI[x,2]-\
                                    diameter[x]/2-maxPar_sim/2-parOffset]))
                                binMax = np.array(([nodeMPI[x,0]+diameter[x]/2+maxPar_sim/2+parOffset,\
                                    nodeMPI[x,1]+diameter[x]/2+maxPar_sim/2+parOffset,nodeMPI[x,2]+\
                                    diameter[x]/2+maxPar_sim/2+parOffset]))

                                overlap = check_particleOverlapMPI(nodeMPI[x,:],diameter[x],binMin,\
                                    binMax,minPar_sim,parOffset,nodeMPI[0:x],diameter[0:x])

                                if overlap == True:
                                    try:
                                        [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,\
                                            parDiameterList[particlesPlaced+x], meshVertices, \
                                            meshTets,newMaxIter,maxIter,minPar_sim,\
                                            maxPar_sim,parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes,\
                                            quiet=not verbose_on)
                                        internalNodes[particlesPlaced+x,:] = node[0,:]
                                    except RuntimeError:
                                        internalNodes[particlesPlaced+x,:] = np.array([maxC[0]*1000, maxC[1]*1000, maxC[2]*1000])

                        particlesPlaced = particlesPlaced + len(nodeMPI)

                        if verbose_on:
                            _log("[" + str(particlesPlaced) + '/' + str(len(parDiameterList)) + "] Particle placement in process...")
                
                finally:
                    executor.shutdown(wait=True)
                
                particlesPlaced = len(parDiameterList)

            except (BrokenProcessPool, OSError) as e:
                if verbose_on:
                    _log("Multiprocessing failed; using single-threaded placement.")
            
        else:
            if verbose_on:
                _log("Particle placement in process... (single-threaded)")


    if multiMatToggle == "Off" and verbose_on:
        _log('[0/' + str(len(internalNodes)) + '] Particle placement in process...')

    write_idx = particlesPlaced
    particles_skipped = 0
    if particlesPlaced < len(parDiameterList):
        start_time = time.time()
        last_report_time = start_time
        if verbose_on:
            _log(f"[{particlesPlaced}/{len(parDiameterList)}] Particle placement in process...")
        if not verbose_on:
            _emit_progress(
                f"[0/{len(parDiameterList)}] Particle placement in process...",
                verbose_on,
            )
    
    orig_n = len(parDiameterList)
    for x in range(particlesPlaced, orig_n):

        particle_start = time.time()
        
        try:
            [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,parDiameterList[x],meshVertices,meshTets,newMaxIter,maxIter,minPar_sim,maxPar_sim,\
                parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes, quiet=not verbose_on)
                
        except RuntimeError as e:
            particles_skipped += 1
            iterReq = 0
            particle_time = time.time() - particle_start
            elapsed = time.time() - start_time
            remaining = orig_n - x - 1
            avg_time = elapsed / max(1, (x + 1 - particles_skipped))
            eta = avg_time * remaining
            if verbose_on and x % 10 == 0:
                status = f"[{x+1}/{orig_n}] Particle placement in process..."
                status += f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
                _log(status)
            elif not verbose_on and orig_n > 0:
                now = time.time()
                if now - last_report_time >= 2.0:
                    last_report_time = now
                    _emit_progress(
                        f"[{x+1}/{orig_n}] Particle placement in process..."
                        f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s",
                        verbose_on,
                    )
            continue

        particle_time = time.time() - particle_start
        elapsed = time.time() - start_time
        remaining = orig_n - x - 1
        avg_time = elapsed / (x + 1 - particles_skipped) if (x + 1 - particles_skipped) > 0 else particle_time
        eta = avg_time * remaining
        
        if verbose_on and (iterReq < 100 or x % 10 == 0):
            status = f"[{x+1}/{orig_n}] Particle placement in process..."
            status += f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
            _log(status)
        elif not verbose_on and orig_n > 0:
            now = time.time()
            if now - last_report_time >= 2.0:
                last_report_time = now
                _emit_progress(
                    f"[{x+1}/{orig_n}] Particle placement in process..."
                    f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s",
                    verbose_on,
                )

        if write_idx != x:
            parDiameterList[write_idx] = parDiameterList[x]
        internalNodes[write_idx,:] = node
        write_idx += 1

        if verbose_on and platform.system() == 'Windows':
            try:
                from PySide2 import QtWidgets
                QtWidgets.QApplication.processEvents()
            except ImportError:
                try:
                    from PySide import QtWidgets
                    QtWidgets.QApplication.processEvents()
                except ImportError:
                    pass

    if write_idx < orig_n:
        parDiameterList = np.asarray(parDiameterList[:write_idx])
        internalNodes = np.asarray(internalNodes[:write_idx])
        particleID = np.asarray(particleID[:write_idx])

    if multiMatToggle == "Off":
        if particlesPlaced < orig_n:
            done_msg = "Particle placement completed."
            if verbose_on:
                _log(done_msg)
            else:
                _emit_progress(done_msg, verbose_on)
        elif not verbose_on:
            _emit_progress("Particle placement completed.", verbose_on)

    if multiMatToggle == "Off":
        materialList = np.ones(len(parDiameterList))
        # Create empty lists if not multi-material or cementStructure
        aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList, PoresDiameterList,\
            ClinkerDiameterList, CHDiameterList, CSH_LDDiameterList, CSH_HDDiameterList = 0,0,0,0,0,0,0,0


    try:
        if len(materialList) != len(parDiameterList):
            raise ValueError("materialList length mismatch")
    except (NameError, ValueError):
        if len(parDiameterList) > 0:
            materialList = np.ones(len(parDiameterList))
            _log("MaterialList reset to default.")
        else:
            materialList = np.array([])
            _log("MaterialList empty.")

    # Save the internalNodes list to a temporary file
    np.save(tempPath + 'internalNodes.npy', internalNodes)

    # Save the materialList to a temporary file
    np.save(tempPath + 'materialList.npy', materialList)

    # Save the parDiameterList to a temporary file
    np.save(tempPath + 'parDiameterList.npy', parDiameterList)

    # Save the particleIDs to a temporary file
    np.save(tempPath + 'particleID.npy', particleID)

    if multiMatToggle == "Off":
        np.save(tempPath + 'volFracPar.npy', volFracPar)
        np.save(tempPath + 'parVolTotal.npy', parVolTotal)




    #placementTime = round(time.time() - start_time,2)
    nParticles = len(parDiameterList)


    ########################## Begin Fiber Generation ##############################

    fiber_result = None

    if fiberToggle in ['on','On','Y','y','Yes','yes']:

        import math
        fiberStartTime = time.time()

        if fiberFile and str(fiberFile).strip() and str(fiberFile).strip() not in ["0", "None", "[]"]:

            try:
                from freecad.ldpmWorkbench.input.read_ctScan_file import read_ctScan_file
                CTScanFiberData = read_ctScan_file(fiberFile)
            except (FileNotFoundError, IOError, ValueError, OSError) as e:
                error_msg = f"ERROR: Could not read CT scan fiber file '{fiberFile}': {e}"
                _log(error_msg)
                raise RuntimeError(error_msg) from e
            
            # Check if any fibers were loaded
            if len(CTScanFiberData) == 0:
                error_msg = f"ERROR: No valid fibers found in CT scan file '{fiberFile}'"
                _log(error_msg)
                raise RuntimeError(error_msg)
            
            CTScanFiberData = np.array(CTScanFiberData).reshape(-1,10)
            p1Fibers = CTScanFiberData[:,0:3]
            p2Fibers = CTScanFiberData[:,3:6]
            orienFibers = CTScanFiberData[:,6:9]
            fiberLengths = CTScanFiberData[:,9:10]
            
            if len(p1Fibers) == 0:
                error_msg = f"ERROR: No fibers extracted from CT scan file '{fiberFile}'"
                _log(error_msg)
                raise RuntimeError(error_msg)
            
            # Set number of fibers from CT scan data
            nFiber = len(p1Fibers)
            fiberTime = round(time.time() - fiberStartTime,2)
            if verbose_on:
                _log(f'Loaded {nFiber} fibers in {fiberTime}s.')
            else:
                _emit_progress(f"External: loaded {nFiber} fibers from CT scan.", verbose_on)

        else:

            if fiberPref<0 or fiberPref>1:
                _log('Fiber orientation strength is out of range, use 0-1')

            # Calculate number of fibers needed
            nFiber = int(round(4*tetVolume*fiberVol/(math.pi*fiberDiameter**2*fiberLength)))

            if not verbose_on and nFiber > 0:
                _emit_progress(f"External: generating {nFiber} fibers.", verbose_on)

            # Initialize empty fiber nodes list outside geometry
            p1Fibers = (np.zeros((nFiber,3))+2)*maxC
            p2Fibers = (np.zeros((nFiber,3))+2)*maxC
            orienFibers = (np.zeros((nFiber,3))+2)*maxC
            fiberLengths = (np.zeros((nFiber,1)))

            for x in range(0,nFiber):

                if verbose_on and x % 100 == 0:
                    _log(str(nFiber-x) + ' Fibers Remaining')

                # Generate fiber
                [p1Fiber, p2Fiber, orienFiber, lFiber] = gen_LDPMCSL_fibers(meshVertices,meshTets,coord1,\
                    coord2,coord3,coord4,maxIter,fiberLength,maxC,maxPar_sim,\
                    np.array([fiberOrientation1, fiberOrientation2, fiberOrientation3]),fiberPref,surfaceFaces,\
                    fiberCutting,None)
                p1Fibers[x,:] = p1Fiber
                p2Fibers[x,:] = p2Fiber
                orienFibers[x,:] = orienFiber
                fiberLengths[x,:] = lFiber

                if platform.system() == 'Windows':
                    try:
                        from PySide2 import QtWidgets
                        QtWidgets.QApplication.processEvents()
                    except ImportError:
                        try:
                            from PySide import QtWidgets
                            QtWidgets.QApplication.processEvents()
                        except ImportError:
                            pass

            fiberTime = round(time.time() - fiberStartTime, 2)
            if verbose_on:
                _log(str(nFiber) + ' fibers placed in ' + str(fiberTime) + ' seconds')

        if fiberOutputFiles in ['on','On','Y','y','Yes','yes']:
            np.save(tempPath + "p1Fibers.npy", p1Fibers)
            np.save(tempPath + "p2Fibers.npy", p2Fibers)
            np.save(tempPath + "orienFibers.npy", orienFibers)
            np.save(tempPath + "fiberLengths.npy", fiberLengths)
            np.save(tempPath + "fiberDiameter.npy", np.array([fiberDiameter]))
            np.save(tempPath + "nFiber.npy", np.array([nFiber]))

        fiber_result = (p1Fibers, p2Fibers, orienFibers, fiberLengths, fiberDiameter, nFiber)

    return fiber_result