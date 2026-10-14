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
## MPI Driver for Facets
##
## ===========================================================================


import gc
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
from mpi4py import MPI

_WORKBENCH_ROOT = str(Path(__file__).resolve().parents[3])
if _WORKBENCH_ROOT not in sys.path:
    sys.path.insert(0, _WORKBENCH_ROOT)

from freecad.ldpmWorkbench.generation.gen_reinforcement import generate_reinforcement
from freecad.ldpmWorkbench.generation.gen_3DCP_interlayer import apply_3DCP_interlayer
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_flowEdges import gen_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_orientationPath import load_path_segments_json
from freecad.ldpmWorkbench.generation.mpi_fiber_facet_intersection import run_mpi_fiber_facet_int
from freecad.ldpmWorkbench.random_field_generation.driver_RF import (
    apply_rf_eole_to_facet_data,
    resolve_rf_realization,
)
from freecad.ldpmWorkbench.generation.gen_LDPM_facetData import gen_LDPM_facetData
from freecad.ldpmWorkbench.generation.gen_CSL_facetData import gen_CSL_facetData
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tetrahedralization import (
    gen_LDPMCSL_tetrahedralization,
)
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tesselation import (
    gen_LDPMCSL_tesselation,
)
from freecad.ldpmWorkbench.input.read_LDPMCSL_tetgen import read_LDPMCSL_tetgen
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_edges import mkData_LDPMCSL_edges
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_faceFacets import mkData_LDPMCSL_faceFacets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetfiberInt import (
    mkData_LDPMCSL_facetfiberInt,
)
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facets import mkData_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetsVertices import (
    mkData_LDPMCSL_facetsVertices,
)
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_tets import mkData_LDPMCSL_tets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_flowEdges import mkData_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkData_nodes import mkData_nodes
from freecad.ldpmWorkbench.output.mkData_particles import mkData_particles
from freecad.ldpmWorkbench.output.mkIges_LDPMCSL_flowEdges import mkIges_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_facets import mkVtk_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_flowEdges import mkVtk_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_reinforcement import (
    mkVtk_LDPMCSL_reinforcement,
)
from freecad.ldpmWorkbench.output.mkVtk_orientationPath import mkVtk_orientationPath
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_fibers import mkVtk_LDPMCSL_fibers
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_nonIntFibers import (
    mkVtk_LDPMCSL_nonIntFibers,
)
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_projFacets import mkVtk_LDPMCSL_projFacets
from freecad.ldpmWorkbench.output.mkVtk_particles import mkVtk_particles


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


_TESS_ARRAYS = (
    ("allNodes", "tess_allNodes.npy"),
    ("allTets", "tess_allTets.npy"),
    ("allEdges", "tess_allEdges.npy"),
    ("tetFacets", "tess_tetFacets.npy"),
    ("facetCenters", "tess_facetCenters.npy"),
    ("facetAreas", "tess_facetAreas.npy"),
    ("facetNormals", "tess_facetNormals.npy"),
    ("tetn1", "tess_tetn1.npy"),
    ("tetn2", "tess_tetn2.npy"),
    ("materialList", "tess_materialList.npy"),
    ("particleID", "tess_particleID.npy"),
    ("facetCellData", "tess_facetCellData.npy"),
)

_FACET_CHUNK_NAMES = (
    "facetData",
    "facetMaterial",
    "subtetVol",
    "facetVol1",
    "facetVol2",
    "particleMaterial",
)


def _load_tess(bundle):
    return {
        key: np.load(bundle / name, mmap_mode="r")
        for key, name in _TESS_ARRAYS
    }


def _write_rank_chunks(chunk_dir, rank, parts):
    for name, arr in zip(_FACET_CHUNK_NAMES, parts):
        np.save(chunk_dir / ("%s_%d.npy" % (name, rank)), np.asarray(arr))


def _assemble_rank_chunks(chunk_dir, size):
    assembled = []
    for name in _FACET_CHUNK_NAMES:
        views = [
            np.load(chunk_dir / ("%s_%d.npy" % (name, r)), mmap_mode="r")
            for r in range(size)
        ]
        nonempty = [view for view in views if view.shape[0] > 0]
        if not nonempty:
            assembled.append(np.zeros((0,) + views[0].shape[1:], dtype=views[0].dtype))
            continue
        total = sum(int(view.shape[0]) for view in nonempty)
        out = np.empty((total,) + nonempty[0].shape[1:], dtype=nonempty[0].dtype)
        cursor = 0
        for view in nonempty:
            count = int(view.shape[0])
            out[cursor:cursor + count] = view
            cursor += count
        assembled.append(out)
    return tuple(assembled)


def _publish_facet_chunks(bundle, rank, parts):
    comm = MPI.COMM_WORLD
    chunk_dir = Path(bundle) / "_mpi_facet_chunks"
    if rank == 0:
        if chunk_dir.is_dir():
            shutil.rmtree(chunk_dir)
        chunk_dir.mkdir()
    comm.Barrier()
    _write_rank_chunks(chunk_dir, rank, parts)
    comm.Barrier()
    return chunk_dir


def _assemble_published_chunks(chunk_dir, rank, size):
    if rank != 0:
        return None, None, None, None, None, None
    assembled = _assemble_rank_chunks(chunk_dir, size)
    shutil.rmtree(chunk_dir, ignore_errors=True)
    return assembled


def _chunk_ranges(n, size):
    base, rem = divmod(n, size)
    ranges = []
    start = 0
    for r in range(size):
        count = base + (1 if r < rem else 0)
        ranges.append((start, start + count))
        start += count
    return ranges


def _have_facet_npy(bundle):
    needed = [
        "facetData.npy",
        "facetMaterial.npy",
        "tess_allNodes.npy",
        "tess_allTets.npy",
        "tess_tetFacets.npy",
        "tess_facetCenters.npy",
        "tess_facetNormals.npy",
        "tess_tetn1.npy",
        "tess_tetn2.npy",
        "internalNodes.npy",
        "parDiameterList.npy",
        "materialList.npy",
        "surfaceNodes.npy",
        "surfaceFaces.npy",
    ]
    return all((bundle / n).is_file() for n in needed)


def run_mpi_facet_generation(
    allNodes,
    allTets,
    allEdges,
    tetFacets,
    facetCenters,
    facetAreas,
    facetNormals,
    tetn1,
    tetn2,
    materialList,
    particleID,
    facetCellData,
    bundle,
    elementType="LDPM",
    verbose=False,
):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    nTets = len(allTets)
    ranges = _chunk_ranges(nTets, size)
    i0, i1 = ranges[rank]
    myIdx = np.arange(i0, i1)

    if verbose:
        print("rank %d: tet %d/%d" % (rank, len(myIdx), nTets), flush=True)

    if len(myIdx) == 0:
        chunk_dir = _publish_facet_chunks(
            bundle,
            rank,
            (
                np.zeros((0, 19)),
                np.zeros(0),
                np.zeros(0),
                np.zeros(0),
                np.zeros(0),
                np.zeros((0, 2)),
            ),
        )
        gc.collect()
        return _assemble_published_chunks(chunk_dir, rank, size)

    myTets = allTets[myIdx]
    if tetFacets.ndim == 2 and tetFacets.shape[1] == 108:
        myTetFacets = tetFacets[myIdx]
    else:
        myTetFacets = tetFacets.reshape(nTets, 12, 9)[myIdx].reshape(-1, 9)

    myCenters = facetCenters.reshape(nTets, 12, 3)[myIdx].reshape(-1, 3)
    myAreas = facetAreas.reshape(nTets, 12)[myIdx].reshape(-1)
    myNormals = facetNormals.reshape(nTets, 12, 3)[myIdx].reshape(-1, 3)

    fcd = np.asarray(facetCellData)
    if fcd.size == 0:
        myCellData = np.zeros((len(myIdx) * 12, 3))
    elif fcd.ndim == 1 or (fcd.ndim == 2 and fcd.shape[0] == 12 * nTets):
        myCellData = fcd.reshape(12, nTets, -1)[:, myIdx, :].reshape(
            -1, fcd.shape[-1] if fcd.ndim == 2 else 1
        )
        if myCellData.ndim == 1:
            myCellData = myCellData.reshape(-1, 1)
    else:
        myCellData = fcd.reshape(nTets, 12, -1)[myIdx].reshape(-1, fcd.shape[-1])

    cementStructure = "Off"
    edgeMaterialList = 0
    materialRule = 0
    multiMaterial = "Off"

    if elementType == "LDPM":
        facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial = (
            gen_LDPM_facetData(
                allNodes,
                myTets,
                myTetFacets,
                myCenters,
                myAreas,
                myNormals,
                tetn1,
                tetn2,
                materialList,
                materialRule,
                multiMaterial,
                cementStructure,
                edgeMaterialList,
                myCellData,
                particleID,
            )
        )
    else:
        facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial = (
            gen_CSL_facetData(
                allNodes,
                allEdges,
                myTets,
                myTetFacets,
                myCenters,
                myAreas,
                myNormals,
                tetn1,
                tetn2,
                materialList,
                materialRule,
                multiMaterial,
                cementStructure,
                edgeMaterialList,
                myCellData,
                particleID,
            )
        )

    facetData = np.asarray(facetData, dtype=float)
    facetData[:, 0] += i0
    facetData[:, 1:4] += 36 * i0

    if verbose:
        print("rank %d: %d facets done" % (rank, len(facetData)), flush=True)

    chunk_dir = _publish_facet_chunks(
        bundle,
        rank,
        (facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial),
    )
    del allNodes, allTets, allEdges, tetFacets, facetCenters, facetAreas, facetNormals
    del tetn1, tetn2, materialList, particleID, facetCellData
    del myTets, myTetFacets, myCenters, myAreas, myNormals, myCellData
    del facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial
    gc.collect()
    return _assemble_published_chunks(chunk_dir, rank, size)


def _write_facet_outputs(
    bundle, facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial
):
    np.save(bundle / "facetData.npy", np.asarray(facetData, dtype=float))
    np.save(bundle / "facetMaterial.npy", np.asarray(facetMaterial, dtype=float))
    np.save(bundle / "subtetVol.npy", np.asarray(subtetVol, dtype=float))
    np.save(bundle / "facetVol1.npy", np.asarray(facetVol1, dtype=float))
    np.save(bundle / "facetVol2.npy", np.asarray(facetVol2, dtype=float))
    np.save(bundle / "particleMaterial.npy", np.asarray(particleMaterial, dtype=float))


def _need_fiber_facet(bundle, cfg):
    if not _toggle_on(cfg.get("fiberToggle", "Off")):
        return False
    if not _toggle_on(cfg.get("fiberIntersections", "Off")):
        return False
    return (bundle / "p1Fibers.npy").is_file() and (bundle / "p2Fibers.npy").is_file()


def _mpi_fiber_facet_from_bundle(bundle, cfg, verbose=False):
    """All ranks must call this. Results only meaningful on rank 0."""
    allNodes = np.load(bundle / "tess_allNodes.npy")
    allTets = np.load(bundle / "tess_allTets.npy")
    tetFacets = np.load(bundle / "tess_tetFacets.npy")
    facetCenters = np.load(bundle / "tess_facetCenters.npy")
    facetNormals = np.load(bundle / "tess_facetNormals.npy")
    tetn1 = np.load(bundle / "tess_tetn1.npy")
    tetn2 = np.load(bundle / "tess_tetn2.npy")
    p1Fibers = np.load(bundle / "p1Fibers.npy")
    p2Fibers = np.load(bundle / "p2Fibers.npy")
    orienFibers = (
        np.load(bundle / "orienFibers.npy")
        if (bundle / "orienFibers.npy").is_file()
        else np.zeros((len(p1Fibers), 3))
    )
    fiberLengths = (
        np.load(bundle / "fiberLengths.npy")
        if (bundle / "fiberLengths.npy").is_file()
        else np.zeros((len(p1Fibers), 1))
    )
    if verbose and MPI.COMM_WORLD.Get_rank() == 0:
        print("Fiber-facet intersections: %d fibers" % len(p1Fibers), flush=True)
    return run_mpi_fiber_facet_int(
        p1Fibers,
        p2Fibers,
        cfg["fiberDiameter"],
        fiberLengths,
        orienFibers,
        allTets,
        allNodes,
        tetFacets,
        tetn1,
        tetn2,
        facetNormals,
        facetCenters,
        verbose=verbose,
    )


def _write_reinforcement_outputs(bundle, cfg, tempPath, geoName):
    reinf = cfg.get("reinforcement")
    if not reinf:
        return None
    if not cfg.get("dataFilesGen", True) and not cfg.get("visFilesGen", True):
        return None
    reinf_cad = reinf.get("cad")
    if reinf_cad:
        reinf_cad = dict(reinf_cad)
        reinf_path = Path(reinf_cad.get("path") or "")
        if reinf_path.name and not reinf_path.is_file():
            reinf_cad["path"] = str(bundle / reinf_path.name)
    print("Writing reinforcement", flush=True)
    result = generate_reinforcement(
        geoName,
        tempPath,
        cfg["minC"],
        cfg["maxC"],
        grid=reinf.get("grid"),
        cad=reinf_cad,
        element_length=reinf.get("elementLength", 1.0),
        diameter=reinf.get("elementDiameter", 1.0),
        element_type=reinf.get("reinfElementType", "2DOF-T2D2/LINK1"),
        log=lambda message: print(message, flush=True),
    )
    if (
        cfg.get("visFilesGen", True)
        and result
        and result.get("nodes")
        and result.get("elements")
    ):
        mkVtk_LDPMCSL_reinforcement(
            geoName,
            tempPath,
            result["nodes"],
            result["elements"],
            diameter=result.get("diameter", 1.0),
        )
    return result


def _apply_random_field(facetData, cfg):
    rf_params = {
        "rfToggle": cfg.get("rfToggle", "Off"),
        "rfFieldDir": cfg.get("rfFieldDir", ""),
        "rfJobPlan": cfg.get("rfJobPlan") or {},
    }
    realization = resolve_rf_realization(rf_params, sample_id=1)
    if realization is None:
        return facetData
    print("Mapping random field to facets, realization %s." % realization, flush=True)
    try:
        return apply_rf_eole_to_facet_data(
            facetData,
            rf_params["rfFieldDir"],
            realization,
        )
    except Exception as exc:
        print("RF mapping failed: %s" % exc, flush=True)
        return facetData


def _flow_edges(bundle, cfg, allNodes, allTets):
    if not _toggle_on(cfg.get("htcToggle", "Off")):
        return None
    needed = (
        "tess_tetPoints.npy",
        "meshVertices.npy",
        "meshTets.npy",
        "coord1.npy",
        "coord2.npy",
        "coord3.npy",
        "coord4.npy",
    )
    if any(not (bundle / name).is_file() for name in needed):
        print("HTC flow edges skipped: mesh arrays are missing.", flush=True)
        return None
    print("Writing HTC flow edges", flush=True)
    return gen_LDPMCSL_flowEdges(
        cfg.get("htcLength", 0.0),
        allNodes,
        allTets,
        np.load(bundle / "tess_tetPoints.npy"),
        cfg.get("maxPar_sim", 0.0),
        np.load(bundle / "meshVertices.npy"),
        np.load(bundle / "meshTets.npy"),
        np.load(bundle / "coord1.npy"),
        np.load(bundle / "coord2.npy"),
        np.load(bundle / "coord3.npy"),
        np.load(bundle / "coord4.npy"),
        np.asarray(cfg["maxC"], dtype=float),
    )


def _write_orientation_path(bundle, cfg, tempPath, geoName):
    if str(cfg.get("geoType", "")) != "Sweep-3DP" or not cfg.get("hasPathSegments"):
        return
    segments = load_path_segments_json(str(bundle / "pathSegments_sweep3dp.json"))
    if not segments:
        return
    mkVtk_orientationPath(segments, geoName, tempPath)


def _write_model_outputs(bundle, cfg, verbose=False, fiber_results=None):
    geoName = cfg["geoName"]
    elementType = cfg["elementType"]
    tempPath = str(bundle) + os.sep

    allNodes = np.load(bundle / "tess_allNodes.npy")
    allTets = np.load(bundle / "tess_allTets.npy")
    tetFacets = np.load(bundle / "tess_tetFacets.npy")
    facetData = np.load(bundle / "facetData.npy")
    facetMaterial = np.load(bundle / "facetMaterial.npy")
    interlayer_params = cfg.get("interlayer") or {}
    if elementType == "LDPM" and interlayer_params.get("enabled"):
        print("Applying 3DCP interlayer mF tags.", flush=True)
        apply_3DCP_interlayer(
            facetData,
            facetMaterial,
            np.asarray(cfg["minC"], dtype=float),
            np.asarray(cfg["maxC"], dtype=float),
            interlayer_params,
        )
        np.save(bundle / "facetData.npy", facetData)
        np.save(bundle / "facetMaterial.npy", facetMaterial)

    facetData = _apply_random_field(facetData, cfg)
    np.save(bundle / "facetData.npy", facetData)

    internalNodes = np.load(bundle / "internalNodes.npy")
    parDiameterList = np.load(bundle / "parDiameterList.npy")
    materialList = np.load(bundle / "materialList.npy")
    surfaceNodes = np.load(bundle / "surfaceNodes.npy")
    surfaceFaces = np.load(bundle / "surfaceFaces.npy")

    allEdges = None
    edge_path = bundle / "tess_allEdges.npy"
    if edge_path.is_file():
        allEdges = np.load(edge_path)

    FiberdataList = None
    TotalIntersections = None
    MaxInterPerFacet = None
    IntersectedFiber = None
    projectedFacet = None

    p1Fibers = np.zeros((0, 3))
    p2Fibers = np.zeros((0, 3))
    orienFibers = np.zeros((0, 3))
    fiberLengths = np.zeros((0, 1))
    if (bundle / "p1Fibers.npy").is_file() and (bundle / "p2Fibers.npy").is_file():
        p1Fibers = np.load(bundle / "p1Fibers.npy")
        p2Fibers = np.load(bundle / "p2Fibers.npy")
        if (bundle / "orienFibers.npy").is_file():
            orienFibers = np.load(bundle / "orienFibers.npy")
        if (bundle / "fiberLengths.npy").is_file():
            fiberLengths = np.load(bundle / "fiberLengths.npy")

    if fiber_results is not None:
        (
            FiberdataList,
            TotalIntersections,
            MaxInterPerFacet,
            _TotalTet,
            _TotalFiber,
            IntersectedFiber,
            projectedFacet,
        ) = fiber_results

    allDiameters = np.concatenate(
        (
            np.array([0.0] * int(len(allNodes) - len(parDiameterList))),
            parDiameterList,
        )
    )

    if cfg.get("dataFilesGen", True):
        if verbose:
            print("Writing data files", flush=True)
        mkData_nodes(geoName, tempPath, allNodes)
        mkData_LDPMCSL_tets(geoName, tempPath, allTets)
        if elementType == "CSL" and allEdges is not None:
            mkData_LDPMCSL_edges(geoName, tempPath, allEdges)
        mkData_LDPMCSL_facets(geoName, tempPath, facetData)
        mkData_LDPMCSL_facetsVertices(geoName, tempPath, tetFacets)
        mkData_LDPMCSL_faceFacets(geoName, tempPath, surfaceNodes, surfaceFaces)
        if FiberdataList is not None:
            mkData_LDPMCSL_facetfiberInt(
                geoName, FiberdataList, TotalIntersections, MaxInterPerFacet, tempPath
            )
        mkData_particles(allNodes, allDiameters, geoName, tempPath)

    edgeData = _flow_edges(bundle, cfg, allNodes, allTets)
    if edgeData is not None and cfg.get("dataFilesGen", True):
        mkData_LDPMCSL_flowEdges(geoName, edgeData, tempPath)

    if cfg.get("visFilesGen", True):
        if verbose:
            print("Writing visualization files", flush=True)
        n_int = len(internalNodes)
        materialList = np.asarray(materialList).reshape(-1)
        parDiameterList = np.asarray(parDiameterList).reshape(-1)
        if len(materialList) == n_int:
            mat_tail = materialList
        elif len(materialList) == len(allNodes):
            mat_tail = materialList[(len(allNodes) - n_int) : len(allNodes)]
        elif len(materialList) > n_int:
            mat_tail = materialList[-n_int:]
        else:
            mat_tail = np.ones(n_int)
        if len(parDiameterList) != n_int:
            if len(parDiameterList) > n_int:
                parDiameterList = parDiameterList[-n_int:]
            else:
                pad = np.zeros(n_int)
                pad[: len(parDiameterList)] = parDiameterList
                parDiameterList = pad
        mkVtk_particles(
            internalNodes,
            parDiameterList,
            mat_tail,
            geoName,
            tempPath,
        )
        mkVtk_LDPMCSL_facets(geoName, tempPath, tetFacets, facetMaterial, facetData)
        if _toggle_on(cfg.get("fiberToggle", "Off")) and len(p1Fibers) > 0:
            mkVtk_LDPMCSL_fibers(
                p1Fibers,
                p2Fibers,
                cfg["fiberDiameter"],
                fiberLengths,
                orienFibers,
                geoName,
                tempPath,
            )
            if projectedFacet is not None:
                mkVtk_LDPMCSL_projFacets(geoName, projectedFacet, tempPath)
        if IntersectedFiber is not None:
            mkVtk_LDPMCSL_nonIntFibers(
                p1Fibers,
                p2Fibers,
                cfg["fiberDiameter"],
                fiberLengths,
                orienFibers,
                geoName,
                IntersectedFiber,
                tempPath,
            )
        if edgeData is not None:
            mkVtk_LDPMCSL_flowEdges(geoName, edgeData, tempPath)
            mkIges_LDPMCSL_flowEdges(geoName, edgeData, tempPath)
        _write_orientation_path(bundle, cfg, tempPath, geoName)

    _write_reinforcement_outputs(bundle, cfg, tempPath, geoName)

    try:
        os.rename(
            Path(tempPath + geoName + "-para-mesh.vtk"),
            Path(tempPath + geoName + "-para-mesh.000.vtk"),
        )
    except Exception:
        pass

    for fname in [geoName + "2D.mesh", geoName + ".node", geoName + ".ele", geoName + ".edge"]:
        try:
            os.remove(Path(tempPath + fname))
        except Exception:
            pass

    print("Wrote data and visualization files", flush=True)


def run_from_bundle(bundle_dir, force_rebuild=False):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    bundle = Path(bundle_dir).resolve()
    manifest_path = bundle / "external_manifest_ldpmcsl.json"

    if (not force_rebuild) and _have_facet_npy(bundle):
        cfg = None
        verbose = False
        if rank == 0:
            with open(manifest_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            verbose = True
            print("Using saved facet files", flush=True)
        cfg = comm.bcast(cfg, root=0)
        verbose = comm.bcast(verbose, root=0)
        fiber_results = None
        if _need_fiber_facet(bundle, cfg):
            fiber_results = _mpi_fiber_facet_from_bundle(bundle, cfg, verbose=verbose)
        if rank == 0:
            _write_model_outputs(
                bundle, cfg, verbose=verbose, fiber_results=fiber_results
            )
        return None, None, None, None, None, None

    meta = None
    err = None
    if rank == 0:
        try:
            if not manifest_path.is_file():
                raise FileNotFoundError("Missing manifest: %s" % manifest_path)
            with open(manifest_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            verbose = True
            geoName = cfg["geoName"]
            elementType = cfg["elementType"]
            tempPath = str(bundle) + os.sep

            for name in (
                "internalNodes.npy",
                "parDiameterList.npy",
                "materialList.npy",
                "particleID.npy",
                "surfaceNodes.npy",
                "surfaceFaces.npy",
            ):
                if not (bundle / name).is_file():
                    raise FileNotFoundError("Missing %s — run MPI particles first." % name)

            internalNodes = np.load(bundle / "internalNodes.npy")
            parDiameterList = np.load(bundle / "parDiameterList.npy")
            materialList = np.load(bundle / "materialList.npy")
            particleID = np.load(bundle / "particleID.npy")
            surfaceNodes = np.load(bundle / "surfaceNodes.npy")
            surfaceFaces = np.load(bundle / "surfaceFaces.npy")

            if verbose:
                print("Forming tetrahedralization", flush=True)
            gen_LDPMCSL_tetrahedralization(
                internalNodes, surfaceNodes, surfaceFaces, geoName, tempPath
            )
            allNodes, allTets, allEdges = read_LDPMCSL_tetgen(
                Path(tempPath + geoName + ".node"),
                Path(tempPath + geoName + ".ele"),
                Path(tempPath + geoName + ".edge"),
            )

            if verbose:
                print("Forming tesselation", flush=True)
            (
                tetFacets,
                facetCenters,
                facetAreas,
                facetNormals,
                tetn1,
                tetn2,
                tetPoints,
                allDiameters,
                facetPointData,
                facetCellData,
            ) = gen_LDPMCSL_tesselation(
                allNodes, allTets, parDiameterList, cfg["minPar_sim"], geoName
            )

            n_nodes = len(allNodes)
            if len(particleID) < n_nodes:
                particleID = np.concatenate(
                    (np.zeros(n_nodes - len(particleID)), particleID)
                )
            if len(materialList) < n_nodes:
                materialList = np.concatenate(
                    (np.zeros(n_nodes - len(materialList)), materialList)
                )

            np.save(bundle / "tess_allNodes.npy", allNodes)
            np.save(bundle / "tess_allTets.npy", allTets)
            np.save(bundle / "tess_allEdges.npy", allEdges)
            np.save(bundle / "tess_tetFacets.npy", tetFacets)
            np.save(bundle / "tess_facetCenters.npy", facetCenters)
            np.save(bundle / "tess_facetAreas.npy", facetAreas)
            np.save(bundle / "tess_facetNormals.npy", facetNormals)
            np.save(bundle / "tess_facetCellData.npy", facetCellData)
            np.save(bundle / "tess_tetn1.npy", np.asarray(tetn1))
            np.save(bundle / "tess_tetn2.npy", np.asarray(tetn2))
            np.save(bundle / "tess_tetPoints.npy", np.asarray(tetPoints))
            np.save(bundle / "tess_materialList.npy", np.asarray(materialList))
            np.save(bundle / "tess_particleID.npy", np.asarray(particleID))

            meta = dict(cfg=cfg, verbose=verbose, elementType=elementType, nTets=len(allTets))
            if verbose:
                print("Generating facets: %d tets, %d ranks" % (len(allTets), comm.Get_size()), flush=True)
        except Exception as exc:
            err = "%s: %s" % (type(exc).__name__, exc)

    err = comm.bcast(err, root=0)
    if err:
        raise RuntimeError(err)

    if rank == 0:
        del allNodes, allTets, allEdges, tetFacets, facetCenters, facetAreas, facetNormals
        del tetn1, tetn2, tetPoints, allDiameters, facetPointData, facetCellData
        del materialList, particleID, internalNodes, parDiameterList, surfaceNodes, surfaceFaces
        gc.collect()
    meta = comm.bcast(meta, root=0)
    comm.Barrier()
    if rank == 0 and meta["verbose"]:
        print("Reading tesselation", flush=True)
    tess = _load_tess(bundle)

    facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial = (
        run_mpi_facet_generation(
            tess.pop("allNodes"),
            tess.pop("allTets"),
            tess.pop("allEdges"),
            tess.pop("tetFacets"),
            tess.pop("facetCenters"),
            tess.pop("facetAreas"),
            tess.pop("facetNormals"),
            tess.pop("tetn1"),
            tess.pop("tetn2"),
            tess.pop("materialList"),
            tess.pop("particleID"),
            tess.pop("facetCellData"),
            bundle,
            elementType=meta["elementType"],
            verbose=meta["verbose"],
        )
    )
    del tess
    gc.collect()

    if rank == 0:
        _write_facet_outputs(
            bundle,
            facetData,
            facetMaterial,
            subtetVol,
            facetVol1,
            facetVol2,
            particleMaterial,
        )
        print("Wrote %d facets" % len(facetData))

    comm.Barrier()
    fiber_results = None
    if _need_fiber_facet(bundle, meta["cfg"]):
        fiber_results = _mpi_fiber_facet_from_bundle(
            bundle, meta["cfg"], verbose=meta["verbose"]
        )

    if rank == 0:
        _write_model_outputs(
            bundle,
            meta["cfg"],
            verbose=meta["verbose"],
            fiber_results=fiber_results,
        )

    return facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial


if __name__ == "__main__":
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    force = "--force" in sys.argv
    bundle = _resolve_bundle_dir(sys.argv)
    try:
        run_from_bundle(bundle, force_rebuild=force)
    except Exception:
        if rank == 0:
            raise
        raise
