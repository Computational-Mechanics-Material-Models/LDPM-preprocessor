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
##
## MPI Driver for LDPMCSL
##
## ===========================================================================


import json
import sys
from pathlib import Path

import numpy as np
from mpi4py import MPI

_WORKBENCH_ROOT = str(Path(__file__).resolve().parents[3])
if _WORKBENCH_ROOT not in sys.path:
    sys.path.insert(0, _WORKBENCH_ROOT)

from freecad.ldpmWorkbench.generation.domain_decomposition import decompose_domain
from freecad.ldpmWorkbench.generation.gen_particle import gen_particle


def _local_pool(myNodes, myDiam, haloNodes, haloDiam):
    if len(haloNodes) == 0:
        return myNodes, myDiam
    if len(myNodes) == 0:
        return haloNodes, haloDiam
    return np.vstack([myNodes, haloNodes]), np.concatenate([myDiam, haloDiam])


def _sync_halo(comm, block, neighbor_ranks, placedNodes, placedDiam):
    gathered = comm.allgather((placedNodes, placedDiam))
    haloNodes = []
    haloDiam = []
    my_rank = comm.Get_rank()
    allowed = set(neighbor_ranks)
    for r, (nodes_r, diam_r) in enumerate(gathered):
        if r == my_rank or r not in allowed:
            continue
        if len(nodes_r) == 0:
            continue
        mask = block.contains_points_halo(nodes_r)
        if mask.any():
            haloNodes.append(nodes_r[mask])
            haloDiam.append(diam_r[mask])

    if haloNodes:
        return np.vstack(haloNodes), np.concatenate(haloDiam)
    return np.zeros((0, 3)), np.zeros(0)


def run_mpi_particle_generation(minC, maxC, meshVertices, meshTets, surfaceNodes,
                                parDiameterList, coord1, coord2, coord3, coord4,
                                maxIter, minPar, maxPar, parOffset, maxEdgeLength,
                                max_dist, syncEvery=25, verbose=False):

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    np.random.seed(42 + rank)

    haloWidth = maxPar + parOffset
    parDiameterList = np.asarray(parDiameterList, dtype=float)

    if rank == 0:
        decomp = decompose_domain(minC, maxC, size, meshVertices, meshTets,
                                  parDiameterList, haloWidth)
    else:
        decomp = None
    decomp = comm.bcast(decomp, root=0)

    block = decomp.blocks[rank]
    neighbor_ranks = decomp.neighbors_of(rank)

    myTetMask = decomp.tets_for_rank(rank)
    myDiamMask = decomp.diameters_for_rank(rank)

    myTets = meshTets[myTetMask]
    myCoord1 = coord1[myTetMask]
    myCoord2 = coord2[myTetMask]
    myCoord3 = coord3[myTetMask]
    myCoord4 = coord4[myTetMask]
    myDiamList = parDiameterList[myDiamMask]
    myDiamList = myDiamList[np.argsort(-myDiamList)]

    placedNodes = np.zeros((0, 3))
    placedDiam = np.zeros(0)
    haloNodes = np.zeros((0, 3))
    haloDiam = np.zeros(0)

    newMaxIter0 = 50
    failedCount = 0
    haveTets = len(myTets) > 0
    placeMaxIter = min(int(maxIter), 500)

    maxLocal = comm.allreduce(len(myDiamList), op=MPI.MAX)

    for i in range(maxLocal):
        if i < len(myDiamList) and haveTets:
            parDiameter = float(myDiamList[i])
            poolNodes, poolDiam = _local_pool(placedNodes, placedDiam, haloNodes, haloDiam)
            newMaxIter = newMaxIter0

            try:
                [newMaxIter, node, iterReq] = gen_particle(
                    surfaceNodes, parDiameter, meshVertices, myTets,
                    newMaxIter, placeMaxIter, minPar, maxPar, parOffset,
                    poolDiam, myCoord1, myCoord2, myCoord3, myCoord4,
                    maxEdgeLength, max_dist, poolNodes, quiet=True
                )
                placedNodes = np.vstack([placedNodes, node]) if len(placedNodes) else np.asarray(node)
                placedDiam = np.append(placedDiam, parDiameter)
            except RuntimeError:
                failedCount += 1
            if verbose and ((i + 1) % 100 == 0 or (i + 1) == len(myDiamList)):
                print("rank %d: particle %d/%d, failed %d" % (rank, i + 1, len(myDiamList), failedCount), flush=True)
        elif i < len(myDiamList):
            failedCount += 1

        if (i + 1) % syncEvery == 0:
            haloNodes, haloDiam = _sync_halo(
                comm, block, neighbor_ranks, placedNodes, placedDiam)

    haloNodes, haloDiam = _sync_halo(
        comm, block, neighbor_ranks, placedNodes, placedDiam)

    allNodes = comm.gather(placedNodes, root=0)
    allDiam = comm.gather(placedDiam, root=0)
    allFailed = comm.gather(failedCount, root=0)

    if rank == 0:
        node_chunks = [n for n in allNodes if n is not None and len(n)]
        diam_chunks = [d for d in allDiam if d is not None and len(d)]
        if node_chunks:
            finalNodes = np.vstack(node_chunks)
            finalDiam = np.concatenate(diam_chunks)
        else:
            finalNodes = np.zeros((0, 3))
            finalDiam = np.zeros(0)
        totalFailed = sum(allFailed)
        return finalNodes, finalDiam, totalFailed

    return None, None, None


def _sieve_present(value):
    if value in [None, 0, "", [], "0"]:
        return False
    return True


def _resolve_bundle_dir(argv):
    if len(argv) > 1 and not str(argv[1]).startswith("--"):
        return Path(argv[1]).resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "external_manifest_ldpmcsl.json").is_file():
        return cwd
    return cwd


def _load_mesh(bundle):
    needed = [
        "meshVertices.npy", "meshTets.npy", "surfaceNodes.npy",
        "coord1.npy", "coord2.npy", "coord3.npy", "coord4.npy",
    ]
    missing = [n for n in needed if not (bundle / n).is_file()]
    if missing:
        raise FileNotFoundError(
            "Mesh files missing in %s: %s. Run external meshing first." %
            (bundle, ", ".join(missing)))
    return (
        np.load(bundle / "meshVertices.npy"),
        np.load(bundle / "meshTets.npy"),
        np.load(bundle / "surfaceNodes.npy"),
        np.load(bundle / "coord1.npy"),
        np.load(bundle / "coord2.npy"),
        np.load(bundle / "coord3.npy"),
        np.load(bundle / "coord4.npy"),
    )


def _build_diameter_list(cfg, verbose):
    from freecad.ldpmWorkbench.generation.calc_sieveCurve import calc_sieveCurve
    from freecad.ldpmWorkbench.generation.calc_parVolume import calc_parVolume
    from freecad.ldpmWorkbench.generation.gen_particleList import gen_particleList

    if _sieve_present(cfg.get("sieveCurveDiameter")):
        newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max = calc_sieveCurve(
            cfg["minPar_exp"], cfg["maxPar_exp"],
            cfg["sieveCurveDiameter"], cfg["sieveCurvePassing"])
    else:
        newSieveCurveD, newSieveCurveP, w_min, w_max, NewSet = 0, 0, 0, 0, 0

    volFracPar, parVolTotal, cdf, cdf1, kappa_i = calc_parVolume(
        cfg["tetVolume"], cfg["wcRatio"], cfg["cementC"], cfg["airFrac"],
        cfg["fullerCoef"], cfg["flyashC"], cfg["silicaC"], cfg["scmC"],
        cfg["fillerC"], cfg["flyashDensity"], cfg["silicaDensity"],
        cfg["scmDensity"], cfg["fillerDensity"], cfg["cementDensity"],
        cfg["densityWater"], cfg["minPar_exp"], cfg["maxPar_exp"],
        newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max)

    maxParNum, parDiameterList = gen_particleList(
        parVolTotal, cfg["minPar_sim"], cfg["maxPar_sim"],
        cfg["minPar_exp"], cfg["maxPar_exp"], newSieveCurveD, cdf, kappa_i,
        NewSet, cfg["fullerCoef"], verbose="On" if verbose else "Off")

    return np.asarray(parDiameterList, dtype=float), volFracPar, parVolTotal


def _write_particle_outputs(bundle, nodes, diams, volFracPar=None, parVolTotal=None):
    n = len(diams)
    np.save(bundle / "internalNodes.npy", np.asarray(nodes, dtype=float).reshape(n, 3))
    np.save(bundle / "parDiameterList.npy", np.asarray(diams, dtype=float).reshape(n))
    np.save(bundle / "materialList.npy", np.ones(n))
    np.save(bundle / "particleID.npy", np.zeros(n))
    if volFracPar is not None:
        np.save(bundle / "volFracPar.npy", volFracPar)
    if parVolTotal is not None:
        np.save(bundle / "parVolTotal.npy", parVolTotal)


def run_from_bundle(bundle_dir, syncEvery=25):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    bundle = Path(bundle_dir).resolve()
    manifest_path = bundle / "external_manifest_ldpmcsl.json"

    cfg = None
    extra = None
    if rank == 0:
        if not manifest_path.is_file():
            raise FileNotFoundError("Missing manifest: %s" % manifest_path)
        with open(manifest_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        verbose = True
        meshVertices, meshTets, surfaceNodes, coord1, coord2, coord3, coord4 = _load_mesh(bundle)

        diam_path = bundle / "parDiameterList.npy"
        volFracPar = None
        parVolTotal = None
        if diam_path.is_file():
            parDiameterList = np.load(diam_path)
            if verbose:
                print("Loaded %d diameters" % len(parDiameterList))
        else:
            parDiameterList, volFracPar, parVolTotal = _build_diameter_list(cfg, verbose)
            np.save(diam_path, parDiameterList)
            if verbose:
                print("Built %d diameters" % len(parDiameterList))

        extra = dict(
            meshVertices=meshVertices, meshTets=meshTets, surfaceNodes=surfaceNodes,
            coord1=coord1, coord2=coord2, coord3=coord3, coord4=coord4,
            parDiameterList=parDiameterList, volFracPar=volFracPar, parVolTotal=parVolTotal,
            verbose=verbose,
        )

    cfg = comm.bcast(cfg, root=0)
    extra = comm.bcast(extra, root=0)

    finalNodes, finalDiam, totalFailed = run_mpi_particle_generation(
        np.asarray(cfg["minC"], dtype=float),
        np.asarray(cfg["maxC"], dtype=float),
        extra["meshVertices"], extra["meshTets"], extra["surfaceNodes"],
        extra["parDiameterList"],
        extra["coord1"], extra["coord2"], extra["coord3"], extra["coord4"],
        maxIter=int(cfg["maxIter"]),
        minPar=float(cfg["minPar_sim"]),
        maxPar=float(cfg["maxPar_sim"]),
        parOffset=float(cfg["parOffset"]),
        maxEdgeLength=float(cfg["maxEdgeLength"]),
        max_dist=float(cfg["max_dist"]),
        syncEvery=syncEvery,
        verbose=extra["verbose"],
    )

    if rank == 0:
        _write_particle_outputs(
            bundle, finalNodes, finalDiam,
            extra["volFracPar"], extra["parVolTotal"])
        print("Placed %d particles, %d failed" % (len(finalDiam), totalFailed))

    return finalNodes, finalDiam, totalFailed


if __name__ == "__main__":
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    bundle = _resolve_bundle_dir(sys.argv)
    try:
        run_from_bundle(bundle)
    except Exception:
        if rank == 0:
            raise
        raise
