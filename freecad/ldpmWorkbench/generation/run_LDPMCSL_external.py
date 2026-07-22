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
## Description coming soon...
##
## ===========================================================================


import json
import math
import os
import time
from pathlib import Path

import numpy as np

from freecad.ldpmWorkbench.generation.gen_3DCP_interlayer import apply_3DCP_interlayer
from freecad.ldpmWorkbench.generation.gen_CSL_facetData import gen_CSL_facetData
from freecad.ldpmWorkbench.generation.gen_LDPM_facetData import gen_LDPM_facetData
from freecad.ldpmWorkbench.random_field_generation.driver_RF import (apply_rf_eole_to_facet_data, resolve_rf_realization)
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_facetfiberInt import gen_LDPMCSL_facetfiberInt
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_fibers import gen_LDPMCSL_fibers
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_flowEdges import gen_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_multiStep import gen_LDPMCSL_multiStep
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_orientationPath import (load_path_segments_json)
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tesselation import gen_LDPMCSL_tesselation
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tetrahedralization import gen_LDPMCSL_tetrahedralization

from freecad.ldpmWorkbench.input.read_ctScan_file import read_ctScan_file
from freecad.ldpmWorkbench.input.read_LDPMCSL_tetgen import read_LDPMCSL_tetgen

from freecad.ldpmWorkbench.output.mkData_LDPMCSL_edges import mkData_LDPMCSL_edges
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_faceFacets import mkData_LDPMCSL_faceFacets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetfiberInt import mkData_LDPMCSL_facetfiberInt
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facets import mkData_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetsVertices import mkData_LDPMCSL_facetsVertices
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_flowEdges import mkData_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_tets import mkData_LDPMCSL_tets
from freecad.ldpmWorkbench.output.mkData_nodes import mkData_nodes
from freecad.ldpmWorkbench.output.mkData_particles import mkData_particles
from freecad.ldpmWorkbench.output.mkIges_LDPMCSL_flowEdges import mkIges_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkPy_LDPM_singleParaview import mkPy_LDPM_singleParaview
from freecad.ldpmWorkbench.output.mkPy_LDPM_singleParaviewLabels import mkPy_LDPM_singleParaviewLabels
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleCell import mkVtk_LDPM_singleCell
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleEdge import mkVtk_LDPM_singleEdge
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleEdgeFacets import mkVtk_LDPM_singleEdgeFacets
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleEdgeParticles import mkVtk_LDPM_singleEdgeParticles
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTet import mkVtk_LDPM_singleTet
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTetFacets import mkVtk_LDPM_singleTetFacets
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTetParticles import mkVtk_LDPM_singleTetParticles
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_facets import mkVtk_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_fibers import mkVtk_LDPMCSL_fibers
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_flowEdges import mkVtk_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_nonIntFibers import mkVtk_LDPMCSL_nonIntFibers
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_projFacets import mkVtk_LDPMCSL_projFacets
from freecad.ldpmWorkbench.output.mkVtk_orientationPath import mkVtk_orientationPath
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_externalMesh import mesh_geometry_with_gmsh
from freecad.ldpmWorkbench.output.mkVtk_particles import mkVtk_particles


def _toggle_on(value):
    return str(value).strip().lower() in ["on", "y", "yes", "true", "1"]


def _verbose_on(value):
    return _toggle_on(value)


def _external_log(message, verbose_on=False):
    print(message, flush=True)


def _temp_path(bundle_dir):
    bundle = str(bundle_dir).replace("\\", "/")
    if not bundle.endswith("/"):
        bundle = bundle + "/"
    return bundle


def run_external_bundle(bundle_dir):

    bundle_dir = Path(bundle_dir).resolve()
    manifest_path = bundle_dir / "external_manifest_ldpmcsl.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    tempPath = _temp_path(bundle_dir)
    geoName = cfg["geoName"]
    elementType = cfg["elementType"]
    verbose_on = _verbose_on(cfg.get("verbose", "On"))

    if _toggle_on(cfg.get("multiMatToggle", "Off")):
        raise RuntimeError(
            "External generation does not support PLDPM multimaterial. "
            "Use in-GUI generation for PLDPM, or turn multimaterial Off."
        )

    start_time = time.time()

    needs_mesh = bool(cfg.get("needsExternalMesh", False)) or not Path(tempPath + "meshVertices.npy").is_file()
    if needs_mesh:
        _external_log("External: creating volume mesh with Gmsh...", verbose_on)
        mesh_info = mesh_geometry_with_gmsh(
            bundle_dir,
            cfg.get("gmshBin"),
            cfg.get("geometryBrep") or (geoName + "_geometry.brep"),
            cfg["minPar_sim"],
            geo_name=geoName,
        )
        cfg["tetVolume"] = mesh_info["tetVolume"]
        cfg["maxEdgeLength"] = mesh_info["maxEdgeLength"]
        cfg["max_dist"] = mesh_info["max_dist"]
        cfg["minC"] = mesh_info["minC"]
        cfg["maxC"] = mesh_info["maxC"]
        cfg["needsExternalMesh"] = False
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        meshVertices = mesh_info["meshVertices"]
        meshTets = mesh_info["meshTets"]
        surfaceNodes = mesh_info["surfaceNodes"]
        surfaceFaces = mesh_info["surfaceFaces"]
        coord1 = mesh_info["coord1"]
        coord2 = mesh_info["coord2"]
        coord3 = mesh_info["coord3"]
        coord4 = mesh_info["coord4"]
    else:
        meshVertices = np.load(tempPath + "meshVertices.npy")
        meshTets = np.load(tempPath + "meshTets.npy")
        surfaceNodes = np.load(tempPath + "surfaceNodes.npy")
        surfaceFaces = np.load(tempPath + "surfaceFaces.npy")
        coord1 = np.load(tempPath + "coord1.npy")
        coord2 = np.load(tempPath + "coord2.npy")
        coord3 = np.load(tempPath + "coord3.npy")
        coord4 = np.load(tempPath + "coord4.npy")

    resume = os.environ.get("CHRONO_EXTERNAL_RESUME", "").strip() in ("1", "true", "True", "yes", "on")
    have_particles = Path(tempPath + "internalNodes.npy").is_file() and Path(tempPath + "parDiameterList.npy").is_file()
    if resume and have_particles:
        _external_log("External: resuming — skipping particle placement (using existing *.npy).", verbose_on)
    else:
        gen_LDPMCSL_multiStep(
            tempPath,
            cfg["numCPU"],
            cfg["numIncrements"],
            cfg["maxIter"],
            cfg["parOffset"],
            cfg["maxEdgeLength"],
            cfg["max_dist"],
            cfg["minPar_sim"],
            cfg["maxPar_sim"],
            cfg["minPar_exp"],
            cfg["maxPar_exp"],
            cfg["sieveCurveDiameter"],
            cfg["sieveCurvePassing"],
            cfg["wcRatio"],
            cfg["cementC"],
            cfg["airFrac"],
            cfg["fullerCoef"],
            cfg["flyashC"],
            cfg["silicaC"],
            cfg["scmC"],
            cfg["fillerC"],
            cfg["flyashDensity"],
            cfg["silicaDensity"],
            cfg["scmDensity"],
            cfg["fillerDensity"],
            cfg["cementDensity"],
            cfg["densityWater"],
            "Off",
            "",
            "",
            cfg.get("grainAggMin", 0.0),
            cfg.get("grainAggMax", 0.0),
            cfg.get("grainAggFuller", 0.0),
            cfg.get("grainAggSieveD", ""),
            cfg.get("grainAggSieveP", ""),
            cfg.get("grainBinderMin", 0.0),
            cfg.get("grainBinderMax", 0.0),
            cfg.get("grainBinderFuller", 0.0),
            cfg.get("grainBinderSieveD", ""),
            cfg.get("grainBinderSieveP", ""),
            cfg.get("grainITZMin", 0.0),
            cfg.get("grainITZMax", 0.0),
            cfg.get("grainITZFuller", 0.0),
            cfg.get("grainITZSieveD", ""),
            cfg.get("grainITZSieveP", ""),
            cfg["tetVolume"],
            cfg["minC"],
            cfg["maxC"],
            cfg["verbose"],
            cfg["fiberToggle"],
            cfg["fiberFile"],
            cfg["fiberDiameter"],
            cfg["fiberLength"],
            cfg["fiberVol"],
            cfg["fiberOrientation1"],
            cfg["fiberOrientation2"],
            cfg["fiberOrientation3"],
            cfg["fiberPref"],
            cfg["fiberCutting"],
            cfg["fiberIntersections"],
            cfg.get("fiberOutputFiles", "Off"),
            surfaceFaces,
        )

    pathSegments = None
    if cfg.get("hasPathSegments"):
        pathSegments = load_path_segments_json(tempPath + "pathSegments_sweep3dp.json")

    if not _toggle_on(cfg.get("fiberOutputFiles", "Off")):
        for _fn in ("p1Fibers.npy", "p2Fibers.npy", "orienFibers.npy", "fiberLengths.npy", "fiberDiameter.npy", "nFiber.npy"):
            try:
                os.remove(tempPath + _fn)
            except OSError:
                pass

    internalNodes = np.load(tempPath + "internalNodes.npy")
    materialList = np.load(tempPath + "materialList.npy")
    parDiameterList = np.load(tempPath + "parDiameterList.npy")
    particleID = np.load(tempPath + "particleID.npy")
    n_placed = len(internalNodes)
    if len(particleID) > n_placed:
        particleID = particleID[:n_placed]
        np.save(tempPath + "particleID.npy", particleID)
    if len(parDiameterList) > n_placed:
        parDiameterList = parDiameterList[:n_placed]
        np.save(tempPath + "parDiameterList.npy", parDiameterList)
    if len(materialList) > n_placed:
        materialList = materialList[:n_placed]
        np.save(tempPath + "materialList.npy", materialList)

    if _toggle_on(cfg["fiberToggle"]):
        if cfg["fiberFile"] not in [0, None, [], ""] and Path(str(cfg["fiberFile"])).is_file():
            CTScanFiberData = read_ctScan_file(cfg["fiberFile"])
            CTScanFiberData = np.array(CTScanFiberData).reshape(-1, 10)
            p1Fibers = CTScanFiberData[:, 0:3]
            p2Fibers = CTScanFiberData[:, 3:6]
            orienFibers = CTScanFiberData[:, 6:9]
            fiberLengths = CTScanFiberData[:, 9:10]
        else:
            nFiber = int(
                round(
                    4
                    * cfg["tetVolume"]
                    * cfg["fiberVol"]
                    / (math.pi * cfg["fiberDiameter"] ** 2 * cfg["fiberLength"])
                )
            )
            maxC = np.asarray(cfg["maxC"])
            p1Fibers = (np.zeros((nFiber, 3)) + 2) * maxC
            p2Fibers = (np.zeros((nFiber, 3)) + 2) * maxC
            orienFibers = (np.zeros((nFiber, 3)) + 2) * maxC
            fiberLengths = np.zeros((nFiber, 1))

            if not verbose_on and nFiber > 0:
                _external_log(f"External: generating {nFiber} fibers.", verbose_on)

            for x in range(0, nFiber):
                if verbose_on and x % 100 == 0:
                    print(str(nFiber - x) + " fibers remaining")

                p1Fiber, p2Fiber, orienFiber, lFiber = gen_LDPMCSL_fibers(
                    meshVertices,
                    meshTets,
                    coord1,
                    coord2,
                    coord3,
                    coord4,
                    cfg["maxIter"],
                    cfg["fiberLength"],
                    np.array(cfg["maxC"]),
                    cfg["maxPar_sim"],
                    np.array(
                        [
                            cfg["fiberOrientation1"],
                            cfg["fiberOrientation2"],
                            cfg["fiberOrientation3"],
                        ]
                    ),
                    cfg["fiberPref"],
                    surfaceFaces,
                    cfg["fiberCutting"],
                    pathSegments,
                )
                p1Fibers[x, :] = p1Fiber
                p2Fibers[x, :] = p2Fiber
                orienFibers[x, :] = orienFiber
                fiberLengths[x, :] = lFiber

            orienFibers[np.abs(orienFibers) < 1e-10] = 0.0
            for i in range(len(orienFibers)):
                norm = np.linalg.norm(orienFibers[i])
                if norm > 0:
                    orienFibers[i] = orienFibers[i] / norm
    else:
        p1Fibers = np.zeros((0, 3))
        p2Fibers = np.zeros((0, 3))
        orienFibers = np.zeros((0, 3))
        fiberLengths = np.zeros((0, 1))

    if not verbose_on:
        _external_log("External: finishing model (tetra, facets, output)...", verbose_on)
    elif verbose_on:
        print("Forming tetrahedralization.")
    gen_LDPMCSL_tetrahedralization(internalNodes, surfaceNodes, surfaceFaces, geoName, tempPath)
    allNodes, allTets, allEdges = read_LDPMCSL_tetgen(
        Path(tempPath + geoName + ".node"),
        Path(tempPath + geoName + ".ele"),
        Path(tempPath + geoName + ".edge"),
    )

    if verbose_on:
        print("Forming tesselation.")
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
    ) = gen_LDPMCSL_tesselation(allNodes, allTets, parDiameterList, cfg["minPar_sim"], geoName)

    if _toggle_on(cfg["htcToggle"]):
        edgeData = gen_LDPMCSL_flowEdges(
            cfg["htcLength"],
            allNodes,
            allTets,
            tetPoints,
            cfg["maxPar_sim"],
            meshVertices,
            meshTets,
            coord1,
            coord2,
            coord3,
            coord4,
            np.array(cfg["maxC"]),
        )
    else:
        edgeData = 0

    edgeMaterialList = 0
    cementStructure = "Off"

    particleID = np.concatenate((0 * np.ones([len(allNodes) - len(particleID),]), particleID))
    materialList = np.concatenate((0 * np.ones([len(allNodes) - len(materialList),]), materialList))

    if verbose_on:
        print("Generating facet data.")
    if elementType == "LDPM":
        facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial = gen_LDPM_facetData(
            allNodes,
            allTets,
            tetFacets,
            facetCenters,
            facetAreas,
            facetNormals,
            tetn1,
            tetn2,
            materialList,
            0,
            "Off",
            cementStructure,
            edgeMaterialList,
            facetCellData,
            particleID,
        )
    else:
        facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial = gen_CSL_facetData(
            allNodes,
            allEdges,
            allTets,
            tetFacets,
            facetCenters,
            facetAreas,
            facetNormals,
            tetn1,
            tetn2,
            materialList,
            0,
            "Off",
            cementStructure,
            edgeMaterialList,
            facetCellData,
            particleID,
        )

    FiberdataList = None
    TotalIntersections = None
    MaxInterPerFacet = None
    IntersectedFiber = None
    projectedFacet = None
    if _toggle_on(cfg["fiberToggle"]) and _toggle_on(cfg["fiberIntersections"]):
        (
            FiberdataList,
            TotalIntersections,
            MaxInterPerFacet,
            TotalTet,
            TotalFiber,
            IntersectedFiber,
            projectedFacet,
        ) = gen_LDPMCSL_facetfiberInt(
            p1Fibers,
            p2Fibers,
            cfg["fiberDiameter"],
            fiberLengths,
            orienFibers,
            geoName,
            allTets,
            allNodes,
            tetFacets,
            facetData,
            tetn1,
            tetn2,
            facetNormals,
            facetCenters,
        )

    interlayer_params = cfg.get("interlayer", {})
    if elementType == "LDPM" and interlayer_params.get("enabled"):
        if verbose_on:
            print("Applying 3DCP interlayer mF tags.")
        apply_3DCP_interlayer(
            facetData,
            facetMaterial,
            np.array(cfg["minC"]),
            np.array(cfg["maxC"]),
            interlayer_params,
        )

    rf_params = {
        "rfToggle": cfg.get("rfToggle", "Off"),
        "rfFieldDir": cfg.get("rfFieldDir", ""),
        "rfJobPlan": cfg.get("rfJobPlan", {}),
    }
    rf_realization = resolve_rf_realization(rf_params, sample_id=1)
    if rf_realization is not None:
        if verbose_on:
            print(f"Mapping random field to facets (EOLE), realization {rf_realization}.")
        try:
            facetData = apply_rf_eole_to_facet_data(
                facetData,
                rf_params["rfFieldDir"],
                rf_realization,
            )
        except Exception as e:
            print(f"RF mapping failed: {e}")

    allDiameters = np.concatenate((np.array([0.0] * int(len(allNodes) - len(parDiameterList))), parDiameterList))

    if cfg["dataFilesGen"]:
        if verbose_on:
            print("Writing data files.")
        mkData_nodes(geoName, tempPath, allNodes)
        mkData_LDPMCSL_tets(geoName, tempPath, allTets)
        if elementType == "CSL":
            mkData_LDPMCSL_edges(geoName, tempPath, allEdges)
        mkData_LDPMCSL_facets(geoName, tempPath, facetData)
        mkData_LDPMCSL_facetsVertices(geoName, tempPath, tetFacets)
        mkData_LDPMCSL_faceFacets(geoName, tempPath, surfaceNodes, surfaceFaces)
        if FiberdataList is not None:
            mkData_LDPMCSL_facetfiberInt(geoName, FiberdataList, TotalIntersections, MaxInterPerFacet, tempPath)
        mkData_particles(allNodes, allDiameters, geoName, tempPath)
        if _toggle_on(cfg["htcToggle"]):
            mkData_LDPMCSL_flowEdges(geoName, edgeData, tempPath)

    if cfg["visFilesGen"]:
        if verbose_on:
            print("Writing visualization files.")
        mkVtk_particles(
            internalNodes,
            parDiameterList,
            materialList[(len(allNodes) - len(internalNodes)) : len(allNodes)],
            geoName,
            tempPath,
        )
        mkVtk_LDPMCSL_facets(geoName, tempPath, tetFacets, facetMaterial, facetData)
        if _toggle_on(cfg["htcToggle"]):
            mkVtk_LDPMCSL_flowEdges(geoName, edgeData, tempPath)
            mkIges_LDPMCSL_flowEdges(geoName, edgeData, tempPath)
        if _toggle_on(cfg["fiberToggle"]):
            mkVtk_LDPMCSL_fibers(
                p1Fibers,
                p2Fibers,
                cfg["fiberDiameter"],
                fiberLengths,
                orienFibers,
                geoName,
                tempPath,
            )
            if pathSegments is not None and len(pathSegments) > 0:
                mkVtk_orientationPath(pathSegments, geoName, tempPath)
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

    if cfg["singleTetGen"]:
        if elementType == "LDPM":
            mkVtk_LDPM_singleTetFacets(geoName, tempPath, tetFacets)
            mkVtk_LDPM_singleTetParticles(allNodes, allTets, allDiameters, geoName, tempPath)
            mkVtk_LDPM_singleTet(allNodes, allTets, geoName, tempPath)
            mkVtk_LDPM_singleCell(allNodes, allTets, parDiameterList, tetFacets, geoName, tempPath)
            mkPy_LDPM_singleParaview(geoName, cfg["outDir"], cfg["outName"], tempPath)
            mkPy_LDPM_singleParaviewLabels(geoName, tempPath)
        elif elementType == "CSL":
            mkVtk_LDPM_singleEdgeFacets(geoName, tempPath, allEdges, facetData, tetFacets)
            mkVtk_LDPM_singleEdgeParticles(allNodes, allEdges, allDiameters, geoName, tempPath)
            mkVtk_LDPM_singleEdge(allNodes, allEdges, geoName, tempPath)

    try:
        os.rename(Path(tempPath + geoName + "-para-mesh.vtk"), Path(tempPath + geoName + "-para-mesh.000.vtk"))
    except Exception:
        pass

    for fname in [geoName + "2D.mesh", geoName + ".node", geoName + ".ele", geoName + ".edge"]:
        try:
            os.remove(Path(tempPath + fname))
        except Exception:
            pass

    if not _toggle_on(cfg.get("fiberOutputFiles", "Off")):
        for _fn in ("p1Fibers.npy", "p2Fibers.npy", "orienFibers.npy", "fiberLengths.npy", "fiberDiameter.npy", "nFiber.npy"):
            try:
                os.remove(tempPath + _fn)
            except OSError:
                pass

    total_time = round(time.time() - start_time, 2)
    _external_log(f"External generation complete ({total_time} s): {bundle_dir}", verbose_on)
