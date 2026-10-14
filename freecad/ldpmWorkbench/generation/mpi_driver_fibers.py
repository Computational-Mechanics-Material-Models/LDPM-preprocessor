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
## MPI Driver for Fibers
##
## ===========================================================================


import json
import math
import sys
from pathlib import Path

import numpy as np
from mpi4py import MPI

_WORKBENCH_ROOT = str(Path(__file__).resolve().parents[3])
if _WORKBENCH_ROOT not in sys.path:
    sys.path.insert(0, _WORKBENCH_ROOT)

from freecad.ldpmWorkbench.generation.gen_3DCP_interlayer import build_interface_regions
from freecad.ldpmWorkbench.generation.fiber_domain_decomposition import decompose_fiber_domain
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_orientationPath import load_path_segments_json
from freecad.ldpmWorkbench.generation.mpi_fiber_placement import (
    attach_halo_grid,
    build_mesh_cache,
    place_one_fiber,
)


def _toggle_on(value):
    return str(value).strip().lower() in ["on", "y", "yes", "true", "1"]


def _resolve_bundle_dir(argv):
    args = [a for a in argv[1:] if not str(a).startswith("--")]
    if args:
        return Path(args[0]).resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "external_manifest_ldpmcsl.json").is_file():
        return cwd
    return cwd


def _load_mesh(bundle):
    needed = [
        "meshVertices.npy", "meshTets.npy", "surfaceFaces.npy",
        "coord1.npy", "coord2.npy", "coord3.npy", "coord4.npy",
    ]
    missing = [n for n in needed if not (bundle / n).is_file()]
    if missing:
        raise FileNotFoundError(
            "Mesh files missing: %s. Run external meshing first." % ", ".join(missing))
    return (
        np.load(bundle / "meshVertices.npy"),
        np.load(bundle / "meshTets.npy"),
        np.load(bundle / "surfaceFaces.npy"),
        np.load(bundle / "coord1.npy"),
        np.load(bundle / "coord2.npy"),
        np.load(bundle / "coord3.npy"),
        np.load(bundle / "coord4.npy"),
    )


def _n_fibers(cfg):
    tetVolume = float(cfg["tetVolume"])
    fiberVol = float(cfg["fiberVol"])
    fiberDiameter = float(cfg["fiberDiameter"])
    fiberLength = float(cfg["fiberLength"])
    if fiberDiameter <= 0 or fiberLength <= 0:
        return 0
    return int(round(4.0 * tetVolume * fiberVol /
                     (math.pi * fiberDiameter ** 2 * fiberLength)))


def _load_path_segments(bundle, cfg):
    if not cfg.get("hasPathSegments"):
        return None
    path = bundle / "pathSegments_sweep3dp.json"
    if not path.is_file():
        return None
    return load_path_segments_json(str(path))


def run_mpi_fiber_generation(minC, maxC, meshVertices, meshTets, surfaceFaces,
                             nFibers, maxIter, fiberLength, maxAggD,
                             fiberOrientation, orientationStrength, cutFiber,
                             pathSegments=None, interfaceRegions=None, verbose=False):

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    np.random.seed(1000 + rank)

    fiberOrientation = np.asarray(fiberOrientation, dtype=float)

    if rank == 0:
        decomp = decompose_fiber_domain(
            nFibers, size, meshVertices, meshTets,
            minC=minC, maxC=maxC, fiberLength=fiberLength)
    else:
        decomp = None
    decomp = comm.bcast(decomp, root=0)

    myCount = int(decomp.counts[rank])
    myTetMask = decomp.tets_for_rank(rank)
    myTets = meshTets[myTetMask]
    halo_mask = decomp.halo_mask_for_rank(rank)

    mesh_cache = build_mesh_cache(meshVertices, meshTets, surfaceFaces)
    attach_halo_grid(mesh_cache, halo_mask)

    p1List = []
    p2List = []
    orienList = []
    lenList = []
    failedCount = 0

    if myCount > 0 and len(myTets) == 0:
        failedCount = myCount
        myCount = 0

    for i in range(myCount):
        try:
            p1Fiber, p2Fiber, orienFiber, lFiber = place_one_fiber(
                myTets, mesh_cache, maxIter, fiberLength,
                fiberOrientation, orientationStrength, cutFiber,
                pathSegments,
                interfaceRegions,
            )
            p1List.append(np.asarray(p1Fiber, dtype=float).reshape(3))
            p2List.append(np.asarray(p2Fiber, dtype=float).reshape(3))
            orienList.append(np.asarray(orienFiber, dtype=float).reshape(3))
            lenList.append(float(lFiber))
        except RuntimeError:
            failedCount += 1
        if verbose and ((i + 1) % 100 == 0 or (i + 1) == myCount):
            print("rank %d: fiber %d/%d, failed %d" % (
                rank, i + 1, myCount, failedCount), flush=True)

    if p1List:
        local_p1 = np.vstack(p1List)
        local_p2 = np.vstack(p2List)
        local_orien = np.vstack(orienList)
        local_len = np.asarray(lenList, dtype=float).reshape(-1, 1)
    else:
        local_p1 = np.zeros((0, 3))
        local_p2 = np.zeros((0, 3))
        local_orien = np.zeros((0, 3))
        local_len = np.zeros((0, 1))

    all_p1 = comm.gather(local_p1, root=0)
    all_p2 = comm.gather(local_p2, root=0)
    all_orien = comm.gather(local_orien, root=0)
    all_len = comm.gather(local_len, root=0)
    all_failed = comm.gather(failedCount, root=0)

    if rank == 0:
        chunks_p1 = [a for a in all_p1 if a is not None and len(a)]
        chunks_p2 = [a for a in all_p2 if a is not None and len(a)]
        chunks_orien = [a for a in all_orien if a is not None and len(a)]
        chunks_len = [a for a in all_len if a is not None and len(a)]
        if chunks_p1:
            p1Fibers = np.vstack(chunks_p1)
            p2Fibers = np.vstack(chunks_p2)
            orienFibers = np.vstack(chunks_orien)
            fiberLengths = np.vstack(chunks_len)
        else:
            p1Fibers = np.zeros((0, 3))
            p2Fibers = np.zeros((0, 3))
            orienFibers = np.zeros((0, 3))
            fiberLengths = np.zeros((0, 1))
        totalFailed = sum(all_failed)
        return p1Fibers, p2Fibers, orienFibers, fiberLengths, totalFailed

    return None, None, None, None, None


def _write_fiber_outputs(bundle, p1, p2, orien, lengths, fiberDiameter):
    n = len(p1)
    np.save(bundle / "p1Fibers.npy", np.asarray(p1, dtype=float).reshape(n, 3))
    np.save(bundle / "p2Fibers.npy", np.asarray(p2, dtype=float).reshape(n, 3))
    np.save(bundle / "orienFibers.npy", np.asarray(orien, dtype=float).reshape(n, 3))
    np.save(bundle / "fiberLengths.npy", np.asarray(lengths, dtype=float).reshape(n, 1))
    np.save(bundle / "fiberDiameter.npy", np.array([float(fiberDiameter)]))
    np.save(bundle / "nFiber.npy", np.array([n]))


def run_from_bundle(bundle_dir):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    bundle = Path(bundle_dir).resolve()
    manifest_path = bundle / "external_manifest_ldpmcsl.json"

    cfg = None
    extra = None
    err = None
    if rank == 0:
        try:
            if not manifest_path.is_file():
                raise FileNotFoundError("Missing manifest: %s" % manifest_path)
            with open(manifest_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            if not _toggle_on(cfg.get("fiberToggle", "Off")):
                raise RuntimeError("fiberToggle is Off in the manifest.")

            verbose = True
            meshVertices, meshTets, surfaceFaces, _c1, _c2, _c3, _c4 = _load_mesh(bundle)
            nFibers = _n_fibers(cfg)
            pathSegments = _load_path_segments(bundle, cfg)
            interfaceRegions = None
            if not _toggle_on(cfg.get("fiberInterfaceIntersect", "On")):
                interfaceRegions = build_interface_regions(
                    cfg["minC"], cfg["maxC"], cfg.get("interlayer") or {}
                )
                if not interfaceRegions:
                    interfaceRegions = None
            if verbose:
                print("Fibers: %d" % nFibers)

            extra = dict(
                meshVertices=meshVertices, meshTets=meshTets,
                surfaceFaces=surfaceFaces,
                nFibers=nFibers, pathSegments=pathSegments,
                interfaceRegions=interfaceRegions, verbose=verbose,
            )
        except Exception as exc:
            err = "%s: %s" % (type(exc).__name__, exc)

    err = comm.bcast(err, root=0)
    if err:
        raise RuntimeError(err)

    cfg = comm.bcast(cfg, root=0)
    extra = comm.bcast(extra, root=0)

    p1, p2, orien, lengths, totalFailed = run_mpi_fiber_generation(
        np.asarray(cfg["minC"], dtype=float),
        np.asarray(cfg["maxC"], dtype=float),
        extra["meshVertices"], extra["meshTets"], extra["surfaceFaces"],
        nFibers=int(extra["nFibers"]),
        maxIter=int(cfg["maxIter"]),
        fiberLength=float(cfg["fiberLength"]),
        maxAggD=float(cfg["maxPar_sim"]),
        fiberOrientation=np.array([
            cfg["fiberOrientation1"],
            cfg["fiberOrientation2"],
            cfg["fiberOrientation3"],
        ], dtype=float),
        orientationStrength=float(cfg["fiberPref"]),
        cutFiber=cfg["fiberCutting"],
        pathSegments=extra["pathSegments"],
        interfaceRegions=extra.get("interfaceRegions"),
        verbose=extra["verbose"],
    )

    if rank == 0:
        _write_fiber_outputs(
            bundle, p1, p2, orien, lengths, cfg["fiberDiameter"])
        print("Placed %d fibers, %d failed" % (len(p1), totalFailed))

    return p1, p2, orien, lengths, totalFailed


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
