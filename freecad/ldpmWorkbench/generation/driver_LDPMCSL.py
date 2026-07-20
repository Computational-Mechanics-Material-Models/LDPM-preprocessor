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
## Description coming soon....
##
##
## ===========================================================================

import os
import sys
import re
import shutil
import time
import tempfile
import numpy as np
from pathlib import Path
import functools
import math
import ast
import json
import platform

import multiprocessing
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import threading

if platform.system() != 'Windows':
    try:
        multiprocessing.set_start_method('fork', force=True)
    except:
        pass
    USE_PROCESSES = True
else:
    USE_PROCESSES = False

# Importing: FreeCAD
import FreeCADGui as Gui
import FreeCAD as App
import Part
import Part,PartGui
import Mesh
import MeshPartGui, FreeCADGui
import MeshPart
import Mesh, Part, PartGui
import MaterialEditor
import ObjectsFem
import FemGui
import Fem
import femmesh.femmesh2mesh

try:  # FreeCAD 1.0 provides a PySide shim
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # FreeCAD 0.20 ships PySide2
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ImportError:  # Fall back for very old FreeCAD versions
        from PySide import QtCore, QtGui  # type: ignore
        QtWidgets = QtGui  # type: ignore


# Importing: generation
from freecad.ldpmWorkbench.generation.calc_LDPMCSL_meshVolume           import calc_LDPMCSL_meshVolume
from freecad.ldpmWorkbench.generation.calc_parVolume                    import calc_parVolume
from freecad.ldpmWorkbench.generation.calc_sieveCurve                   import calc_sieveCurve
from freecad.ldpmWorkbench.generation.calc_LDPMCSL_surfMeshSize         import calc_LDPMCSL_surfMeshSize
from freecad.ldpmWorkbench.generation.calc_LDPMCSL_surfMeshExtents      import calc_LDPMCSL_surfMeshExtents
from freecad.ldpmWorkbench.generation.check_particleOverlapMPI          import check_particleOverlapMPI
from freecad.ldpmWorkbench.generation.check_multiMat_size               import check_multiMat_size
from freecad.ldpmWorkbench.generation.check_multiMat_matVol             import check_multiMat_matVol
from freecad.ldpmWorkbench.generation.gen_CSL_facetData                 import gen_CSL_facetData
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tesselation           import gen_LDPMCSL_tesselation
from freecad.ldpmWorkbench.generation.gen_LDPM_facetData                import gen_LDPM_facetData
from freecad.ldpmWorkbench.random_field_generation.driver_RF            import (
    apply_rf_eole_to_facet_data,
    resolve_rf_realization,
)
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_analysis              import gen_LDPMCSL_analysis
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_facetfiberInt         import gen_LDPMCSL_facetfiberInt
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_fibers                import gen_LDPMCSL_fibers
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_orientationPath       import build_sweep3dp_path_segments, save_path_segments_json
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_flowEdges             import gen_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry              import gen_LDPMCSL_geometry
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_initialMesh           import gen_LDPMCSL_initialMesh
from freecad.ldpmWorkbench.generation.gen_particle                      import gen_particle
from freecad.ldpmWorkbench.generation.gen_particleMPI                   import gen_particleMPI
from freecad.ldpmWorkbench.generation.gen_particleList                  import gen_particleList
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_multiStep             import gen_multiMat_phase_particle_list, _phase_list_val
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_properties            import gen_LDPMCSL_properties
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_subParticle           import gen_LDPMCSL_subParticle
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tetrahedralization    import gen_LDPMCSL_tetrahedralization
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_periodicMesh          import gen_LDPMCSL_periodicMesh
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_externalMesh          import (
    export_shape_brep,
    freecad_gmsh_binary,
)
from freecad.ldpmWorkbench.generation.run_LDPMCSL_external              import run_external_bundle
from freecad.ldpmWorkbench.generation.gen_multiMat_refine               import gen_multiMat_refine
from freecad.ldpmWorkbench.generation.gen_multiMat_reform               import gen_multiMat_reform
from freecad.ldpmWorkbench.generation.gen_multiMat_assign               import gen_multiMat_assign
from freecad.ldpmWorkbench.generation.gen_3DCP_interlayer                import apply_3DCP_interlayer
from freecad.ldpmWorkbench.generation.sort_multiMat_voxels              import sort_multiMat_voxels
from freecad.ldpmWorkbench.generation.sort_multiMat_mat                 import sort_multiMat_mat

# Importing: input
from freecad.ldpmWorkbench.input.read_ctScan_file                       import read_ctScan_file
from freecad.ldpmWorkbench.input.read_interlayer_inputs            import read_interlayer_inputs
from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs                    import read_LDPMCSL_inputs, read_rf_generation_inputs
from freecad.ldpmWorkbench.input.read_LDPMCSL_tetgen                    import read_LDPMCSL_tetgen
from freecad.ldpmWorkbench.input.read_multiMat_file                     import read_multiMat_file

# Importing: output
from freecad.ldpmWorkbench.output.mkVtk_particles                       import mkVtk_particles
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_facets                  import mkVtk_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_fibers                  import mkVtk_LDPMCSL_fibers
from freecad.ldpmWorkbench.output.mkVtk_orientationPath                 import mkVtk_orientationPath
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_flowEdges               import mkVtk_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_nonIntFibers            import mkVtk_LDPMCSL_nonIntFibers
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_projFacets              import mkVtk_LDPMCSL_projFacets
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTetFacets            import mkVtk_LDPM_singleTetFacets
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleEdgeFacets           import mkVtk_LDPM_singleEdgeFacets
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTetParticles         import mkVtk_LDPM_singleTetParticles
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleEdgeParticles        import mkVtk_LDPM_singleEdgeParticles
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTet                  import mkVtk_LDPM_singleTet
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleEdge                 import mkVtk_LDPM_singleEdge
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleCell                 import mkVtk_LDPM_singleCell
from freecad.ldpmWorkbench.output.mkPy_LDPM_singleParaview              import mkPy_LDPM_singleParaview
from freecad.ldpmWorkbench.output.mkPy_LDPM_singleParaviewLabels        import mkPy_LDPM_singleParaviewLabels
from freecad.ldpmWorkbench.output.mkData_nodes                          import mkData_nodes
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_tets                   import mkData_LDPMCSL_tets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_edges                  import mkData_LDPMCSL_edges
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facets                 import mkData_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetfiberInt          import mkData_LDPMCSL_facetfiberInt
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetsVertices         import mkData_LDPMCSL_facetsVertices
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_faceFacets             import mkData_LDPMCSL_faceFacets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_flowEdges              import mkData_LDPMCSL_flowEdges
from freecad.ldpmWorkbench.output.mkData_particles                      import mkData_particles
from freecad.ldpmWorkbench.output.mkDisp_sieveCurves                    import mkDisp_sieveCurves
from freecad.ldpmWorkbench.output.mkIges_LDPMCSL_flowEdges              import mkIges_LDPMCSL_flowEdges



def _copy_external_input(source_file, temp_path, output_name):

    if source_file in [None, "", 0, []]:
        return source_file

    try:
        source_path = Path(source_file)
        if source_path.is_file():
            target_path = Path(temp_path) / output_name
            shutil.copy2(source_path, target_path)
            return str(target_path)
    except Exception:
        pass

    return source_file


def _json_safe(value):

    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def _external_fmt_elapsed(elapsed):
    elapsed_min = int(elapsed // 60)
    elapsed_sec = int(elapsed % 60)
    if elapsed_min > 0:
        return f"{elapsed_min}m {elapsed_sec}s"
    return f"{elapsed_sec}s"


def _external_report(msg):
    text = str(msg)
    if not text.endswith("\n"):
        text += "\n"
    try:
        App.Console.PrintMessage(text)
    except Exception:
        print(text, end="")
    try:
        QtWidgets.QApplication.processEvents()
    except Exception:
        pass


class _ExternalStepMonitor(object):

    def __init__(self, label, interval_s=30):
        self.label = label
        self.interval_s = interval_s
        self._running = [True]
        self._thread = None
        self._emitter = None
        self._t0 = None

    def __enter__(self):
        self._t0 = time.time()
        _external_report(f"{self.label} is in process... (Starting...)")
        try:
            class StatusEmitter(QtCore.QObject):
                status_signal = QtCore.Signal(str)

            self._emitter = StatusEmitter()

            def print_status(msg):
                try:
                    App.Console.PrintMessage(msg)
                except Exception:
                    print(msg.strip())
                try:
                    QtWidgets.QApplication.processEvents()
                except Exception:
                    pass

            self._emitter.status_signal.connect(print_status)

            def monitor():
                while self._running[0]:
                    for _ in range(int(self.interval_s)):
                        if not self._running[0]:
                            return
                        time.sleep(1)
                    if self._running[0]:
                        t = _external_fmt_elapsed(time.time() - self._t0)
                        try:
                            self._emitter.status_signal.emit(
                                f"{self.label} is in process... (Elapsed: {t})\n"
                            )
                        except Exception:
                            pass

            self._thread = threading.Thread(target=monitor, daemon=True)
            self._thread.start()
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc, tb):
        self._running[0] = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        t = _external_fmt_elapsed(time.time() - self._t0)
        if exc_type is None:
            _external_report(f"{self.label} completed in {t}")
        else:
            _external_report(f"{self.label} failed after {t}")
        try:
            if self._emitter is not None:
                self._emitter.status_signal.disconnect()
        except Exception:
            pass
        return False


def driver_LDPMCSL(self, runMode, tempPath):

    if isinstance(runMode, bool):
        runMode = "fast" if runMode else "normal"
    if runMode not in ["normal", "fast", "external"]:
        raise ValueError("runMode must be one of: normal, fast, external")

    gen_ui = None
    for f in self.form:
        if hasattr(f, "statusWindow") and hasattr(f, "progressBar"):
            gen_ui = f
            break
    if gen_ui is None and len(self.form) > 5:
        gen_ui = self.form[5]
    elif gen_ui is None:
        gen_ui = self.form[-1]

    [setupFile, constitutiveEQ, matParaSet, \
        numCPU, numIncrements,maxIter,placementAlg,\
        geoType, dimensions, cadFile,\
        minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, fullerCoef, sieveCurveDiameter, sieveCurvePassing,\
        wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
        cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
        fillerC, fillerDensity, airFrac2,\
        htcToggle, htcLength,\
        fiberToggle, fiberCutting, fiberDiameter, fiberLength, fiberVol, fiberOrientation1, fiberOrientation2, fiberOrientation3, fiberPref, fiberFile, fiberIntersections, fiberOutputFiles,\
        multiMatToggle,aggFile,multiMatFile,multiMatRule,\
        grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP,\
        grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP,\
        grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP,\
        phaseMode,\
        mixPhaseMode, phaseFillerContent, phaseFillerDensity,\
        particlePhaseMode, phaseMinPar, phaseMaxPar, phaseOffsetCoefList,\
        periodicToggle,particleOffsetCoef,\
        outDir, dataFilesGen, visFilesGen, singleTetGen, modelType,\
        orientationPathType_sweep3dp, orientationPathSketchName_sweep3dp, orientationSegments_sweep3dp] = read_LDPMCSL_inputs(self.form)

    interlayer_params = read_interlayer_inputs(self.form)
    rf_params = read_rf_generation_inputs(
        self.form,
        job_plan=getattr(self, "_rfJobPlan", None),
        field_dir=getattr(self, "_rfFieldDir", None),
    )


    if numCPU < 1 or numCPU is None:
        try:
            detected_cpus = multiprocessing.cpu_count()
            numCPU = max(1, detected_cpus - 1)
            print(f"Auto-detected {detected_cpus} CPUs, using {numCPU} for particle generation")
        except:
            numCPU = 1
            print("Could not auto-detect CPUs")

    if maxPar_exp > minPar_exp > 0:
        if minPar_sim < minPar_exp:
            minPar_sim = minPar_exp
        if maxPar_sim > maxPar_exp:
            maxPar_sim = maxPar_exp
    
    if minPar_sim >= maxPar_sim:
        error_msg = f"ERROR: Min particle size ({minPar_sim:.3f}) must be less than max ({maxPar_sim:.3f})."
        print(error_msg)
        gen_ui.statusWindow.setText(error_msg)
        gen_ui.progressBar.setValue(0)
        raise ValueError(error_msg)

    # Make output directory if does not exist
    try:
        os.mkdir(outDir)
    except:
        pass

    i = 0
    # Use single names for geoTypes
    if geoType in ["Box","Cylinder","Cone","Sphere","Ellipsoid","Prism","Dogbone","Custom"]:
        geoTypeOutName = geoType
    elif geoType == "Notched Prism - Semi Circle":
        geoTypeOutName = "NotchedPrismSemiCircle"
    elif geoType == "Notched Prism - Square":
        geoTypeOutName = "NotchedPrismSquare"
    elif geoType == "Notched Prism - Ellipse":
        geoTypeOutName = "NotchedPrismEllipse"
    elif geoType == "Import CAD or Mesh":
        geoTypeOutName = "ImportedFile"
    elif geoType == "Sweep-3DP":
        geoTypeOutName = "Sweep"
    else:
        geoTypeOutName = geoType

    if modelType in ["Confinement Shear Lattice (CSL) - LDPM Style ",\
                        "Confinement Shear Lattice (CSL) - Original"]:
        elementType = "CSL"
    else:
        elementType = "LDPM"

    geoName = elementType + "geo" + str(0).zfill(3)

    outName = '/' + geoName + geoTypeOutName + str(i).zfill(3)
    while os.path.isdir(Path(outDir + outName)):
        i = i+1
        outName = '/' + geoName + geoTypeOutName + str(i).zfill(3)

    try:
        os.makedirs(outDir + outName, exist_ok=True)
    except:
        pass


    # Initialize code start time to measure performance
    start_time = time.time()


    if runMode == "external":
        if App.ActiveDocument is None:
            App.newDocument("Unnamed")
    else:
        # Store document
        docGui = Gui.activeDocument()

        # Make new document and set view if does not exisit
        try:
            docGui.activeView().viewAxonometric()
        except:
            App.newDocument("Unnamed")
            docGui = Gui.activeDocument()
            docGui.activeView().viewAxonometric()
        Gui.runCommand('Std_PerspectiveCamera',1)

    try:
        sieveCurveDiameter = ast.literal_eval(sieveCurveDiameter)
        sieveCurvePassing = ast.literal_eval(sieveCurvePassing)
    except:
        pass

    try:
        grainAggSieveD = ast.literal_eval(grainAggSieveD)
        grainAggSieveP = ast.literal_eval(grainAggSieveP)
    except:
        pass

    try:
        grainITZSieveD = ast.literal_eval(grainITZSieveD)
        grainITZSieveP = ast.literal_eval(grainITZSieveP)
    except:
        pass


    try:
        grainBinderSieveD = ast.literal_eval(grainBinderSieveD)
        grainBinderSieveP = ast.literal_eval(grainBinderSieveP)
    except:
        pass






    if fillerC > 0:
        airFrac = airFrac2
    else:
        airFrac = airFrac1
    
    verbose = "On"

    gen_ui.progressBar.setValue(1) 
    gen_ui.statusWindow.setText("Status: Generating objects.") 




    meshName = elementType + "mesh" + str(0).zfill(3)
    analysisName = elementType + "analysis"
    materialName = elementType + "material"
    dataFilesName = elementType + 'dataFiles'+ str(0).zfill(3)
    visualFilesName = elementType + 'visualFiles'+ str(0).zfill(3)

    i = 0
    try:
        test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
    except:
        test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])

    while test == True:
        i = i+1
        geoName = elementType + "geo" + str(i).zfill(3)
        meshName = elementType + "mesh" + str(i).zfill(3)
        dataFilesName = elementType + 'dataFiles'+ str(i).zfill(3)
        visualFilesName = elementType + 'visualFiles'+ str(i).zfill(3)
        try:
            test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
        except:
            test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])

    # Generate geometry
    gen_ui.statusWindow.setText("Status: Generating geometry.") 
    if geoType == "Sweep-3DP" and len(dimensions) < 11:
        raise ValueError("ERROR: Sweep-3DP selected but parameters are missing.")
    if periodicToggle == "On":
        geoType = 'Import CAD or Mesh'
        # Build the surface mesh based on the simulation particle size
        if runMode == "external":
            with _ExternalStepMonitor("Periodic mesh Creating"):
                cadFile = gen_LDPMCSL_periodicMesh(cadFile,analysisName,geoName,meshName,minPar_sim,dimensions,tempPath)
        else:
            cadFile = gen_LDPMCSL_periodicMesh(cadFile,analysisName,geoName,meshName,minPar_sim,dimensions,tempPath)
    if runMode == "external":
        with _ExternalStepMonitor("Geometry Creating"):
            genGeo = gen_LDPMCSL_geometry(dimensions,geoType,geoName,cadFile)
    else:
        genGeo = gen_LDPMCSL_geometry(dimensions,geoType,geoName,cadFile)
    if genGeo is None:
        raise RuntimeError(f"ERROR: Geometry not created for '{geoType}'.")
    gen_ui.progressBar.setValue(2)

    if runMode != "external":
        # Set view
        docGui.activeView().viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
        Gui.runCommand('Std_DrawStyle',6)
        Gui.runCommand('Std_PerspectiveCamera',1)


    # Generate analysis objects
    if runMode == "external":
        gen_ui.statusWindow.setText("Status: Skipping analysis objects for external generation.")
        _external_report("Skipping analysis objects for external generation.")
        gen_ui.progressBar.setValue(3)

        cementC = cementC * (1.0E+12)
        flyashC = flyashC * (1.0E+12)
        silicaC = silicaC * (1.0E+12)
        scmC = scmC * (1.0E+12)
        cementDensity = cementDensity * (1.0E+12)
        flyashDensity = flyashDensity * (1.0E+12)
        silicaDensity = silicaDensity * (1.0E+12)
        scmDensity = scmDensity * (1.0E+12)
        densityWater = densityWater * (1.0E+12)
        if particlePhaseMode in (2, 3):
            pass
        else:
            fillerC = fillerC * (1.0E+12)
            fillerDensity = fillerDensity * (1.0E+12)
            phaseFillerContent = [c * (1.0E+12) for c in phaseFillerContent]
            phaseFillerDensity = [d * (1.0E+12) for d in phaseFillerDensity]

        parOffset = particleOffsetCoef * minPar_sim

        shape = genGeo.Shape if hasattr(genGeo, "Shape") else None
        if shape is None:
            raise RuntimeError("External packaging failed: geometry has no Shape to export.")

        bb = shape.BoundBox
        minC = np.array([bb.XMin, bb.YMin, bb.ZMin], dtype=float)
        maxC = np.array([bb.XMax, bb.YMax, bb.ZMax], dtype=float)
        try:
            tetVolume = float(shape.Volume)
        except Exception:
            tetVolume = float(abs((maxC[0] - minC[0]) * (maxC[1] - minC[1]) * (maxC[2] - minC[2])))
        max_dist = float(np.linalg.norm(maxC))
        maxEdgeLength = float(2.0 * minPar_sim)

        geometry_brep_name = geoName + "_geometry.brep"
        geometry_brep_path = Path(tempPath) / geometry_brep_name
        _external_report("Exporting geometry for external Gmsh meshing...")
        export_shape_brep(genGeo, geometry_brep_path)

        try:
            gmsh_bin = freecad_gmsh_binary()
        except Exception as e:
            gmsh_bin = ""
            _external_report(f"Warning: Gmsh binary not found ({e}).")

        _external_report("Preparing external package...")

        pathSegments = build_sweep3dp_path_segments(
            geoType,
            dimensions,
            orientationPathType_sweep3dp,
            orientationPathSketchName_sweep3dp,
            orientationSegments_sweep3dp,
        )
        if pathSegments is not None:
            save_path_segments_json(pathSegments, tempPath + "pathSegments_sweep3dp.json")

        agg_suffix = Path(str(aggFile)).suffix if aggFile not in [None, "", 0, []] else ""
        multiMat_suffix = Path(str(multiMatFile)).suffix if multiMatFile not in [None, "", 0, []] else ""
        fiber_suffix = Path(str(fiberFile)).suffix if fiberFile not in [None, "", 0, []] else ""
        aggFileBundle = _copy_external_input(aggFile, tempPath, "aggFile" + agg_suffix)
        multiMatFileBundle = _copy_external_input(multiMatFile, tempPath, "multiMatFile" + multiMat_suffix)
        fiberFileBundle = _copy_external_input(fiberFile, tempPath, "fiberFile" + fiber_suffix)

        manifest = {
            "geoName": geoName,
            "elementType": elementType,
            "geoType": geoType,
            "tempPath": tempPath,
            "outDir": outDir,
            "outName": outName,
            "modelType": modelType,
            "dataFilesGen": dataFilesGen,
            "visFilesGen": visFilesGen,
            "singleTetGen": singleTetGen,
            "numCPU": numCPU,
            "numIncrements": numIncrements,
            "maxIter": maxIter,
            "parOffset": parOffset,
            "maxEdgeLength": maxEdgeLength,
            "max_dist": max_dist,
            "minPar_sim": minPar_sim,
            "maxPar_sim": maxPar_sim,
            "minPar_exp": minPar_exp,
            "maxPar_exp": maxPar_exp,
            "sieveCurveDiameter": sieveCurveDiameter,
            "sieveCurvePassing": sieveCurvePassing,
            "wcRatio": wcRatio,
            "cementC": cementC,
            "airFrac": airFrac,
            "fullerCoef": fullerCoef,
            "flyashC": flyashC,
            "silicaC": silicaC,
            "scmC": scmC,
            "fillerC": fillerC,
            "flyashDensity": flyashDensity,
            "silicaDensity": silicaDensity,
            "scmDensity": scmDensity,
            "fillerDensity": fillerDensity,
            "cementDensity": cementDensity,
            "densityWater": densityWater,
            "multiMatToggle": multiMatToggle,
            "aggFile": aggFileBundle,
            "multiMatFile": multiMatFileBundle,
            "multiMatRule": multiMatRule,
            "phaseMode": phaseMode,
            "grainAggMin": grainAggMin,
            "grainAggMax": grainAggMax,
            "grainAggFuller": grainAggFuller,
            "grainAggSieveD": grainAggSieveD,
            "grainAggSieveP": grainAggSieveP,
            "grainBinderMin": grainBinderMin,
            "grainBinderMax": grainBinderMax,
            "grainBinderFuller": grainBinderFuller,
            "grainBinderSieveD": grainBinderSieveD,
            "grainBinderSieveP": grainBinderSieveP,
            "grainITZMin": grainITZMin,
            "grainITZMax": grainITZMax,
            "grainITZFuller": grainITZFuller,
            "grainITZSieveD": grainITZSieveD,
            "grainITZSieveP": grainITZSieveP,
            "mixPhaseMode": mixPhaseMode,
            "phaseFillerContent": phaseFillerContent,
            "phaseFillerDensity": phaseFillerDensity,
            "particlePhaseMode": particlePhaseMode,
            "phaseMinPar": phaseMinPar,
            "phaseMaxPar": phaseMaxPar,
            "phaseOffsetCoefList": phaseOffsetCoefList,
            "fillerOnlyPhases": particlePhaseMode in (2, 3),
            "tetVolume": tetVolume,
            "minC": [float(minC[0]), float(minC[1]), float(minC[2])],
            "maxC": [float(maxC[0]), float(maxC[1]), float(maxC[2])],
            "verbose": "Off",
            "fiberToggle": fiberToggle,
            "fiberCutting": fiberCutting,
            "fiberDiameter": fiberDiameter,
            "fiberLength": fiberLength,
            "fiberVol": fiberVol,
            "fiberOrientation1": fiberOrientation1,
            "fiberOrientation2": fiberOrientation2,
            "fiberOrientation3": fiberOrientation3,
            "fiberPref": fiberPref,
            "fiberFile": fiberFileBundle,
            "fiberIntersections": fiberIntersections,
            "fiberOutputFiles": fiberOutputFiles,
            "htcToggle": htcToggle,
            "htcLength": htcLength,
            "hasPathSegments": pathSegments is not None and len(pathSegments) > 0,
            "interlayer": interlayer_params,
            "rfToggle": rf_params["rfToggle"],
            "numSamples": rf_params["numSamples"],
            "rfFieldDir": rf_params["rfFieldDir"],
            "rfAssignments": rf_params["rfAssignments"],
            "rfJobPlan": rf_params["rfJobPlan"],
            "needsExternalMesh": True,
            "geometryBrep": geometry_brep_name,
            "gmshBin": gmsh_bin,
        }

        with open(Path(tempPath + "external_manifest_ldpmcsl.json"), "w", encoding="utf-8") as f:
            json.dump(_json_safe(manifest), f, indent=2)

        workbenchRoot = str(Path(__file__).resolve().parents[3])
        runnerPath = Path(tempPath + "run_external_ldpmcsl.py")
        with open(runnerPath, "w", encoding="utf-8") as f:
            f.write(
                "import sys\n"
                "from pathlib import Path\n\n"
                "WORKBENCH_ROOT = r\"" + workbenchRoot.replace("\\", "\\\\") + "\"\n"
                "if WORKBENCH_ROOT not in sys.path:\n"
                "    sys.path.insert(0, WORKBENCH_ROOT)\n\n"
                "from freecad.ldpmWorkbench.generation.run_LDPMCSL_external import run_external_bundle\n\n"
                "if __name__ == '__main__':\n"
                "    run_external_bundle(Path(__file__).resolve().parent)\n"
            )

        file_names = os.listdir(tempPath)
        for file_name in file_names:
            shutil.move(os.path.join(tempPath, file_name), Path(outDir + outName))

        finalDir = Path(outDir + outName)
        manifest["tempPath"] = str(finalDir)
        manifest["geometryBrep"] = str(finalDir / geometry_brep_name)
        if aggFileBundle not in [None, "", 0, []]:
            manifest["aggFile"] = str(finalDir / Path(str(aggFileBundle)).name)
        if multiMatFileBundle not in [None, "", 0, []]:
            manifest["multiMatFile"] = str(finalDir / Path(str(multiMatFileBundle)).name)
        if fiberFileBundle not in [None, "", 0, []]:
            manifest["fiberFile"] = str(finalDir / Path(str(fiberFileBundle)).name)

        with open(finalDir / "external_manifest_ldpmcsl.json", "w", encoding="utf-8") as f:
            json.dump(_json_safe(manifest), f, indent=2)

        gen_ui.statusWindow.setText("Status: External generation package created.")
        gen_ui.progressBar.setValue(100)
        total_elapsed = _external_fmt_elapsed(time.time() - start_time)
        _external_report("External generation package written to: " + str(finalDir))
        _external_report("Geometry in FreeCAD; Gmsh mesh + particles run outside FreeCAD.")
        _external_report("External packaging completed in " + total_elapsed)
        _external_report("Run external: python run_external_ldpmcsl.py")
        return
    else:
        gen_ui.statusWindow.setText("Status: Generating analysis objects.") 
        genAna = gen_LDPMCSL_analysis(analysisName,materialName)
    gen_ui.progressBar.setValue(3) 


    # Generate surface mesh
    gen_ui.statusWindow.setText("Status: Generating surface mesh.") 
    [meshVertices,meshTets,surfaceNodes,surfaceFaces] = gen_LDPMCSL_initialMesh(cadFile,analysisName,geoName,meshName,minPar_sim,geo_obj=genGeo)

    gen_ui.progressBar.setValue(5) 

    # Gets extents of geometry
    [minC,maxC] = calc_LDPMCSL_surfMeshExtents(meshVertices)

    # Convert density to Kg/m3
    cementC = cementC * (1.0E+12)
    flyashC = flyashC * (1.0E+12)
    silicaC = silicaC * (1.0E+12)
    scmC = scmC * (1.0E+12)
    cementDensity = cementDensity * (1.0E+12)
    flyashDensity = flyashDensity * (1.0E+12)
    silicaDensity = silicaDensity * (1.0E+12)
    scmDensity = scmDensity * (1.0E+12)
    densityWater = densityWater * (1.0E+12)
    if particlePhaseMode in (2, 3):
        pass
    else:
        fillerC = fillerC * (1.0E+12)
        fillerDensity = fillerDensity * (1.0E+12)
        phaseFillerContent = [c * (1.0E+12) for c in phaseFillerContent]
        phaseFillerDensity = [d * (1.0E+12) for d in phaseFillerDensity]


    gen_ui.statusWindow.setText("Calculating input data") 

    # Gets volume of geometry
    tetVolume = calc_LDPMCSL_meshVolume(meshVertices,meshTets)


    # Calculation of surface mesh size
    maxEdgeLength = calc_LDPMCSL_surfMeshSize(meshVertices,surfaceFaces)

    # Basic Calcs
    parOffset = particleOffsetCoef*minPar_sim # using simulation particle size instead of experimental size for offset

    
    # Store coordinates of meshTets in new format
    coord1 = meshVertices[meshTets[:,0]-1]
    coord2 = meshVertices[meshTets[:,1]-1]
    coord3 = meshVertices[meshTets[:,2]-1]
    coord4 = meshVertices[meshTets[:,3]-1]

    verts = meshVertices[np.array(meshTets).flatten()-1]
    max_dist = np.max(np.sqrt(np.sum(verts**2, axis=1)))


    if runMode == "fast":

        gen_ui.statusWindow.setText("Status: Preparing data for particle generation...")
        try:
            App.Console.PrintMessage("Preparing data for particle generation...\n")
        except Exception:
            pass
        
        np.save(tempPath + "coord1.npy", coord1)
        np.save(tempPath + "coord2.npy", coord2)
        np.save(tempPath + "coord3.npy", coord3)
        np.save(tempPath + "coord4.npy", coord4)
        np.save(tempPath + "meshVertices.npy", meshVertices)
        np.save(tempPath + "meshTets.npy", meshTets)
        np.save(tempPath + "surfaceNodes.npy", surfaceNodes)

        gen_ui.statusWindow.setText("Status: Starting particle generation...")
        try:
            App.Console.PrintMessage("Starting particle generation...\n")
        except Exception:
            pass
        
        try:
            from freecad.ldpmWorkbench.generation.gen_LDPMCSL_multiStep import gen_LDPMCSL_multiStep
            fiber_result = gen_LDPMCSL_multiStep(
                tempPath, numCPU, numIncrements, maxIter, parOffset, maxEdgeLength, max_dist,
                minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, sieveCurveDiameter, sieveCurvePassing,
                wcRatio, cementC, airFrac, fullerCoef, flyashC, silicaC, scmC, fillerC,
                flyashDensity, silicaDensity, scmDensity, fillerDensity, cementDensity, densityWater,
                multiMatToggle, aggFile, multiMatFile, grainAggMin, grainAggMax, grainAggFuller,
                grainAggSieveD, grainAggSieveP, grainBinderMin, grainBinderMax, grainBinderFuller,
                grainBinderSieveD, grainBinderSieveP, grainITZMin, grainITZMax, grainITZFuller,
                grainITZSieveD, grainITZSieveP, tetVolume, minC, maxC, verbose,
                fiberToggle, fiberFile, fiberDiameter, fiberLength, fiberVol, fiberOrientation1, fiberOrientation2, fiberOrientation3, fiberPref, fiberCutting, fiberIntersections, fiberOutputFiles, surfaceFaces,
                phaseMode,
                phaseMinPar, phaseMaxPar, phaseOffsetCoefList, phaseFillerContent, phaseFillerDensity,
                particlePhaseMode in (2, 3),
            )
            
            gen_ui.statusWindow.setText("Status: Particle generation completed!")
            
        except Exception as e:
            error_msg = f"ERROR: Particle generation failed: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            gen_ui.statusWindow.setText("Status: Particle generation failed!")
            raise RuntimeError(error_msg) from e

        try:
            internalNodes = np.load(tempPath + "internalNodes.npy")
        except FileNotFoundError as e:
            error_msg = f"ERROR: Could not find internalNodes.npy in {tempPath}\n"
            error_msg += f"The subprocess may have failed to generate the required files.\n"
            error_msg += f"Check the output above for details."
            print(error_msg)
            gen_ui.statusWindow.setText("Status: ERROR - Output files not found!")
            raise FileNotFoundError(error_msg) from e

        try:
            materialList = np.load(tempPath + "materialList.npy")
        except FileNotFoundError as e:
            error_msg = f"ERROR: Could not find materialList.npy in {tempPath}"
            print(error_msg)
            raise FileNotFoundError(error_msg) from e

        try:
            parDiameterList = np.load(tempPath + "parDiameterList.npy")
        except FileNotFoundError as e:
            error_msg = f"ERROR: Could not find parDiameterList.npy in {tempPath}"
            print(error_msg)
            raise FileNotFoundError(error_msg) from e

        try:
            particleID = np.load(tempPath + "particleID.npy")
        except FileNotFoundError as e:
            error_msg = f"ERROR: Could not find particleID.npy in {tempPath}"
            print(error_msg)
            raise FileNotFoundError(error_msg) from e

        if fiberToggle in ['on','On','Y','y','Yes','yes']:
            if fiber_result is not None:
                p1Fibers, p2Fibers, orienFibers, fiberLengths, fiberDiameter, nFiber = fiber_result
            elif fiberOutputFiles in ['on','On','Y','y','Yes','yes']:
                try:
                    p1Fibers = np.load(tempPath + "p1Fibers.npy")
                    p2Fibers = np.load(tempPath + "p2Fibers.npy")
                    orienFibers = np.load(tempPath + "orienFibers.npy")
                    fiberLengths = np.load(tempPath + "fiberLengths.npy")
                    fiberDiameter = float(np.load(tempPath + "fiberDiameter.npy")[0])
                    nFiber = int(np.load(tempPath + "nFiber.npy")[0])
                except FileNotFoundError as e:
                    error_msg = f"ERROR: Could not find fiber data files in {tempPath}"
                    print(error_msg)
                    raise FileNotFoundError(error_msg) from e
            else:
                error_msg = f"ERROR: Fiber data missing after generation in {tempPath}"
                print(error_msg)
                raise RuntimeError(error_msg)
        else:
            p1Fibers, p2Fibers, orienFibers, fiberLengths = 0, 0, 0, 0

        if multiMatToggle == "Off":
            volFracPar = np.load(tempPath + "volFracPar.npy")
            parVolTotal = np.load(tempPath + "parVolTotal.npy")

        try:
            os.remove(tempPath + "internalNodes.npy")
            os.remove(tempPath + "materialList.npy")
            os.remove(tempPath + "parDiameterList.npy")
            os.remove(tempPath + "particleID.npy")
            if multiMatToggle == "Off":
                os.remove(tempPath + "volFracPar.npy")
                os.remove(tempPath + "parVolTotal.npy")
            os.remove(tempPath + "coord1.npy")
            os.remove(tempPath + "coord2.npy")
            os.remove(tempPath + "coord3.npy")
            os.remove(tempPath + "coord4.npy")
            os.remove(tempPath + "meshVertices.npy")
            os.remove(tempPath + "meshTets.npy")
            os.remove(tempPath + "surfaceNodes.npy")
        except Exception as e:
            print(f"Could not remove temporary files: {e}")



    else:





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

            fillerOnlyPhases = particlePhaseMode in (2, 3)
            use_phase_sim = len(phaseMinPar) > 0 and len(phaseMaxPar) > 0

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
                    )
                    if i == 0:
                        aggGrainsDiameterList = grainsDiameterList
                    else:
                        binderGrainsDiameterList = grainsDiameterList
                parDiameterList = np.concatenate((aggGrainsDiameterList,binderGrainsDiameterList))
                internalNodes = (np.zeros((len(aggGrainsDiameterList)+len(binderGrainsDiameterList),3))+2)*maxC
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
                    )
                    lists_by_phase[phase_i] = grainsDiameterList
                aggGrainsDiameterList = lists_by_phase[0]
                itzGrainsDiameterList = lists_by_phase[1]
                binderGrainsDiameterList = lists_by_phase[2]
                parDiameterList = np.concatenate((aggGrainsDiameterList,itzGrainsDiameterList,binderGrainsDiameterList))
                internalNodes = (np.zeros((len(aggGrainsDiameterList)+\
                    len(binderGrainsDiameterList)+len(itzGrainsDiameterList),3))+2)*maxC




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



            gen_ui.statusWindow.setText("Status: Calculating list of particles.") 
            # Calculate list of particle diameters for placement
            [maxParNum,parDiameterList] = gen_particleList(parVolTotal, minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, newSieveCurveD,\
                cdf,kappa_i,NewSet,fullerCoef)
        
            # Initialize empty particle nodes list outside geometry
            internalNodes = (np.zeros((len(parDiameterList),3))+2)*maxC
        












        gen_ui.statusWindow.setText('Placing particles into geometry. (' + str(0) + '/' + str(len(internalNodes)) + ')') 
        
        # Initialize values
        newMaxIter = 50
        particlesPlaced = 0

        particleID = np.zeros(len(internalNodes))

        if multiMatToggle == "On":

            use_phase_sim = len(phaseMinPar) > 0 and len(phaseMaxPar) > 0

            def _phase_sim_place(i, grainMin, grainMax):
                if use_phase_sim:
                    return _phase_list_val(phaseMinPar, i, grainMin), _phase_list_val(phaseMaxPar, i, grainMax)
                return grainMin, grainMax

            def _phase_offset_place(i, simMin):
                if len(phaseOffsetCoefList) > i:
                    return _phase_list_val(phaseOffsetCoefList, i, 0.2) * simMin
                return parOffset

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
                    if target > 0 and x % max(1, int(np.rint(target / 100))) == 0:
                        status = (
                            f"[{x}/{target}] Particle placement in process... Phase {phase_num}"
                            f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
                        )
                        gen_ui.progressBar.setValue(80 * ((x) / target) + 6)
                        gen_ui.statusWindow.setText(status)
                        print(status)
                n_placed = len(placed)
                done_msg = f"Particle placement completed Phase {phase_num} ({n_placed}/{n_placed})"
                gen_ui.statusWindow.setText(done_msg)
                print(done_msg)
                return np.asarray(placed) if n_placed > 0 else np.array([])

            if phaseMode == 2:
                sim0, sim0max = _phase_sim_place(0, grainAggMin, grainAggMax)
                sim1, sim1max = _phase_sim_place(1, grainBinderMin, grainBinderMax)
                aggGrainsDiameterList = _place_phase_grains(0, aggGrainsDiameterList, aggVoxels, sim0, sim0max, aggVoxelIDs, 0, _phase_offset_place(0, sim0))
                n0 = len(aggGrainsDiameterList)
                n1 = len(binderGrainsDiameterList)
                internalNodes = np.vstack([np.asarray(internalNodes[:n0]), (np.zeros((n1, 3)) + 2) * maxC])
                particleID = np.concatenate([np.asarray(particleID[:n0]), np.zeros(n1)])
                parDiameterList = np.concatenate([aggGrainsDiameterList, binderGrainsDiameterList])
                binderGrainsDiameterList = _place_phase_grains(1, binderGrainsDiameterList, binderVoxels, sim1, sim1max, 0, n0, _phase_offset_place(1, sim1))
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
                sim0, sim0max = _phase_sim_place(0, grainAggMin, grainAggMax)
                sim1, sim1max = _phase_sim_place(1, grainITZMin, grainITZMax)
                sim2, sim2max = _phase_sim_place(2, grainBinderMin, grainBinderMax)
                aggGrainsDiameterList = _place_phase_grains(0, aggGrainsDiameterList, aggVoxels, sim0, sim0max, aggVoxelIDs, 0, _phase_offset_place(0, sim0))
                n0 = len(aggGrainsDiameterList)
                n1 = len(itzGrainsDiameterList)
                n2 = len(binderGrainsDiameterList)
                internalNodes = np.vstack([np.asarray(internalNodes[:n0]), (np.zeros((n1 + n2, 3)) + 2) * maxC])
                particleID = np.concatenate([np.asarray(particleID[:n0]), np.zeros(n1 + n2)])
                parDiameterList = np.concatenate([aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList])
                itzGrainsDiameterList = _place_phase_grains(1, itzGrainsDiameterList, itzVoxels, sim1, sim1max, 0, n0, _phase_offset_place(1, sim1))
                n1 = len(itzGrainsDiameterList)
                n2 = len(binderGrainsDiameterList)
                internalNodes = np.vstack([np.asarray(internalNodes[:n0 + n1]), (np.zeros((n2, 3)) + 2) * maxC])
                particleID = np.concatenate([np.asarray(particleID[:n0 + n1]), np.zeros(n2)])
                parDiameterList = np.concatenate([aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList])
                binderGrainsDiameterList = _place_phase_grains(
                    2, binderGrainsDiameterList, binderVoxels, sim2, sim2max, 0,
                    n0 + n1, _phase_offset_place(2, sim2)
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

            use_parallel = (numCPU > 1) and USE_PROCESSES
            
            if use_parallel:
                from freecad.ldpmWorkbench.generation.gen_LDPMCSL_multiStep import configure_multiprocessing_for_freecad
                worker_exe = configure_multiprocessing_for_freecad()
                print("Using multiprocessing with {} CPUs (worker: {})".format(numCPU, worker_exe))
                
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
                                                maxPar_sim,parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes)
                                            internalNodes[particlesPlaced+x,:] = node[0,:]
                                        except RuntimeError:
                                            internalNodes[particlesPlaced+x,:] = np.array([maxC[0]*1000, maxC[1]*1000, maxC[2]*1000])

                            particlesPlaced = particlesPlaced + len(nodeMPI)

                            gen_ui.progressBar.setValue(int(80*((particlesPlaced)/len(parDiameterList))+6))
                            gen_ui.statusWindow.setText("Placing particles into geometry. (" + str(particlesPlaced) + '/' + str(len(parDiameterList)) + ')')
                            
                            QtWidgets.QApplication.processEvents()
                    
                    finally:
                        executor.shutdown(wait=True)
                    
                    particlesPlaced = len(parDiameterList)

                except (BrokenProcessPool, OSError) as e:
                    print("Multiprocessing failed ({}); using single-threaded placement".format(e))
                    gen_ui.statusWindow.setText("Multiprocessing failed")
                
            else:
                print("Using single-threaded particle placement")
                gen_ui.statusWindow.setText("Using single-threaded particle placement")


            write_idx = particlesPlaced
            particles_skipped = 0
            orig_n = len(parDiameterList)
            placement_start = time.time()
            progress_file = tempPath + "progress.txt"
            if particlesPlaced < orig_n:
                print(f"[{particlesPlaced}/{orig_n}] Particle placement in process...")

            for x in range(particlesPlaced, orig_n):

                particle_start = time.time()
                
                try:
                    [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,parDiameterList[x],meshVertices,meshTets,newMaxIter,maxIter,minPar_sim,maxPar_sim,\
                        parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes)
                        
                except RuntimeError as e:
                    particles_skipped += 1
                    iterReq = 0
                    particle_time = time.time() - particle_start
                    elapsed = time.time() - placement_start
                    remaining = orig_n - x - 1
                    avg_time = elapsed / max(1, (x + 1 - particles_skipped))
                    eta = avg_time * remaining
                    progress_pct = 80*((x+1)/orig_n)+6
                    gen_ui.progressBar.setValue(int(progress_pct))
                    gen_ui.statusWindow.setText(
                        'Placing particles into geometry. (' + str(x+1) + '/' + str(orig_n) + ')'
                    )
                    if x % 10 == 0 or (x + 1) == orig_n:
                        status = f"[{x+1}/{orig_n}] Particle placement in process..."
                        status += f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
                        print(status)
                    with open(progress_file, 'w', encoding='utf-8') as pf:
                        pf.write(f"[{x+1}/{orig_n}] Particle placement in process...\n")
                        pf.write(f"Progress: {100*(x+1)/orig_n:.1f}%\n")
                        pf.write(f"Iterations: {iterReq}\n")
                        pf.write(f"Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s\n")
                        pf.write(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    QtWidgets.QApplication.processEvents()
                    continue

                particle_time = time.time() - particle_start
                elapsed = time.time() - placement_start
                remaining = orig_n - x - 1
                avg_time = elapsed / (x + 1 - particles_skipped) if (x + 1 - particles_skipped) > 0 else particle_time
                eta = avg_time * remaining
                
                progress_pct = 80*((x+1)/orig_n)+6
                gen_ui.progressBar.setValue(int(progress_pct))
                
                gen_ui.statusWindow.setText(
                    'Placing particles into geometry. (' + str(x+1) + '/' + str(orig_n) + ')'
                )
                
                if iterReq < 100 or x % 10 == 0 or (x + 1) == orig_n:
                    status = f"[{x+1}/{orig_n}] Particle placement in process..."
                    status += f" | Iterations: {iterReq} | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s"
                    print(status)
                
                with open(progress_file, 'w', encoding='utf-8') as pf:
                    pf.write(f"[{x+1}/{orig_n}] Particle placement in process...\n")
                    pf.write(f"Progress: {100*(x+1)/orig_n:.1f}%\n")
                    pf.write(f"Iterations: {iterReq}\n")
                    pf.write(f"Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s\n")
                    pf.write(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

                if write_idx != x:
                    parDiameterList[write_idx] = parDiameterList[x]
                internalNodes[write_idx,:] = node
                write_idx += 1
                
                QtWidgets.QApplication.processEvents()

            if write_idx < orig_n:
                parDiameterList = np.asarray(parDiameterList[:write_idx])
                internalNodes = np.asarray(internalNodes[:write_idx])

            if particlesPlaced < orig_n:
                done_msg = "Particle placement completed."
                gen_ui.statusWindow.setText(done_msg)
                print(done_msg)


            materialList = np.ones(len(parDiameterList))

            # Create empty lists if not multi-material or cementStructure
            aggGrainsDiameterList, itzGrainsDiameterList, binderGrainsDiameterList, PoresDiameterList,\
                ClinkerDiameterList, CHDiameterList, CSH_LDDiameterList, CSH_HDDiameterList = 0,0,0,0,0,0,0,0
            particleID = np.zeros(len(parDiameterList))




        placementTime = round(time.time() - start_time,2)   
        nParticles = len(parDiameterList) 




    pathSegments = build_sweep3dp_path_segments(
        geoType,
        dimensions,
        orientationPathType_sweep3dp,
        orientationPathSketchName_sweep3dp,
        orientationSegments_sweep3dp,
    )
    if pathSegments is not None:
        print(
            f"PathSegments created with {len(pathSegments)} segments "
            f"(orientationPathType_sweep3dp={orientationPathType_sweep3dp})"
        )
    elif geoType == "Sweep-3DP" and orientationPathType_sweep3dp >= 0:
        print(
            f"Sweep-3DP orientation path (type={orientationPathType_sweep3dp}): "
            f"No pathSegments created"
        )
    else:
        print(f"geoType: {geoType} | orientationPathType: {orientationPathType_sweep3dp}")

    if fiberToggle in ['on','On','Y','y','Yes','yes']:
        
        fiberStartTime = time.time()

        # Use fiber data from CT scan if file exists
        if fiberFile and str(fiberFile).strip() and str(fiberFile).strip() not in ["0", "None", "[]"]:

            try:
                # CTScanfiber data arrangement
                CTScanFiberData = read_ctScan_file(fiberFile)
            except (FileNotFoundError, IOError, ValueError, OSError) as e:
                error_msg = f"ERROR: Could not read CT scan fiber file '{fiberFile}': {e}"
                print(error_msg)
                gen_ui.statusWindow.setText("ERROR: Invalid CT scan fiber file!")
                raise RuntimeError(error_msg) from e

            # Check if any fibers were loaded
            if len(CTScanFiberData) == 0:
                error_msg = f"ERROR: No valid fibers found in CT scan file '{fiberFile}'"
                print(error_msg)
                gen_ui.statusWindow.setText(error_msg)
                raise RuntimeError(error_msg)
            
            CTScanFiberData = np.array(CTScanFiberData).reshape(-1,10)
            p1Fibers = CTScanFiberData[:,0:3]
            p2Fibers = CTScanFiberData[:,3:6]
            orienFibers = CTScanFiberData[:,6:9]
            fiberLengths = CTScanFiberData[:,9:10]
            
            # Validate fiber data
            if len(p1Fibers) == 0:
                error_msg = f"ERROR: No fibers extracted from CT scan file '{fiberFile}'"
                print(error_msg)
                gen_ui.statusWindow.setText(error_msg)
                raise RuntimeError(error_msg)
            
            # Set number of fibers from CT scan data
            nFiber = len(p1Fibers)
            fiberTime = round(time.time() - fiberStartTime,2)
            status_msg = f'{nFiber} fibers loaded from CT scan file in {fiberTime} seconds'
            print(status_msg)
            gen_ui.statusWindow.setText(status_msg)


        # Generate fibers if no CT data
        else:


            if fiberPref<0 or fiberPref>1:

                gen_ui.statusWindow.setText('Fiber orientation strength is out of range, use 0-1')

            # Calculate number of fibers needed 
            nFiber = int(round(4*tetVolume*fiberVol/(math.pi*fiberDiameter**2*fiberLength)))

            # Initialize empty fiber nodes list outside geometry
            p1Fibers = (np.zeros((nFiber,3))+2)*maxC
            p2Fibers = (np.zeros((nFiber,3))+2)*maxC
            orienFibers = (np.zeros((nFiber,3))+2)*maxC
            fiberLengths = (np.zeros((nFiber,1)))

            if geoType == "Sweep-3DP" and pathSegments is not None:
                print(f"Starting fiber generation: pathSegments={len(pathSegments)}, fiberPref={fiberPref}")
            
            for x in range(0,nFiber):
                
                if x % 100 == 0:

                    gen_ui.statusWindow.setText(str(nFiber-x) + ' Fibers Remaining')


                [p1Fiber, p2Fiber, orienFiber, lFiber] = gen_LDPMCSL_fibers(meshVertices,meshTets,coord1,\
                    coord2,coord3,coord4,maxIter,fiberLength,maxC,maxPar_sim,\
                    np.array([fiberOrientation1, fiberOrientation2, fiberOrientation3]),fiberPref,surfaceFaces,\
                    fiberCutting,pathSegments)
                
                p1Fibers[x,:] = p1Fiber
                p2Fibers[x,:] = p2Fiber
                orienFibers[x,:] = orienFiber
                fiberLengths[x,:] = lFiber

            fiberTime = round(time.time() - fiberStartTime,2)

            gen_ui.statusWindow.setText(str(nFiber) + ' fibers placed in ' + str(fiberTime) + ' seconds')

            orienFibers[np.abs(orienFibers) < 1e-10] = 0.0
            
            for i in range(len(orienFibers)):
                norm = np.linalg.norm(orienFibers[i])
                if norm > 0:
                    orienFibers[i] = orienFibers[i] / norm
            
            if fiberOutputFiles in ['on','On','Y','y','Yes','yes']:
                np.save(tempPath + "p1Fibers.npy", p1Fibers)
                np.save(tempPath + "p2Fibers.npy", p2Fibers)
                np.save(tempPath + "orienFibers.npy", orienFibers)
                np.save(tempPath + "fiberLengths.npy", fiberLengths)
                np.save(tempPath + "fiberDiameter.npy", np.array([fiberDiameter]))
                np.save(tempPath + "nFiber.npy", np.array([nFiber]))




    tetTessTimeStart = time.time()

    # Generate tetrahedralization
    gen_ui.statusWindow.setText("Status: Forming tetrahedralization.") 
    
    try:
        App.Console.PrintMessage("Tetrahedralization in process... (Starting...)\n")
    except Exception as e:
        print(f"Could not print to console: {e}")
    
    # Process events to ensure starting message appears
    try:
        QtWidgets.QApplication.processEvents()
    except:
        pass
    
    # Use background thread + Qt signal to post messages to main thread
    # This works even when main thread is blocked by os.system()
    tetra_start_time = time.time()
    tetra_running = [True]
    tetra_emitter = None
    monitor_thread = None
    
    try:
        # Create a QObject to emit signals from thread
        class StatusEmitter(QtCore.QObject):
            status_signal = QtCore.Signal(str)
        
        tetra_emitter = StatusEmitter()
        
        def print_status(msg):
            try:
                App.Console.PrintMessage(msg)
            except:
                print(msg.strip())
            try:
                QtWidgets.QApplication.processEvents()  # Ensure message appears immediately
            except:
                pass
        
        tetra_emitter.status_signal.connect(print_status)
        
        def monitor_tetra_status():
            try:
                while tetra_running[0]:
                    # Sleep in 1-second intervals to allow quick shutdown
                    for _ in range(60):
                        if not tetra_running[0]:
                            return
                        time.sleep(1)
                    
                    if tetra_running[0]:
                        elapsed = time.time() - tetra_start_time
                        elapsed_min = int(elapsed // 60)
                        elapsed_sec = int(elapsed % 60)
                        if elapsed_min > 0:
                            time_str = f"{elapsed_min}m {elapsed_sec}s"
                        else:
                            time_str = f"{elapsed_sec}s"
                        # Use Qt signal to post message to main thread (thread-safe)
                        try:
                            tetra_emitter.status_signal.emit(f"Tetrahedralization in process... (Elapsed: {time_str})\n")
                        except Exception as e:
                            print(f"Could not emit status signal: {e}")
            except Exception as e:
                print(f"Monitor thread error: {e}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_tetra_status, daemon=True)
        monitor_thread.start()
    except Exception as e:
        print(f"Could not start status monitoring: {e}")
    
    try:
        tetGen = gen_LDPMCSL_tetrahedralization(internalNodes,surfaceNodes,\
            surfaceFaces,geoName,tempPath)
    finally:
        # Stop the monitoring thread
        tetra_running[0] = False
        
        # Wait briefly for thread to stop
        if monitor_thread and monitor_thread.is_alive():
            monitor_thread.join(timeout=2.0)
        
        # Print completion message
        elapsed = time.time() - tetra_start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        if elapsed_min > 0:
            time_str = f"{elapsed_min}m {elapsed_sec}s"
        else:
            time_str = f"{elapsed_sec}s"
        
        try:
            App.Console.PrintMessage(f"Tetrahedralization completed in {time_str}\n")
        except:
            print(f"Tetrahedralization completed in {time_str}")
        
        try:
            QtWidgets.QApplication.processEvents()
        except:
            pass
        
        # Cleanup signal connection
        try:
            if tetra_emitter:
                tetra_emitter.status_signal.disconnect()
        except:
            pass
    
    gen_ui.progressBar.setValue(89) 


    # Read in tetrahedralization
    [allNodes,allTets,allEdges] = read_LDPMCSL_tetgen(Path(tempPath + geoName \
    + '.node'),Path(tempPath + geoName + '.ele'),Path(tempPath + geoName + '.edge'))
    gen_ui.progressBar.setValue(90) 


    # Generate tesselation
    gen_ui.statusWindow.setText("Status: Forming tesselation.") 
    
    # Print starting message to Report View
    try:
        App.Console.PrintMessage("Tesselation in process... (Starting...)\n")
    except Exception as e:
        print(f"Could not print to console: {e}")
    
    try:
        QtWidgets.QApplication.processEvents()
    except:
        pass
    
    # Use background thread + Qt signal to post messages to main thread
    tesselation_start_time = time.time()
    tesselation_running = [True]
    tesselation_emitter = None
    tesselation_monitor_thread = None
    
    try:
        # Create a QObject to emit signals from thread
        class TesselationEmitter(QtCore.QObject):
            status_signal = QtCore.Signal(str)
        
        tesselation_emitter = TesselationEmitter()
        
        def print_tesselation_status(msg):
            try:
                App.Console.PrintMessage(msg)
            except:
                print(msg.strip())
            try:
                QtWidgets.QApplication.processEvents()  # Ensure message appears immediately
            except:
                pass
        
        tesselation_emitter.status_signal.connect(print_tesselation_status)
        
        def monitor_tesselation_status():
            try:
                while tesselation_running[0]:
                    # Sleep in 1-second intervals to allow quick shutdown
                    for _ in range(60):
                        if not tesselation_running[0]:
                            return
                        time.sleep(1)
                    
                    if tesselation_running[0]:
                        elapsed = time.time() - tesselation_start_time
                        elapsed_min = int(elapsed // 60)
                        elapsed_sec = int(elapsed % 60)
                        if elapsed_min > 0:
                            time_str = f"{elapsed_min}m {elapsed_sec}s"
                        else:
                            time_str = f"{elapsed_sec}s"
                        # Use Qt signal to post message to main thread (thread-safe)
                        try:
                            tesselation_emitter.status_signal.emit(f"Tesselation in process... (Elapsed: {time_str})\n")
                        except Exception as e:
                            print(f"Could not emit status signal: {e}")
            except Exception as e:
                print(f"Monitor thread error: {e}")
        
        # Start monitoring thread
        tesselation_monitor_thread = threading.Thread(target=monitor_tesselation_status, daemon=True)
        tesselation_monitor_thread.start()
    except Exception as e:
        print(f"Could not start status monitoring: {e}")
    
    try:
        [tetFacets,facetCenters,facetAreas,facetNormals,tetn1,tetn2,tetPoints,allDiameters,facetPointData,facetCellData] = \
            gen_LDPMCSL_tesselation(allNodes,allTets,parDiameterList,minPar_sim,geoName)
    finally:
        # Stop the monitoring thread
        tesselation_running[0] = False
        
        # Wait briefly for thread to stop
        if tesselation_monitor_thread and tesselation_monitor_thread.is_alive():
            tesselation_monitor_thread.join(timeout=2.0)
        
        # Print completion message
        elapsed = time.time() - tesselation_start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        if elapsed_min > 0:
            time_str = f"{elapsed_min}m {elapsed_sec}s"
        else:
            time_str = f"{elapsed_sec}s"
        
        try:
            App.Console.PrintMessage(f"Tesselation completed in {time_str}\n")
        except:
            print(f"Tesselation completed in {time_str}")
        
        try:
            QtWidgets.QApplication.processEvents()
        except:
            pass
        
        # Cleanup signal connection
        try:
            if tesselation_emitter:
                tesselation_emitter.status_signal.disconnect()
        except:
            pass    

    # If edge elements are turned on, perform edge computations
    if htcToggle in ['on','On']:
        edgeData = gen_LDPMCSL_flowEdges(htcLength,allNodes,allTets,tetPoints,maxPar_sim,\
            meshVertices,meshTets,coord1,coord2,coord3,coord4,maxC)

    else:
        edgeData = 0




    gen_ui.progressBar.setValue(95) 
    tetTessTime = round(time.time() - tetTessTimeStart,2)   




    # Store values for unused features
    edgeMaterialList = 0
    cementStructure = 'Off'




    writeTimeStart = time.time()



    

    if multiMatToggle in ['on','On','Y','y','Yes','yes']:

        # Read in multi-material file
        [multiMatX,multiMatY,multiMatZ,multiMatRes,multiMatVoxels] = read_multiMat_file(multiMatFile)


        # Organize and store voxels of each material
        sortedVoxels = sort_multiMat_voxels(multiMatVoxels, phaseMode=phaseMode)
        [aggVoxels,itzVoxels,binderVoxels,aggVoxelIDs] = sortedVoxels
        if phaseMode == 2:
            itzVoxels = np.array([])


    # Extend material lists for edge nodes
    particleID = np.concatenate((0*np.ones([len(allNodes)-\
        len(particleID),]),particleID))
    
    if multiMatToggle in ['on','On','Y','y','Yes','yes']:
        if phaseMode == 2:
            edgeFill = 2
        else:
            edgeFill = 3
        materialList = np.concatenate((edgeFill*np.ones([len(allNodes)-\
            len(materialList),]),materialList))

    elif cementStructure in ['on','On','Y','y','Yes','yes']:
        materialList = np.concatenate((edgeMaterialList,materialList))

    else:
        materialList = np.concatenate((0*np.ones([len(allNodes)-\
            len(materialList),]),materialList))    


    # For surface particles, find the nearest voxel and assign the material
    if multiMatToggle in ['on','On','Y','y','Yes','yes']:
        materialList = gen_multiMat_assign(
            allNodes, materialList, aggVoxels, itzVoxels, binderVoxels, internalNodes,
            multiMatX, multiMatY, multiMatZ, multiMatRes, minC,
            phaseMode=phaseMode
        )






    
    gen_ui.statusWindow.setText("Status: Generating facet data information.") 

    if elementType == "LDPM":
        [facetData,facetMaterial,subtetVol,facetVol1,facetVol2,particleMaterial] = gen_LDPM_facetData(\
            allNodes,allTets,tetFacets,facetCenters,facetAreas,facetNormals,tetn1,\
            tetn2,materialList,multiMatRule,multiMatToggle,cementStructure,edgeMaterialList,facetCellData,particleID,
            phaseMode=phaseMode)
    elif elementType == "CSL":
        [facetData,facetMaterial,subtetVol,facetVol1,facetVol2,particleMaterial] = gen_CSL_facetData(\
            allNodes,allEdges,allTets,tetFacets,facetCenters,facetAreas,facetNormals,tetn1,\
            tetn2,materialList,multiMatRule,multiMatToggle,cementStructure,edgeMaterialList,facetCellData,particleID)


    gen_ui.progressBar.setValue(98) 


    if ((fiberToggle in ['on','On','Y','y','Yes','yes']) and (fiberIntersections in ['on','On','Y','y','Yes','yes'])):

        gen_ui.statusWindow.setText('Determining fiber-facet intersections.')

        [FiberdataList,TotalIntersections,MaxInterPerFacet,TotalTet,TotalFiber,IntersectedFiber,projectedFacet]\
            = gen_LDPMCSL_facetfiberInt(p1Fibers,p2Fibers,fiberDiameter,fiberLengths,orienFibers,\
            geoName,allTets,allNodes,tetFacets,facetData,tetn1,tetn2,facetNormals,facetCenters)




    gen_ui.statusWindow.setText("Status: Writing external facet data file.") 
    # Create file of external triangle facets for plotting of cells
    #externalFacetsFile = externalFacetFile(facetData,meshVertices,surfaceFaces,geoName)





    # Initialize counter for number of facet materials switched
    matSwitched = 0


    # Calculate volume associated with each material (and adjust for high-order material rules)
    if multiMatToggle == "On":

        # Read in aggregate file
        try:
            [multiMatX,multiMatY,multiMatZ,multiMatRes,aggDistinctVoxels] = read_multiMat_file(aggFile)
        except:
            pass


        # Read in multi-material file
        [multiMatX,multiMatY,multiMatZ,multiMatRes,multiMatVoxels] = read_multiMat_file(multiMatFile)


        # Organize and store voxels of each material
        sortedVoxels = sort_multiMat_voxels(multiMatVoxels, phaseMode=phaseMode)
        [aggVoxels,itzVoxels,binderVoxels,aggVoxelIDs] = sortedVoxels
        if phaseMode == 2:
            itzVoxels = np.array([])
        try:
            [aggVoxels,discard2,discard3,aggVoxelIDs] = sort_multiMat_voxels(aggDistinctVoxels, phaseMode=phaseMode)
        except:
            pass

        else:
            [itzVolFracSim,binderVolFracSim,aggVolFracSim,itzVolFracAct,binderVolFracAct,aggVolFracAct] = check_multiMat_matVol(
                subtetVol,facetMaterial,aggVoxels,itzVoxels,binderVoxels, phaseMode=phaseMode)
        
            if multiMatRule > 9:

                sortedData1 = sort_multiMat_mat(facetMaterial,facetVol1,facetVol2,particleMaterial,subtetVol)

                i = 0
                
                while (abs(itzVolFracSim-itzVolFracAct) > 0.02 or abs(itzVolFracSim-itzVolFracAct) == 0.00) and \
                    abs(binderVolFracSim-binderVolFracAct) > 0.02 and \
                    abs(aggVolFracSim-aggVolFracAct) > 0.02 and i < len(sortedData1):

                    # Skip refinement for facets with same-material particles
                    if sortedData1[i,3] != sortedData1[i,4]:
                        
                        # Refine material assignment based on volume fractions
                        sortedData = gen_multiMat_refine(sortedData1,
                            itzVolFracSim,binderVolFracSim,aggVolFracSim,\
                            itzVolFracAct,binderVolFracAct,aggVolFracAct,i,
                            phaseMode=phaseMode)

                        # Recalculate and update volume fractions
                        [itzVolFracSim,binderVolFracSim,aggVolFracSim,itzVolFracAct,binderVolFracAct,\
                            aggVolFracAct] = check_multiMat_matVol(sortedData[:,5],sortedData[:,2],\
                            aggVoxels,itzVoxels,binderVoxels, phaseMode=phaseMode)     

                        sortedData1 = sortedData
                        matSwitched = matSwitched+1

                    else:
                        pass

                    i = i+1
                    

                [facetData,facetMaterial] = gen_multiMat_reform(allTets,facetData,sortedData1)

            [itzVolFracSim,binderVolFracSim,aggVolFracSim,itzVolFracAct,binderVolFracAct,\
                aggVolFracAct] = check_multiMat_matVol(subtetVol,facetMaterial,\
                aggVoxels,itzVoxels,binderVoxels, phaseMode=phaseMode)

    if multiMatToggle == "Off":

        itzVolFracSim,binderVolFracSim,aggVolFracSim,itzVolFracAct,binderVolFracAct,aggVolFracAct,\
            PoresVolFracSim,ClinkerVolFracSim,CHVolFracSim,CSH_LDVolFracSim,CSH_HDVolFracSim,\
            PoresVolFracAct,ClinkerVolFracAct,CHVolFracAct,CSH_LDVolFracAct,CSH_HDVolFracAct,\
            matSwitched,multiMatRule = 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0

    if elementType == "LDPM" and interlayer_params.get("enabled"):
        gen_ui.statusWindow.setText("Status: Applying 3DCP interlayer mF tags.")
        apply_3DCP_interlayer(facetData, facetMaterial, minC, maxC, interlayer_params)

    rf_realization = resolve_rf_realization(rf_params, sample_id=1)
    if rf_realization is not None:
        gen_ui.statusWindow.setText("Status: Mapping random field to facets (EOLE).")
        try:
            QtWidgets.QApplication.processEvents()
        except Exception:
            pass
        try:
            facetData = apply_rf_eole_to_facet_data(
                facetData,
                rf_params.get("rfFieldDir", ""),
                rf_realization,
            )
            App.Console.PrintMessage(
                f"Random field mapped to facets: realization {rf_realization} "
                f"from {rf_params.get('rfFieldDir', '')}\n"
            )
        except Exception as e:
            App.Console.PrintError(f"RF mapping failed: {e}\n")
            gen_ui.statusWindow.setText(f"Status: ERROR - RF mapping failed: {e}")

    App.activeDocument().addObject('App::DocumentObjectGroup',dataFilesName)
    App.activeDocument().getObject(dataFilesName).Label = 'Data Files'

    App.activeDocument().addObject('App::DocumentObjectGroup',visualFilesName)
    App.activeDocument().getObject(visualFilesName).Label = 'Visualization Files'




    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName))
    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName))


    # If data files requested, generate them
    if dataFilesGen == True:

        gen_ui.statusWindow.setText("Status: Writing node data file.")

        mkData_nodes(geoName,tempPath,allNodes)

        gen_ui.statusWindow.setText("Status: Writing tet data file.")

        mkData_LDPMCSL_tets(geoName,tempPath,allTets)

        if elementType == "CSL":
            gen_ui.statusWindow.setText("Status: Writing edge data file.")
            mkData_LDPMCSL_edges(geoName,tempPath,allEdges)


        gen_ui.statusWindow.setText("Status: Writing facet data file.")

        # If data files requested, generate Facet File
        mkData_LDPMCSL_facets(geoName,tempPath,facetData)
        mkData_LDPMCSL_facetsVertices(geoName,tempPath,tetFacets)
        mkData_LDPMCSL_faceFacets(geoName,tempPath,surfaceNodes,surfaceFaces)
        
        if ((fiberToggle in ['on','On','Y','y','Yes','yes']) and (fiberIntersections in ['on','On','Y','y','Yes','yes'])):
                mkData_LDPMCSL_facetfiberInt(geoName,FiberdataList,TotalIntersections,MaxInterPerFacet,tempPath)

        

        gen_ui.statusWindow.setText("Status: Writing particle data file.")


        # Create diameters list (including zero edge particle diameters)
        allDiameters = np.concatenate((np.array([0.0,]*int(len(allNodes)-len(parDiameterList))),parDiameterList))

        # If data files requested, generate Particle Data File
        mkData_particles(allNodes,allDiameters,geoName,tempPath)


        if htcToggle in ['on','On']:

            gen_ui.statusWindow.setText("Status: Writing flow edge data file.")

            # Generate edge element data file
            mkData_LDPMCSL_flowEdges(geoName,edgeData,tempPath)

    # If visuals requested, generate them
    if visFilesGen == True:

        gen_ui.statusWindow.setText("Status: Writing visualization files.")

        # If visuals requested, generate Particle VTK File (note we only want to visualize internal nodes, hence the slicing)
        mkVtk_particles(internalNodes,parDiameterList,materialList[(len(allNodes)-len(internalNodes)):len(allNodes)],geoName,tempPath)

        # If visuals requested, generate Facet VTK File
        mkVtk_LDPMCSL_facets(geoName,tempPath,tetFacets,facetMaterial,facetData)

        # If visuals requested, generate flow edge VTK File
        if htcToggle in ['on','On']:

            mkVtk_LDPMCSL_flowEdges(geoName,edgeData,tempPath)
            mkIges_LDPMCSL_flowEdges(geoName,edgeData,tempPath)

        if fiberToggle in ['on','On','Y','y','Yes','yes']:
            mkVtk_LDPMCSL_fibers(p1Fibers,p2Fibers,fiberDiameter,fiberLengths,orienFibers,geoName,tempPath)

        if ((fiberToggle in ['on','On','Y','y','Yes','yes']) and (fiberIntersections in ['on','On','Y','y','Yes','yes'])):
            mkVtk_LDPMCSL_projFacets(geoName,projectedFacet,tempPath)
            mkVtk_LDPMCSL_nonIntFibers(p1Fibers,p2Fibers,fiberDiameter,fiberLengths,orienFibers,geoName,IntersectedFiber,tempPath)
        
        if geoType == "Sweep-3DP" and pathSegments is not None and len(pathSegments) > 0:
            mkVtk_orientationPath(pathSegments, geoName, tempPath)    


    # If single tet/cell visuals requested, generate them
    if singleTetGen == True:
        if elementType == "LDPM":
            mkVtk_LDPM_singleTetFacets(geoName,tempPath,tetFacets)
            mkVtk_LDPM_singleTetParticles(allNodes,allTets,allDiameters,geoName,tempPath)
            mkVtk_LDPM_singleTet(allNodes,allTets,geoName,tempPath)
            mkVtk_LDPM_singleCell(allNodes,allTets,parDiameterList,tetFacets,geoName,tempPath)
            mkPy_LDPM_singleParaview(geoName, outDir, outName, tempPath)
            mkPy_LDPM_singleParaviewLabels(geoName, tempPath)
        elif elementType == "CSL":
            pass
            mkVtk_LDPM_singleEdgeFacets(geoName,tempPath,allEdges,facetData,tetFacets)
            mkVtk_LDPM_singleEdgeParticles(allNodes,allEdges,allDiameters,geoName,tempPath)
            mkVtk_LDPM_singleEdge(allNodes,allEdges,geoName,tempPath)
        else:
            pass




    # Move files to selected output directory
    if fiberOutputFiles not in ['on','On','Y','y','Yes','yes']:
        for _fn in ("p1Fibers.npy", "p2Fibers.npy", "orienFibers.npy", "fiberLengths.npy", "fiberDiameter.npy", "nFiber.npy"):
            try:
                os.remove(tempPath + _fn)
            except OSError:
                pass

    # List all files in temp directory
    file_names = os.listdir(tempPath)
        
    # Move all files to output directory    
    for file_name in file_names:
        src_path = os.path.join(tempPath, file_name)
        dst_path = os.path.join(outDir + outName, file_name)
        # If destination exists, remove it first to avoid conflicts
        if os.path.exists(dst_path):
            if os.path.isfile(dst_path):
                os.remove(dst_path)
            else:
                shutil.rmtree(dst_path)
        shutil.move(src_path, dst_path)

    try:
        os.rename(Path(outDir + outName + '/' + geoName + '-para-mesh.vtk'),Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk'))
    except:
        pass
    os.remove(Path(outDir + outName + '/' + geoName + '2D.mesh'))
    os.remove(Path(outDir + outName + '/' + geoName + '.node'))
    os.remove(Path(outDir + outName + '/' + geoName + '.ele'))
    os.remove(Path(outDir + outName + '/' + geoName + '.edge'))

    # Clean up temp directory
    try:
        if os.path.exists(tempPath):
            shutil.rmtree(tempPath)
    except Exception as e:
        print(f"Could not remove temp directory {tempPath}: {e}")

    try:
        App.Console.PrintMessage("Model moved to output folder...\n")
    except Exception:
        print("Model moved to output folder...")




    if dataFilesGen == True:
        # Set linked object for node data file
        LDPMnodesData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMnodesData")
        #LDPMnodesData.ViewObject.Proxy = IconViewProviderToFile(LDPMnodesData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMnodesData)
        LDPMnodesData.addProperty("App::PropertyFile",'Location','Node Data File','Location of node data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-nodes.dat'))
        
        # Set linked object for tet data file
        LDPMtetsData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMtetsData")
        #LDPMtetsData.ViewObject.Proxy = IconViewProviderToFile(LDPMtetsData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMtetsData)
        LDPMtetsData.addProperty("App::PropertyFile",'Location','Tet Data File','Location of tets data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-tets.dat'))

        # Set linked object for facet data file
        LDPMfacetsData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMfacetsData")
        #LDPMfacetsData.ViewObject.Proxy = IconViewProviderToFile(LDPMfacetsData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMfacetsData)
        LDPMfacetsData.addProperty("App::PropertyFile",'Location','Facet Data File','Location of facet data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-facets.dat'))

        # Set linked object for face facet data file
        LDPMfaceFacetsData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMfaceFacetsData")
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMfaceFacetsData)
        LDPMfaceFacetsData.addProperty("App::PropertyFile",'Location','Face Facet Data File','Location of face facet data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-faceFacets.dat'))

        # Set linked object for facet vertices data file
        LDPMfacetsVerticesData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMfacetsVerticesData")
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMfacetsVerticesData)
        LDPMfacetsVerticesData.addProperty("App::PropertyFile",'Location','Facet Vertices Data File','Location of facet vertices data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-facetsVertices.dat'))




    if visFilesGen == True:
        # Set linked object for particle VTK file
        LDPMparticlesVTK = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMparticlesVTK")
        #LDPMparticlesVTK.ViewObject.Proxy = IconViewProviderToFile(LDPMparticlesVTK,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMparticlesVTK)
        LDPMparticlesVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-particles.000.vtk'))


    if geoType in ['Cylinder', 'Cone', 'Sphere','Import CAD or Mesh']:

        if visFilesGen == True:
            # Insert mesh visualization and link mesh VTK file
            Fem.insert(str(Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk')),App.ActiveDocument.Name)        
            LDPMmeshVTK = App.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000')
            LDPMmeshVTK.Label = 'LDPMmeshVTK' 
            App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMmeshVTK)
            LDPMmeshVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk'))

            Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').ShapeColor = (0.80,0.80,0.80)
            Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').BackfaceCulling = False
            Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').MaxFacesShowInner = 0
            Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').DisplayMode = u"Faces"

        
        try:
            objName = App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0].Name
            Gui.getDocument(App.ActiveDocument.Name).getObject(objName).Transparency = 50
            Gui.getDocument(App.ActiveDocument.Name).getObject(objName).ShapeColor = (0.80,0.80,0.80)
        except:
            pass

    else:
        if visFilesGen == True:
            # Set linked object for mesh VTK file
            LDPMmeshVTK = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMmeshVTK")
            #LDPMmeshVTK.ViewObject.Proxy = IconViewProviderToFile(LDPMmeshVTK,os.path.join(ICONPATH,'FEMMeshICON.svg'))
            App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMmeshVTK)
            LDPMmeshVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk'))


        try:
            objName = genGeo.Name
        except:
            try:
                objName = App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0].Name
            except:
                objName = None
        try:
            if objName:
                Gui.getDocument(App.ActiveDocument.Name).getObject(objName).Transparency = 0
                Gui.getDocument(App.ActiveDocument.Name).getObject(objName).ShapeColor = (0.80,0.80,0.80)
        except:
            pass


    if visFilesGen == True:
        # Insert facet visualization and link facet VTK file
        Fem.insert(str(Path(outDir + outName + '/' + geoName + '-para-facets.000.vtk')),App.ActiveDocument.Name)        
        LDPMfacetsVTK = App.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000')
        LDPMfacetsVTK.Label = 'LDPMfacetsVTK' 
        App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMfacetsVTK)
        LDPMfacetsVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-facets.000.vtk'))


        # Set visualization properties for facets
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').DisplayMode = u"Wireframe"
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').MaxFacesShowInner = 0
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').BackfaceCulling = False
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').ShapeColor = (0.36,0.36,0.36)


    # Remove initial mesh and insert final mesh visualization
    #App.getDocument(App.ActiveDocument.Name).removeObject(meshName)
    doc = App.getDocument(App.ActiveDocument.Name)
    if hasattr(doc, meshName):
        doc.removeObject(meshName)
    meshFile = str(Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk'))
    Fem.insert(meshFile,App.ActiveDocument.Name)

    filename = os.path.basename(meshFile)
    filename, file_extension = os.path.splitext(filename)
    filename = re.sub("\.", "_", filename)
    filename = re.sub("/.", "_", filename)
    filename = re.sub("-", "_", filename)
    # If filename starts with a number, resub it with an underscore
    filename = re.sub("^\d", "_", filename)
    newMesh = App.getDocument(App.ActiveDocument.Name).getObject(filename)
    newMesh.Label = meshName




    # Set visualization properties for particle centers
    # Need to load differently for generated vs loaded meshes
    if geoType == "Import CAD or Mesh":
        doc = App.getDocument(App.ActiveDocument.Name)
        import_obj_name = None
        try:
            if genGeo is not None and doc.getObject(genGeo.Name) is not None:
                import_obj_name = genGeo.Name
        except Exception:
            pass
        if import_obj_name is None:
            try:
                matches = doc.getObjectsByLabel(geoName)
                if matches:
                    import_obj_name = matches[0].Name
            except Exception:
                pass
        if import_obj_name is None:
            cad_base = os.path.basename(cadFile)
            cad_base, _ = os.path.splitext(cad_base)
            cad_base = re.sub("\.", "_", cad_base)
            cad_base = re.sub("/.", "_", cad_base)
            cad_base = re.sub("-", "_", cad_base)
            cad_base = re.sub("^\d", "_", cad_base)
            if doc.getObject(cad_base) is not None:
                import_obj_name = cad_base
        if import_obj_name is not None:
            try:
                geoObj = doc.getObject(import_obj_name)
                geoGui = Gui.getDocument(App.ActiveDocument.Name).getObject(import_obj_name)
                if geoGui is not None:
                    geoGui.BackfaceCulling = False
                    geoGui.Transparency = 0
                    geoGui.DisplayMode = u"Faces, Wireframe & Nodes"
                    geoGui.ShapeColor = (0.80, 0.80, 0.80)
                if geoObj is not None:
                    analysis = doc.getObject(analysisName)
                    if analysis is not None:
                        analysis.addObject(geoObj)
                    geoObj.Label = meshName
            except Exception:
                pass
    else:
        Gui.getDocument(App.ActiveDocument.Name).getObject(filename).DisplayMode = u"Nodes"
        Gui.getDocument(App.ActiveDocument.Name).getObject(filename).PointSize = 3.00
        Gui.getDocument(App.ActiveDocument.Name).getObject(filename).PointColor = (0.00,0.00,0.00)




    # If FreeCAD version is 1.0 or greater, import the HTC mesh
    # Check if FreeCAD version is 1.0 or greater
    if float(App.Version()[0]) >= 1.0:
        if htcToggle in ['on','On']:
            htcFile = str(Path(outDir + outName + '/' + geoName + '-para-flowEdges.000.vtk'))
            Fem.insert(htcFile,App.ActiveDocument.Name)





    # Set material properties, descriptions, and values based on selected constitutive equation set and material parameter set
    [materialProps, materialPropDesc, materialPropsVal] = gen_LDPMCSL_properties(constitutiveEQ, matParaSet)




    simProps = [\
        "TotalTime",\
        "TimestepSize",\
        "NumberOfThreads",\
        "NumberOutputSteps",\
        ]




    simPropDesc = [\
        "Description coming soon...",\
        "Description coming soon...",\
        "Description coming soon...",\
        "Description coming soon...",\
        ]





    # Remove unused material properties
    #App.getDocument(App.ActiveDocument.Name).getObject(materialName).removeProperty("References")

    # Add appropriate constitutive equation set
    App.getDocument(App.ActiveDocument.Name).getObject(materialName).addProperty("App::PropertyString",'ConstitutiveEquationSet','Base','Set of constitutive equations.').ConstitutiveEquationSet=constitutiveEQ



    # Add appropriate material properties
    for x in range(len(materialProps)):
        App.getDocument(App.ActiveDocument.Name).getObject(materialName).addProperty("App::PropertyString",materialProps[x],elementType+" Parameters",materialPropDesc[x])
        setattr(App.getDocument(App.ActiveDocument.Name).getObject(materialName),materialProps[x],str(materialPropsVal[x]))


    # Add appropriate simulation properties
    for x in range(len(simProps)):
        App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addProperty("App::PropertyFloat",simProps[x],"Simulation",simPropDesc[x])#.Density=0.25
    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addProperty("App::PropertyEnumeration","Solver","Simulation","Solver software").Solver=['Project Chrono']
    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addProperty("App::PropertyEnumeration","IntegrationScheme","Simulation","Integrator type").IntegrationScheme=['Explicit']












    gen_ui.progressBar.setValue(100) 


    if multiMatToggle == "Off":
        # Display sieve curve data - save directly to output directory
        try:
            # Use output directory instead of temp directory
            output_path = str(Path(outDir + outName)) + os.sep
            print(f"Generating sieve curve data to: {output_path}")
            mkDisp_sieveCurves(volFracPar, parVolTotal, tetVolume, minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, fullerCoef,sieveCurveDiameter,sieveCurvePassing,parDiameterList,output_path)
        except Exception as e:
            print(f"Could not generate sieve curve display: {e}")
            import traceback
            traceback.print_exc()
        
        # List all files in temp directory (if it exists) and move them
        if not os.path.exists(tempPath):
            file_names = []
        else:
            file_names = os.listdir(tempPath)
        
        # Move all files to output directory (if any exist)
        for file_name in file_names:
            try:
                shutil.move(os.path.join(tempPath, file_name), Path(outDir + outName))
            except Exception as e:
                print(f"Could not move file {file_name}: {e}")

    # Switch back to model window
    mw=Gui.getMainWindow()
    mdi=mw.findChild(QtWidgets.QMdiArea)
    mdi.activatePreviousSubWindow()

    # Switch to FEM GUI
    App.ActiveDocument.recompute()



    Gui.Control.closeDialog()
    Gui.activateWorkbench("FemWorkbench")
    FemGui.setActiveAnalysis(App.activeDocument().getObject(analysisName))
    





